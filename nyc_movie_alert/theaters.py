"""Loads the list of theaters to check from config/theaters.yaml."""
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config" / "theaters.yaml"


@dataclass
class Theater:
    name: str
    url: str


def load_theaters(path: Path = DEFAULT_PATH) -> list[Theater]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return [Theater(name=t["name"], url=t["url"]) for t in data.get("theaters", [])]
