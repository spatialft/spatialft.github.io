"""Tests for extract_answer — the single function all accuracy numbers flow through."""

from src.dataset import extract_answer


def test_exact_match():
    assert extract_answer("left") == "left"
    assert extract_answer("upper-left") == "upper-left"
    assert extract_answer("below") == "below"


def test_case_insensitive():
    assert extract_answer("LEFT") == "left"
    assert extract_answer("Upper-Left") == "upper-left"


def test_trailing_whitespace():
    assert extract_answer("  right  ") == "right"
    assert extract_answer("above\n") == "above"


def test_ends_with_direction():
    assert extract_answer("The answer is upper-right") == "upper-right"
    assert extract_answer("A is to the left") == "left"


def test_direction_embedded_in_text():
    assert extract_answer("A is above B in the grid") == "above"


def test_longer_match_wins_over_suffix():
    # "upper-left" contains "left" — the longer match should win
    assert extract_answer("the answer is upper-left") == "upper-left"
    assert extract_answer("upper-left is the direction") == "upper-left"


def test_last_occurrence_wins():
    # When multiple directions appear, the last one (by end position) wins
    assert extract_answer("first left then right") == "right"
    assert extract_answer("above then below") == "below"


def test_think_tags_stripped():
    assert extract_answer("<think>some reasoning</think>left") == "left"
    assert extract_answer("<think>left is wrong</think>right") == "right"


def test_no_direction_returns_none():
    assert extract_answer("I don't know") is None
    assert extract_answer("") is None
    assert extract_answer("42") is None


def test_all_eight_directions():
    for d in ("left", "right", "above", "below", "upper-left", "upper-right", "lower-left", "lower-right"):
        assert extract_answer(d) == d
