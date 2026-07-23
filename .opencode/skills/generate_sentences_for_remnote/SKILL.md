---
name: generate_sentences_for_remnote
description: |
  Generate English vocabulary explanations and Remnote flashcards from a plain-text vocabulary list.
  Use this skill whenever the user wants to turn a vocabulary .txt file into Remnote flashcards,
  generate word explanations and example sentences, run the `generate_explanations` and
  `generate_flashcards_from_expalantions` scripts together, or process vocabulary files for spaced-repetition cards.
  Trigger on phrases like "make flashcards", "generate explanations", "Remnote cards", "vocabulary to flashcards",
  or any mention of processing a vocabulary file through the WordsLearn pipeline.
---

# Generate sentences for Remnote

This skill runs the two-step WordsLearn pipeline that turns a plain-text vocabulary list into Remnote flashcards:

1. `python -m scripts.generate_explanations` — generate a JSON file of word explanations, IPA, examples, and synonyms.
2. `python -m scripts.generate_flashcards_from_expalantions` — convert that JSON into a `.txt` file of Remnote flashcards.

## Usage

Run the bundled script from the project root (`/Users/rlan/projects/WordsLearn`):

```bash
python opencode/skills/generate_sentences_for_remnote/scripts/run_pipeline.py \
  -i <vocabulary.txt> \
  --num-workers <N> \
  --models <model-1> <model-2> ...
```

### Required parameters

| Parameter | Description |
|-----------|-------------|
| `-i`, `--input` | Path to the input vocabulary `.txt` file. |
| `--num-workers` | Number of parallel workers for explanation generation. |
| `--models` | Space-separated list of model identifiers to cycle through. |

### Optional parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--existing-explanation-dir` | `explanations` | Directory containing existing explanation JSONs; words already present are skipped. |
| `--explanation-save-path` | Inferred from input | Path for the generated explanations JSON. Defaults to `explanations/<input_parent_dir>/<stem_with_underscores>.json`. |
| `-o`, `--output-path` | Inferred from input | Path for the final flashcards `.txt` file. Defaults to `output/<input_stem>.txt`. |

### Example

```bash
python opencode/skills/generate_sentences_for_remnote/scripts/run_pipeline.py \
  -i vocabularies/word_meaning/word-meaning-20260715.txt \
  --num-workers 12 \
  --models ark-coding-plan/doubao-seed-2.0-lite zhipuai-coding-plan/glm-5-turbo \
  opencode/deepseek-v4-flash-free opencode-go/deepseek-v4-flash \
  ark-coding-plan/deepseek-v4-flash photonmark/gpt-5.6-luna
```

This is equivalent to running:

```bash
python -m scripts.generate_explanations \
  --num-workers 12 \
  --models ark-coding-plan/doubao-seed-2.0-lite zhipuai-coding-plan/glm-5-turbo \
    opencode/deepseek-v4-flash-free opencode-go/deepseek-v4-flash \
    ark-coding-plan/deepseek-v4-flash photonmark/gpt-5.6-luna \
  --agent word-explanation-generator-single \
  --existing-explanation-dir explanations \
  -i vocabularies/word_meaning/word-meaning-20260715.txt \
  --explanation-save-path ./explanations/word_meaning/word_meaning_20260715.json

python -m scripts.generate_flashcards_from_expalantions \
  -e ./explanations/word_meaning/word_meaning_20260715.json \
  -o ./output/word-meaning-20260715.txt
```

## Notes

- The script always runs from the project root so that `python -m scripts.…` resolves correctly.
- The `--agent` is hard-coded to `word-explanation-generator-single`.
- If the inferred paths are not what the user wants, they should pass `--explanation-save-path` and/or `--output-path` explicitly.
