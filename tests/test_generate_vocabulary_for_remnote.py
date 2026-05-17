from pathlib import Path

from scripts.generate_vocabulary_for_remnote import merge_vocabularies, read_vocabularies


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
