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
from pydantic import BaseModel, ValidationError

from .vocab_utils import parent_ensured_path, read_json


class Example(BaseModel):
    english: str
    chinese: str


class Meaning(BaseModel):
    part_of_speech: str
    explanation: str
    examples: list[Example]
    synonyms: list[str]


class Explanation(BaseModel):
    word: str
    american_ipa: str
    british_ipa: str
    derived_forms: list[str]
    common_collocations: list[str]
    meanings: list[Meaning]


class GetExplanationError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate word explanations JSON from vocabulary files.")
    parser.add_argument("-i", "--vocabularies", nargs="+", type=Path, required=True)
    parser.add_argument("--explanations-path", type=parent_ensured_path, required=True)
    parser.add_argument("--models", nargs="+", type=str, required=True)
    parser.add_argument("--startover", default=False, action="store_true")
    parser.add_argument("--num-workers", type=int, default=1)
    args = parser.parse_args()
    args.models = itertools.cycle(args.models)
    return args


def main(args) -> None:
    vocabulary = merge_vocabularies(read_vocabularies(args.vocabularies))
    explanations = generate_explanations(
        vocabulary, args.explanations_path, args.models, startover=args.startover, num_workers=args.num_workers
    )
    write_explanations(explanations, args.explanations_path)


def read_vocabularies(vocabulary_paths: list[Path]) -> list[list[str]]:
    return [
        [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]
        for path in vocabulary_paths
    ]


def merge_vocabularies(vocabularies: list[list[str]]) -> set[str]:
    return set(itertools.chain.from_iterable(vocabularies))


def generate_explanations(
    vocabulary: set[str],
    explanations_path: Path,
    models: itertools.cycle,
    startover: bool = False,
    num_workers: int = 1,
) -> dict[str, dict]:
    logger.info(f"Generating explanations for {len(vocabulary)} words.")
    explanations: dict[str, dict] = {}
    if not startover:
        try:
            logger.info(f"Reading explanations from {explanations_path}.")
            explanations = read_json(explanations_path)
        except FileNotFoundError:
            pass

    words_to_process = [word for word in sorted(vocabulary) if word not in explanations]
    if words_to_process:
        logger.info(f"Incremental words to generate ({len(words_to_process)}): {words_to_process}")
    else:
        logger.info("No new words to generate.")
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


def write_explanations(explanations: dict[str, dict], explanations_path: Path) -> None:
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
            raw = json.loads(result.stdout)
        except json.decoder.JSONDecodeError:
            try:
                raw = json_repair.loads(result.stdout)
            except ValueError:
                logger.warning("Failed to decode JSON for word '{}' (attempt {})", word, attempt + 1)
                continue

        try:
            explanation = Explanation.model_validate(raw).model_dump()
        except ValidationError:
            logger.warning("Schema validation failed for word '{}' (attempt {})", word, attempt + 1)
            continue

        explanation["generated_by"] = model
        return explanation

    raise GetExplanationError(f"Max retries exceeded for word {word} when calling get_explanation.")


if __name__ == "__main__":
    main(parse_args())
