import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate word explanations and Remnote flashcards from a vocabulary file."
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Path to the input vocabulary .txt file.",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        required=True,
        help="Number of parallel workers for explanation generation.",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        type=str,
        required=True,
        help="Space-separated list of model identifiers to cycle through.",
    )
    parser.add_argument(
        "--existing-explanation-dir",
        type=Path,
        default=Path("explanations"),
        help="Directory containing existing explanation JSONs (default: explanations).",
    )
    parser.add_argument(
        "--explanation-save-path",
        type=Path,
        default=None,
        help="Path for the generated explanations JSON. Inferred from --input if omitted.",
    )
    parser.add_argument(
        "-o", "--output-path",
        type=Path,
        default=None,
        help="Path for the final flashcards .txt file. Inferred from --input if omitted.",
    )
    return parser.parse_args()


def infer_paths(input_path: Path) -> tuple[Path, Path]:
    stem = input_path.stem
    json_stem = stem.replace("-", "_")
    explanation_path = Path("explanations") / input_path.parent.name / f"{json_stem}.json"
    output_path = Path("output") / f"{stem}.txt"
    return explanation_path, output_path


def run(command: list[str]) -> None:
    print("Running:", " ".join(command))
    result = subprocess.run(command, check=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}")


def main() -> None:
    args = parse_args()

    explanation_path = args.explanation_save_path
    output_path = args.output_path
    if explanation_path is None or output_path is None:
        inferred_explanation, inferred_output = infer_paths(args.input)
        explanation_path = explanation_path or inferred_explanation
        output_path = output_path or inferred_output

    explanation_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    run([
        sys.executable, "-m", "scripts.generate_explanations",
        "--num-workers", str(args.num_workers),
        "--models", *args.models,
        "--agent", "word-explanation-generator-single",
        "--existing-explanation-dir", str(args.existing_explanation_dir),
        "-i", str(args.input),
        "--explanation-save-path", str(explanation_path),
    ])

    run([
        sys.executable, "-m", "scripts.generate_flashcards_from_expalantions",
        "-e", str(explanation_path),
        "-o", str(output_path),
    ])

    print(f"Pipeline complete. Flashcards saved to: {output_path}")


if __name__ == "__main__":
    main()
