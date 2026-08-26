"""Tracks which (movie, theater) alerts have already been sent, so we don't
re-notify every run for a title that's still in the middle of its engagement."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "state.json"
COOLDOWN_DAYS = 30


def _key(movie_title: str, theater_name: str) -> str:
    return f"{movie_title.strip().lower()}|{theater_name.strip().lower()}"


def load(path: Path = DEFAULT_PATH) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(state: dict, path: Path = DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def already_notified(state: dict, movie_title: str, theater_name: str) -> bool:
    key = _key(movie_title, theater_name)
    last = state.get(key)
    if not last:
        return False
    last_dt = datetime.fromisoformat(last)
    return datetime.now(timezone.utc) - last_dt < timedelta(days=COOLDOWN_DAYS)


def mark_notified(state: dict, movie_title: str, theater_name: str) -> None:
    state[_key(movie_title, theater_name)] = datetime.now(timezone.utc).isoformat()
