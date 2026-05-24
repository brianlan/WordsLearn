import json
from pathlib import Path

from loguru import logger


def parent_ensured_path(path: str | Path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return Path(path)


def read_json(json_path: Path) -> dict:
    with open(json_path) as f:
        return json.load(f)
