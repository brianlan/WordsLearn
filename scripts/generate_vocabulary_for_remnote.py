import argparse
import subprocess
import itertools
import json
from pathlib import Path

from tqdm import tqdm
from loguru import logger
from jinja2 import Template


def parent_ensured_path(path: str | Path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return Path(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="desc")
    parser.add_argument("-i", "--vocabularies", nargs="+", type=Path, required=True)
    parser.add_argument("-o", "--output-path", type=parent_ensured_path, required=True)
    parser.add_argument("--models", nargs="+", type=str, required=True)
    parser.add_argument("--explanations-path", type=parent_ensured_path, required=True)
    parser.add_argument("--startover", default=False, action="store_true")
    args = parser.parse_args()
    args.models = itertools.cycle(args.models)
    return args


def main(args) -> None:
    vocabulary = merge_vocabularies(read_vocabularies(args.vocabularies))
    explanations = generate_expalantions(vocabulary, args.explanations_path, args.models, startover=args.startover)
    write_expalantions(explanations, args.explanations_path)
    flash_cards = generate_remnote_flash_cards(explanations)
    write_flash_cards(flash_cards, args.output_path)


def read_vocabularies(vocabulary_paths: list[Path]) -> list[list[str]]:
    return [[line.strip() for line in path.read_text().splitlines() if line.strip()] for path in vocabulary_paths]


def merge_vocabularies(vocabularies: list[list[str]]) -> set[str]:
    return set(itertools.chain.from_iterable(vocabularies))


def generate_expalantions(
    vocabulary: set[str], explanations_path: Path, models: itertools.cycle, startover: bool = False
) -> dict[str, dict]:
    logger.info(f"Generating explanations for {len(vocabulary)} words.")
    explanations: dict[str, dict] = {}
    if not startover:
        explanations = read_explanations(explanations_path)

    for word in tqdm(sorted(vocabulary)):
        if word not in explanations:
            explanations[word] = get_explanation(word, models=models)

    return explanations


def read_explanations(explanations_path: Path) -> dict[str, dict]:
    logger.info(f"Reading explanations from {explanations_path}.")
    try:
        with open(explanations_path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def write_expalantions(explanations: dict[str, dict], explanations_path: Path) -> None:
    with open(explanations_path, "w", encoding="utf-8") as f:
        json.dump(explanations, f, ensure_ascii=False)
    logger.info(f"Successfully write explanations ({len(explanations)} words) to {explanations_path}.")


def get_explanation(word: str, models: itertools.cycle) -> dict:
    model = next(models)
    prompt = f"Generate the explanation for word: {word}."
    result = subprocess.run(
        ["opencode", "run", "--pure", "-m", model, "--agent", "word-explanation-generator", prompt],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("opencode failed: {}", result.stderr.strip())
        return {}
    result_dict = json.loads(result.stdout)
    return result_dict


def generate_remnote_flash_cards(explanations: dict[str, dict]) -> list[str]:
    flash_cards: list[str] = []
    for word, explanation in explanations.items():
        en_card = generate_full_explanation_markdown_format(explanation)
        flash_cards.extend(["\n", en_card])
        for meaning in explanation["meanings"]:
            for example_sentence in meaning["examples"]:
                zh_card = f"{example_sentence['chinese']}=={word}"
                flash_cards.extend(["\n", zh_card])
    return flash_cards


def generate_full_explanation_markdown_format(explanation: dict) -> str:
    template = Template(Path("templates/word-explanation.md").read_text())
    return template.render(**explanation).strip()


def write_flash_cards(flash_cards: list[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(flash_cards), encoding="utf-8")
    logger.info(f"Successfully wrote {len(flash_cards)} flash cards to {output_path}.")


if __name__ == "__main__":
    main(parse_args())
