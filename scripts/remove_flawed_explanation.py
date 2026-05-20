import argparse
import json
import re
from pathlib import Path

from loguru import logger


def parent_ensured_path(path: str | Path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return Path(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="desc")

    parser.add_argument("explanations_path", type=Path)
    parser.add_argument("--dry-run", default=False, action="store_true")

    return parser.parse_args()


def main(args) -> None:
    with open(args.explanations_path) as f:
        explanations = json.load(f)

    flaw_word_list = set()
    pattern = re.compile(r"\[[^\]]+\]")  # 匹配 [xxx] 格式
    for word, expltn in explanations.items():
        for meaning in expltn["meanings"]:
            for eg in meaning["examples"]:
                if not pattern.search(eg["chinese"]) or not pattern.search(eg["english"]):
                    flaw_word_list.add(word)

    logger.info(f"Word with flaws: {sorted(flaw_word_list)}")

    if not args.dry_run and len(flaw_word_list) > 0:
        for word in flaw_word_list:
            logger.info(f"Removed {explanations[word].get('generated_by', 'unknown')} generated word: {word} from {args.explanations_path}")
            del explanations[word]

        with open(args.explanations_path, "w", encoding="utf-8") as f:
            json.dump(explanations, f, ensure_ascii=False)


if __name__ == "__main__":
    main(parse_args())
