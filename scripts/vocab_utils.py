import json
from pathlib import Path

from loguru import logger


def parent_ensured_path(path: str | Path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return Path(path)


def read_explanations(explanations_path: Path) -> dict[str, dict]:
    logger.info(f"Reading explanations from {explanations_path}.")
    with open(explanations_path) as f:
        return json.load(f)
