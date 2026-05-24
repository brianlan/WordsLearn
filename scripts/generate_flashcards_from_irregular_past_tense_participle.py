import argparse
from pathlib import Path

from loguru import logger

from .vocab_utils import parent_ensured_path, read_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="desc")

    parser.add_argument("input_file", type=Path, help="input file")
    parser.add_argument("-o", "--output", type=parent_ensured_path, help="Output path")

    return parser.parse_args()


def main(args) -> None:
    data = read_json(args.input_file)
    logger.info(f"Read {len(data)} words from {args.input_file}")
    flashcards = []
    for orig_form, past_form in data.items():
        flashcards.extend(generate_flashcards_for_word(orig_form, past_form))
    with open(args.output, "w") as f:
        f.write("\n".join(flashcards))
        logger.info(f"Successfully wrote flashcards to {args.output}")


def generate_flashcards_for_word(orig_form: str, past_form: dict[str, list]) -> list[str]:
    return (
        generate_flashcards([orig_form], past_form["past_tenses"], "过去式") +
        generate_flashcards([orig_form], past_form["past_participles"], "过去分词") + 
        generate_flashcards(past_form["past_tenses"], [orig_form], "原形") + 
        generate_flashcards(past_form["past_tenses"], past_form["past_participles"], "过去分词") + 
        generate_flashcards(past_form["past_participles"], [orig_form], "原形") + 
        generate_flashcards(past_form["past_participles"], past_form["past_tenses"], "过去式")
    )


def generate_flashcards(front: list[str], back: list[str], question_type: str) -> list[str]:
    flashcards = []
    for i in front:
        flashcard = f"{i}的{question_type} == {', '.join(back)}"
        flashcards.append(flashcard)
    return flashcards


if __name__ == "__main__":
    main(parse_args())