"""JSON-backed CRUD for the user's movie watchlist."""
import json
from datetime import date, datetime, timezone
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "watchlist.json"


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save(path: Path, movies: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2)
        f.write("\n")


def list_movies(path: Path = DEFAULT_PATH) -> list[dict]:
    return _load(path)


def add_movie(title: str, path: Path = DEFAULT_PATH) -> bool:
    """Add a title if not already present (case-insensitive). Returns True if added."""
    movies = _load(path)
    if any(m["title"].strip().lower() == title.strip().lower() for m in movies):
        return False
    movies.append({"title": title.strip(), "added": datetime.now(timezone.utc).date().isoformat()})
    _save(path, movies)
    return True


def remove_movie(title: str, path: Path = DEFAULT_PATH) -> bool:
    """Remove a title (case-insensitive). Returns True if removed."""
    movies = _load(path)
    remaining = [m for m in movies if m["title"].strip().lower() != title.strip().lower()]
    if len(remaining) == len(movies):
        return False
    _save(path, remaining)
    return True
