import argparse
import concurrent.futures
import itertools
import json
import json_repair
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path

from tqdm import tqdm
from loguru import logger
from jinja2 import Template


def parent_ensured_path(path: str | Path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return Path(path)


class GetExplanationError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="desc")
    parser.add_argument("-i", "--vocabularies", nargs="+", type=Path, required=True)
    parser.add_argument("-o", "--output-path", type=parent_ensured_path, required=True)
    parser.add_argument("--models", nargs="+", type=str, required=True)
    parser.add_argument("--explanations-path", type=parent_ensured_path, required=True)
    parser.add_argument("--startover", default=False, action="store_true")
    parser.add_argument("--num-workers", type=int, default=1)
    args = parser.parse_args()
    args.models = itertools.cycle(args.models)
    return args


def main(args) -> None:
    vocabulary = merge_vocabularies(read_vocabularies(args.vocabularies))
    explanations = generate_expalantions(
        vocabulary, args.explanations_path, args.models, startover=args.startover, num_workers=args.num_workers
    )
    write_expalantions(explanations, args.explanations_path)
    flash_cards = generate_remnote_flash_cards(explanations)
    write_flash_cards(flash_cards, args.output_path)


def read_vocabularies(vocabulary_paths: list[Path]) -> list[list[str]]:
    return [
        [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]
        for path in vocabulary_paths
    ]


def merge_vocabularies(vocabularies: list[list[str]]) -> set[str]:
    return set(itertools.chain.from_iterable(vocabularies))


def generate_expalantions(
    vocabulary: set[str],
    explanations_path: Path,
    models: itertools.cycle,
    startover: bool = False,
    num_workers: int = 1,
) -> dict[str, dict]:
    logger.info(f"Generating explanations for {len(vocabulary)} words.")
    explanations: dict[str, dict] = {}
    if not startover:
        explanations = read_explanations(explanations_path)

    words_to_process = [word for word in sorted(vocabulary) if word not in explanations]
    model_lock = threading.Lock()

    def get_model() -> str:
        with model_lock:
            return next(models)

    def explain_word(word: str) -> tuple[str, dict | None]:
        try:
            return word, get_explanation(word, get_model=get_model)
        except GetExplanationError:
            logger.error("Max retries exceeded for word '{}', skipping.", word)
            return word, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(explain_word, word) for word in words_to_process]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(words_to_process)):
            word, result = future.result()
            if result is not None:
                explanations[word] = result

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


def get_explanation(word: str, get_model: Callable[[], str], max_retries: int = 3) -> dict:
    for attempt in range(max_retries + 1):
        model = get_model()
        prompt = f"Generate the explanation for word: {word}."
        result = subprocess.run(
            ["opencode", "run", "--pure", "-m", model, "--agent", "word-explanation-generator", prompt],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error("opencode failed (attempt {}): {}", attempt + 1, result.stderr.strip())
            continue
        try:
            result_dict = json_repair.loads(result.stdout, strict=True)
            return result_dict
        except (ValueError, json.decoder.JSONDecodeError):
            logger.warning("Failed to decode JSON for word '{}' (attempt {})", word, attempt + 1)
            continue

    raise GetExplanationError(f"Max retries exceeded for word {word} when calling get_explanation.")


def generate_remnote_flash_cards(explanations: dict[str, dict]) -> list[str]:
    flash_cards: list[str] = []
    for word, explanation in explanations.items():
        for meaning in explanation["meanings"]:
            for example in meaning["examples"]:
                ipa, exp, syn = explanation["american_ipa"], meaning["explanation"], meaning["synonyms"]
                en_card = create_card(example["english"], ipa, exp, syn)
                zh_card = create_card(example["chinese"], ipa, exp, syn)
                flash_cards.extend([en_card, zh_card])
    return flash_cards


def emphasize(sentence: str, style: tuple[str, str]) -> str:
    return sentence.replace("[", style[0]).replace("]", style[1])


def create_card(example: str, ipa: str, explanation: str, synonyms: list[str]) -> str:
    def bu(s):
        return emphasize(s, (" _**", "**_ "))

    def b(s):
        return emphasize(s, (" __**", "**__ "))

    return f"{bu(example)} == {ipa} : {b(explanation)} [{', '.join(synonyms)}]"


def generate_full_explanation_markdown_format(explanation: dict) -> str:
    template = Template(Path("templates/word-explanation.md").read_text())
    return template.render(**explanation).strip()


def write_flash_cards(flash_cards: list[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(flash_cards), encoding="utf-8")
    logger.info(f"Successfully wrote {len(flash_cards)} flash cards to {output_path}.")


if __name__ == "__main__":
    main(parse_args())
