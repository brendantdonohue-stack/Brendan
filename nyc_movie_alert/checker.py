"""Core check: fetch each theater's page and match it against the watchlist."""
from dataclasses import dataclass

from . import state as state_module
from .extract import find_context_snippet, has_nearby_date, visible_text
from .fetcher import fetch
from .matcher import find_link_for_title, find_match
from .notifier import Alert
from .theaters import Theater


@dataclass
class FetchStatus:
    theater: Theater
    ok: bool
    length: int
    status_code: int | None = None
    error: str | None = None
    rendered: bool = False


def run_check(
    movies: list[dict], theaters: list[Theater], state: dict, debug: bool = False
) -> tuple[list[Alert], list[FetchStatus]]:
    """Returns (new_alerts, fetch_statuses). Mutates `state` in place for
    every alert found (caller is responsible for persisting it)."""
    alerts: list[Alert] = []
    statuses: list[FetchStatus] = []

    for theater in theaters:
        result = fetch(theater.url)
        statuses.append(
            FetchStatus(
                theater=theater,
                ok=result.ok,
                length=len(result.html) if result.html else 0,
                status_code=result.status_code,
                error=result.error,
                rendered=result.rendered,
            )
        )
        if not result.ok:
            continue

        html = result.html
        text = visible_text(html)

        for movie in movies:
            title = movie["title"]
            if not find_match(title, text):
                continue
            if state_module.already_notified(state, title, theater.name):
                continue
            link = find_link_for_title(title, html)
            context = find_context_snippet(title, text)
            likely_real = has_nearby_date(context) if context else False
            alerts.append(
                Alert(
                    movie_title=title,
                    theater_name=theater.name,
                    theater_url=theater.url,
                    link=link,
                    context=context,
                    likely_real=likely_real,
                )
            )
            state_module.mark_notified(state, title, theater.name)

    if debug:
        for s in statuses:
            tag = " [rendered]" if s.rendered else ""
            if s.ok:
                print(f"[debug] {s.theater.name}: OK ({s.length} chars){tag}")
            else:
                print(f"[debug] {s.theater.name}: FAILED ({s.error}){tag}")

    return alerts, statuses
