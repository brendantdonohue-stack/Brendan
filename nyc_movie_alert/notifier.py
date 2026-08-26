"""Sends alert emails over SMTP."""
import os
import smtplib
from dataclasses import dataclass
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


@dataclass
class SmtpConfig:
    host: str
    port: int
    user: str
    password: str
    from_addr: str
    to_addr: str

    @classmethod
    def from_env(cls) -> "SmtpConfig | None":
        """Reads SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD/ALERT_FROM/ALERT_TO
        from the environment, falling back to config/config.yaml for any that
        are unset (see config/config.example.yaml)."""
        file_config: dict = {}
        if CONFIG_YAML_PATH.exists():
            with open(CONFIG_YAML_PATH, encoding="utf-8") as f:
                file_config = yaml.safe_load(f) or {}

        def get(env_key: str, yaml_key: str) -> str | None:
            return os.environ.get(env_key) or file_config.get(yaml_key)

        host = get("SMTP_HOST", "smtp_host")
        user = get("SMTP_USER", "smtp_user")
        password = get("SMTP_PASSWORD", "smtp_password")
        to_addr = get("ALERT_TO", "alert_to")
        if not (host and user and password and to_addr):
            return None
        return cls(
            host=host,
            port=int(get("SMTP_PORT", "smtp_port") or 465),
            user=user,
            password=password,
            from_addr=get("ALERT_FROM", "alert_from") or user,
            to_addr=to_addr,
        )


def _format_body(alerts: list[Alert]) -> str:
    lines = ["A movie from your watchlist is playing in NYC:", ""]
    for alert in alerts:
        line = f"- \"{alert.movie_title}\" at {alert.theater_name}"
        lines.append(line)
        lines.append(f"  {alert.link or alert.theater_url}")
    lines.append("")
    lines.append("(Sent by your nyc-movie-alert watchlist checker.)")
    return "\n".join(lines)


def send_alert_email(alerts: list[Alert], config: SmtpConfig) -> None:
    if not alerts:
        return
    subject = (
        f'"{alerts[0].movie_title}" is playing in NYC'
        if len(alerts) == 1
        else f"{len(alerts)} movies from your watchlist are playing in NYC"
    )
    msg = MIMEText(_format_body(alerts))
    msg["Subject"] = subject
    msg["From"] = config.from_addr
    msg["To"] = config.to_addr

    with smtplib.SMTP_SSL(config.host, config.port) as server:
        server.login(config.user, config.password)
        server.sendmail(config.from_addr, [config.to_addr], msg.as_string())
