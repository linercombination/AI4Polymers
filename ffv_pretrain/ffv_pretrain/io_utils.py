from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml


def load_yaml(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def ensure_dir(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def write_json(path: str | Path, payload: dict) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_metadata(cache_dir: str | Path) -> pd.DataFrame:
    return pd.read_csv(Path(cache_dir) / "metadata.csv")


def load_manifest(cache_dir: str | Path) -> dict:
    return json.loads((Path(cache_dir) / "manifest.json").read_text(encoding="utf-8"))

