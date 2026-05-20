import argparse
from pathlib import Path

from loguru import logger

from .vocab_utils import parent_ensured_path, read_explanations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Remnote flash cards from explanations JSON.")
    parser.add_argument("-e", "--explanations-path", type=Path, required=True)
    parser.add_argument("-o", "--output-path", type=parent_ensured_path, required=True)
    return parser.parse_args()


def main(args) -> None:
    explanations = read_explanations(args.explanations_path)
    flash_cards = generate_remnote_flash_cards(explanations)
    write_flash_cards(flash_cards, args.output_path)


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


def write_flash_cards(flash_cards: list[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(flash_cards), encoding="utf-8")
    logger.info(f"Successfully wrote {len(flash_cards)} flash cards to {output_path}.")


if __name__ == "__main__":
    main(parse_args())
