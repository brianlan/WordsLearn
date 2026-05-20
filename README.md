# WordsLearn (单词乐)

A Python CLI tool that generates bilingual (English-Chinese) vocabulary flashcards for [RemNote](https://remnote.com) using LLM-powered word explanations.

## Overview

WordsLearn reads plain-text vocabulary lists, calls an LLM to generate rich, structured explanations for each word, and outputs RemNote-compatible flashcards with bilingual example sentences. It caches explanations as JSON so you can incrementally build your deck without re-generating existing words.

## Features

- **LLM-powered explanations** — Uses an [OpenCode](https://opencode.ai) agent (`word-explanation-generator`) to generate structured word data including:
  - American & British IPA
  - Collins-style definitions (bracketed target word)
  - Three bilingual example sentences per meaning
  - Context-replaceable synonyms
  - Derived forms
  - Common collocations
- **Bilingual flashcards** — Generates both English and Chinese RemNote flashcards from each example sentence
- **Parallel generation** — Multi-threaded word processing with configurable worker count
- **Resume support** — Explanations are cached in JSON; skips already-processed words on subsequent runs
- **JSON repair** — Handles malformed LLM outputs with `json_repair` and Pydantic validation
- **Multi-model support** — Round-robin across multiple models to distribute API load

## Project Structure

```
WordsLearn/
├── scripts/
│   ├── generate_explanations.py             # Step 1: generate explanations JSON
│   ├── generate_flashcards.py               # Step 2: generate RemNote flashcard TXT
│   └── vocab_utils.py                       # Shared helpers
├── vocabularies/                            # Input word lists
│   ├── toefl.txt                            # 1201 TOEFL words
│   ├── shiwen.txt                           # Sample vocabulary
│   └── ref.txt                              # Reference vocabulary
├── explanations/
│   └── word_meaning.json                    # Cached LLM explanations
├── output/                                  # Generated flashcards
│   └── flash_cards_*.txt
├── templates/
│   └── word-explanation.md                  # Jinja2 template for full markdown output
├── tests/
│   └── test_scripts.py
├── .opencode/agents/
│   └── word-explanation-generator.md        # OpenCode agent prompt
└── requirements.txt
```

## Installation

```bash
pip install -r requirements.txt
```

Dependencies:
- `json_repair`
- `jinja2`
- `loguru`
- `tqdm`
- `pytest`
- `pydantic`

You also need the [OpenCode](https://opencode.ai) CLI installed and configured with at least one agent named `word-explanation-generator`.

## Usage

The workflow is two steps: first generate explanations, then generate flashcards.

### Step 1: Generate explanations

```bash
python -m scripts.generate_explanations \
  -i vocabularies/toefl.txt \
  --explanations-path explanations/toefl.json \
  --models model1 model2 \
  --num-workers 4
```

### Step 2: Generate flashcards

```bash
python -m scripts.generate_flashcards \
  -e explanations/toefl.json \
  -o output/flash_cards_toefl.txt
```

### CLI Arguments — `generate_explanations.py`

| Argument | Description |
|----------|-------------|
| `-i, --vocabularies` | One or more vocabulary list files (required) |
| `--explanations-path` | JSON output file for word explanations (required) |
| `--models` | One or more LLM models to use in round-robin (required) |
| `--startover` | Ignore existing cache and re-generate all words |
| `--num-workers` | Number of parallel worker threads (default: 1) |

### CLI Arguments — `generate_flashcards.py`

| Argument | Description |
|----------|-------------|
| `-e, --explanations-path` | JSON file with word explanations (required) |
| `-o, --output-path` | Output file for RemNote flashcards (required) |

### Vocabulary File Format

Plain text with one word per line. Lines starting with `#` are treated as comments and ignored.

```text
# Unit 1
abandon
abnormal
abolish
...
```

### Output Format

RemNote flashcards use a simple `==` delimiter between the question (example sentence with emphasized word) and the answer (IPA + definition + synonyms):

```text
We could see the mountains  _**afar**_  in the distance. == /əˈfɑːr/ : If something is  __**afar**__ , it is a long way away from you. [far away, distantly, far off]
我们可以看到 _**远处**_ 的群山。 == /əˈfɑːr/ : If something is  __**afar**__ , it is a long way away from you. [far away, distantly, far off]
```

## Running Tests

```bash
pytest tests/
```

## How It Works

1. **Read & merge** — Combines all vocabulary files into a deduplicated set of words.
2. **Generate explanations** — For each new word, calls the OpenCode agent with a structured prompt. The agent returns JSON with IPA, meanings, examples, synonyms, derived forms, and collocations.
3. **Cache** — Saves valid explanations to a JSON file for incremental builds.
4. **Generate flashcards** — Reads the cached explanations and transforms each example sentence into a pair of RemNote flashcards (English + Chinese).
5. **Write output** — Saves flashcards to a text file ready for import into RemNote.

## Customization

- **Agent prompt**: Edit `.opencode/agents/word-explanation-generator.md` to change LLM behavior.
- **Markdown template**: Modify `templates/word-explanation.md` to adjust the full explanation format (useful for non-flashcard output).
- **Styling**: The `create_card` and `emphasize` functions in `scripts/generate_flashcards.py` control RemNote bold/italic formatting.

## License

MIT
