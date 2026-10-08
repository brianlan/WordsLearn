import itertools
import json
import subprocess
import sys
from pathlib import Path

from scripts import generate_explanations as generate_explanations_module
from scripts.generate_explanations import (
    generate_explanations,
    merge_vocabularies,
    read_vocabularies,
    write_explanations,
)


def test_merge_vocabularies_combines_and_dedupes():
    vocabularies = [["apple", "banana"], ["banana", "cherry"], ["date"]]
    assert merge_vocabularies(vocabularies) == {"apple", "banana", "cherry", "date"}


def test_merge_vocabularies_empty_input():
    assert merge_vocabularies([]) == set()


def test_merge_vocabularies_single_list():
    assert merge_vocabularies([["apple", "banana"]]) == {"apple", "banana"}


def test_read_vocabularies_skips_empty_and_comment_lines(tmp_path: Path):
    vocab_file = tmp_path / "vocab.txt"
    vocab_file.write_text("apple\n\n  \n# skip me\nbanana\n# another comment\n")
    assert read_vocabularies([vocab_file]) == [["apple", "banana"]]


def test_read_vocabularies_strips_whitespace(tmp_path: Path):
    vocab_file = tmp_path / "vocab.txt"
    vocab_file.write_text("  hello  \n  world  \n")
    assert read_vocabularies([vocab_file]) == [["hello", "world"]]


def test_read_vocabularies_multiple_files(tmp_path: Path):
    file1 = tmp_path / "vocab1.txt"
    file2 = tmp_path / "vocab2.txt"
    file1.write_text("apple\n# comment\nbanana\n")
    file2.write_text("cherry\n\n")
    assert read_vocabularies([file1, file2]) == [["apple", "banana"], ["cherry"]]


def test_generate_explanations_writes_after_each_word(tmp_path: Path, monkeypatch):
    save_path = tmp_path / "out.json"
    snapshots = []
    real_write = write_explanations

    def fake_run(cmd, **kwargs):
        word = cmd[-1].split("word: ")[1].split(" ")[0]
        payload = {
            "word": word,
            "american_ipa": "a",
            "british_ipa": "b",
            "derived_forms": [],
            "common_collocations": [],
            "meanings": [{"part_of_speech": "n.", "explanation": "e", "examples": [], "synonyms": []}],
        }
        return subprocess.CompletedProcess(cmd, 0, json.dumps(payload), "")

    def spy(explanations, path):
        snapshots.append(sorted(explanations))
        real_write(explanations, path)

    monkeypatch.setattr(generate_explanations_module.subprocess, "run", fake_run)
    monkeypatch.setattr(generate_explanations_module, "write_explanations", spy)
    generate_explanations(
        {"apple", "banana"},
        itertools.cycle(["model"]),
        agent="agent",
        num_workers=1,
        explanation_save_path=save_path,
    )

    assert len(snapshots) == 2  # one write per successfully generated word
    assert snapshots[-1] == ["apple", "banana"]
    assert sorted(json.loads(save_path.read_text())) == ["apple", "banana"]


def test_write_explanations_keeps_existing_entries(tmp_path: Path):
    save_path = tmp_path / "out.json"
    save_path.write_text(json.dumps({"apple": {"word": "apple"}, "banana": {"word": "old"}}))

    write_explanations({"banana": {"word": "new"}, "cherry": {"word": "cherry"}}, save_path)

    written = json.loads(save_path.read_text())
    assert sorted(written) == ["apple", "banana", "cherry"]
    assert written["banana"] == {"word": "new"}
    assert not list(tmp_path.glob("*.tmp"))  # atomic replace leaves no temp file behind


def test_generate_explanations_help():
    result = subprocess.run(
        [sys.executable, "-m", "scripts.generate_explanations", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Generate word explanations JSON" in result.stdout


def test_generate_flashcards_from_explanations_help():
    result = subprocess.run(
        [sys.executable, "-m", "scripts.generate_flashcards_from_explanations", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Generate Remnote flash cards" in result.stdout
