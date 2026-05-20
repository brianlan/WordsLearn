import argparse
import json
from pathlib import Path

from loguru import logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remove specific words from an explanations JSON file")
    parser.add_argument("explanations_path", type=Path)
    parser.add_argument("words", nargs="+", help="Words to remove")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main(args) -> None:
    with open(args.explanations_path) as f:
        explanations = json.load(f)

    removed = [w for w in args.words if w in explanations]
    missing = [w for w in args.words if w not in explanations]

    if missing:
        logger.warning(f"Not found: {missing}")

    logger.info(f"Will remove {len(removed)} words: {removed}")

    if not args.dry_run and len(removed) > 0:
        for w in removed:
            del explanations[w]
        with open(args.explanations_path, "w", encoding="utf-8") as f:
            json.dump(explanations, f, ensure_ascii=False)
        logger.info(f"Removed {len(removed)} words from {args.explanations_path}")


if __name__ == "__main__":
    main(parse_args())
