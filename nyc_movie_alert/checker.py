"""Core check: fetch each theater's page and match it against the watchlist."""
from dataclasses import dataclass

from . import state as state_module
from .fetcher import fetch_html
from .matcher import find_link_for_title, find_match
from .notifier import Alert
from .theaters import Theater


@dataclass
class FetchStatus:
    theater: Theater
    ok: bool
    length: int


def run_check(
    movies: list[dict], theaters: list[Theater], state: dict, debug: bool = False
) -> tuple[list[Alert], list[FetchStatus]]:
    """Returns (new_alerts, fetch_statuses). Mutates `state` in place for
    every alert found (caller is responsible for persisting it)."""
    alerts: list[Alert] = []
    statuses: list[FetchStatus] = []

    for theater in theaters:
        html = fetch_html(theater.url)
        ok = html is not None
        statuses.append(FetchStatus(theater=theater, ok=ok, length=len(html) if html else 0))
        if not ok:
            continue

        for movie in movies:
            title = movie["title"]
            if not find_match(title, html):
                continue
            if state_module.already_notified(state, title, theater.name):
                continue
            link = find_link_for_title(title, html)
            alerts.append(
                Alert(movie_title=title, theater_name=theater.name, theater_url=theater.url, link=link)
            )
            state_module.mark_notified(state, title, theater.name)

    if debug:
        for s in statuses:
            print(f"[debug] {s.theater.name}: {'OK' if s.ok else 'FAILED'} ({s.length} chars)")

    return alerts, statuses
