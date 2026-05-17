from scripts.generate_vocabulary_for_remnote import merge_vocabularies


def test_merge_vocabularies_combines_and_dedupes():
    vocabularies = [["apple", "banana"], ["banana", "cherry"], ["date"]]
    assert merge_vocabularies(vocabularies) == {"apple", "banana", "cherry", "date"}


def test_merge_vocabularies_empty_input():
    assert merge_vocabularies([]) == set()


def test_merge_vocabularies_single_list():
    assert merge_vocabularies([["apple", "banana"]]) == {"apple", "banana"}
