from __future__ import annotations
import tomllib
from pathlib import Path


def load_config(path="config.toml") -> dict:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))
