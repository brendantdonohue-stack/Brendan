"""Sends alert emails over SMTP."""
import html as html_lib
import os
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import yaml

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

CONFIG_YAML_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"


@dataclass
class Alert:
    movie_title: str
    theater_name: str
    theater_url: str
    link: str | None = None
    context: str | None = None
    show_date: str | None = None
    likely_real: bool = False


@dataclass
class SmtpConfig:
    host: str
    port: int
    user: str
    password: str
    from_addr: str
    to_addrs: list[str]

    @classmethod
    def from_env(cls) -> "SmtpConfig | None":
        """Reads SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD/ALERT_FROM/ALERT_TO
        from the environment, falling back to config/config.yaml for any that
        are unset (see config/config.example.yaml). ALERT_TO may be a single
        address or a comma-separated list, to alert more than one person."""
        file_config: dict = {}
        if CONFIG_YAML_PATH.exists():
            with open(CONFIG_YAML_PATH, encoding="utf-8") as f:
                file_config = yaml.safe_load(f) or {}

        def get(env_key: str, yaml_key: str) -> str | None:
            return os.environ.get(env_key) or file_config.get(yaml_key)

        host = get("SMTP_HOST", "smtp_host")
        user = get("SMTP_USER", "smtp_user")
        password = get("SMTP_PASSWORD", "smtp_password")
        to_addr_raw = get("ALERT_TO", "alert_to")
        if not (host and user and password and to_addr_raw):
            return None
        to_addrs = [addr.strip() for addr in str(to_addr_raw).split(",") if addr.strip()]
        if not to_addrs:
            return None
        return cls(
            host=host,
            port=int(get("SMTP_PORT", "smtp_port") or 465),
            user=user,
            password=password,
            from_addr=get("ALERT_FROM", "alert_from") or user,
            to_addrs=to_addrs,
        )


def _send(subject: str, text_body: str, html_body: str, config: SmtpConfig) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.from_addr
    msg["To"] = ", ".join(config.to_addrs)
    # Order matters: email clients that render HTML prefer the last part,
    # so plain text (the fallback) goes first.
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL(config.host, config.port) as server:
        server.login(config.user, config.password)
        server.sendmail(config.from_addr, config.to_addrs, msg.as_string())


# A running joke: the header is always this exact phrase, no matter which
# movie(s) actually matched -- Barry Lyndon is the bit, not a real filter.
_JOKE_HEADER = "Is Barry Lyndon Playing in New York?"
_TAGLINE = (
    "a vibecoded weekly alert to see if Barry Lyndon and other interesting "
    "pictures are playing on the big screen"
)


def _header_title(_alerts: list[Alert]) -> str:
    return _JOKE_HEADER


def _format_text_body(alerts: list[Alert]) -> str:
    lines = [_header_title(alerts), "an alert by brendan", _TAGLINE, ""]
    for alert in alerts:
        confidence = "likely a real listing" if alert.likely_real else "UNCONFIRMED, please check"
        lines.append(f'- "{alert.movie_title}" at {alert.theater_name} ({confidence})')
        if alert.show_date:
            lines.append(f"  first showing: {alert.show_date}")
        lines.append(f"  {alert.link or alert.theater_url}")
        if alert.context:
            lines.append(f'  page text: "...{alert.context}..."')
        lines.append("")
    lines.append(
        "Note: this is a text match on the theater's page, not a parsed showtime -- "
        "always confirm on the theater's own site before making plans."
    )
    lines.append("(Sent by your nyc-movie-alert watchlist checker.)")
    return "\n".join(lines)


def _format_html_body(alerts: list[Alert]) -> str:
    esc = html_lib.escape
    cards = []
    for alert in alerts:
        confidence_color = "#2e7d32" if alert.likely_real else "#e65100"
        confidence_text = "likely a real listing" if alert.likely_real else "UNCONFIRMED, please check"
        link = alert.link or alert.theater_url
        date_line = (
            f'<div style="font-size:14px; margin:4px 0;">'
            f"<strong>First showing:</strong> {esc(alert.show_date)}</div>"
            if alert.show_date
            else ""
        )
        context_block = (
            f'<div style="font-size:13px; color:#555; margin-top:6px; '
            f'border-left:3px solid #ddd; padding-left:8px;">'
            f"&ldquo;&hellip;{esc(alert.context)}&hellip;&rdquo;</div>"
            if alert.context
            else ""
        )
        cards.append(
            f"""
            <div style="margin-bottom:18px; padding-bottom:18px; border-bottom:1px solid #eee;">
              <div style="font-size:17px; font-weight:bold; color:#111;">
                "{esc(alert.movie_title)}" at {esc(alert.theater_name)}
              </div>
              {date_line}
              <div style="font-size:13px; color:{confidence_color}; margin:4px 0;">
                {esc(confidence_text)}
              </div>
              <div style="font-size:13px;">
                <a href="{esc(link)}" style="color:#1a73e8;">{esc(link)}</a>
              </div>
              {context_block}
            </div>
            """
        )

    return f"""
    <div style="font-family: Arial, Helvetica, sans-serif; max-width:600px; margin:0 auto;">
      <div style="font-size:28px; font-weight:bold; color:#c62828; line-height:1.2;">
        {esc(_header_title(alerts))}
      </div>
      <div style="font-size:14px; color:#777; margin:4px 0;">
        an alert by brendan
      </div>
      <div style="font-size:12px; color:#999; margin:0 0 24px;">
        {esc(_TAGLINE)}
      </div>
      {''.join(cards)}
      <div style="font-size:12px; color:#999; margin-top:8px;">
        Note: this is a text match on the theater's page, not a parsed showtime &mdash;
        always confirm on the theater's own site before making plans.<br>
        (Sent by your nyc-movie-alert watchlist checker.)
      </div>
    </div>
    """


def send_alert_email(alerts: list[Alert], config: SmtpConfig) -> None:
    if not alerts:
        return
    subject = _header_title(alerts)
    _send(subject, _format_text_body(alerts), _format_html_body(alerts), config)


def send_test_email(config: SmtpConfig) -> None:
    """Sends a canned message to confirm SMTP credentials and delivery work,
    independent of whether any real watchlist match currently exists."""
    text_body = (
        f"Test email\nan alert by brendan\n{_TAGLINE}\n\n"
        "This is a test email from nyc-movie-alert.\n\n"
        "If you're reading this, your SMTP settings are correct and alerts "
        "will reach this address when a real match is found.\n"
    )
    html_body = f"""
    <div style="font-family: Arial, Helvetica, sans-serif; max-width:600px; margin:0 auto;">
      <div style="font-size:28px; font-weight:bold; color:#c62828;">Test email</div>
      <div style="font-size:14px; color:#777; margin:4px 0;">an alert by brendan</div>
      <div style="font-size:12px; color:#999; margin:0 0 24px;">{html_lib.escape(_TAGLINE)}</div>
      <p>This is a test email from nyc-movie-alert.</p>
      <p>If you're reading this, your SMTP settings are correct and alerts will
      reach this address when a real match is found.</p>
    </div>
    """
    _send("nyc-movie-alert test email", text_body, html_body, config)
