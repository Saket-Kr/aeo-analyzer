import pytest

from app.services.aeo_checks.direct_answer import DirectAnswerCheck
from app.services.content_parser import ParsedContent


def _make_content(first_paragraph: str) -> ParsedContent:
    return ParsedContent(
        first_paragraph=first_paragraph,
        headings=[],
        clean_text=first_paragraph,
        sentences=[first_paragraph],
        is_html=False,
        raw=first_paragraph,
    )


@pytest.fixture
def check():
    return DirectAnswerCheck()


def test_short_declarative_no_hedge(check):
    content = _make_content("Python is a high-level programming language used for web development.")
    result = check.run(content)
    assert result.score == 20
    assert result.passed is True
    assert result.details.is_declarative is True
    assert result.details.has_hedge_phrase is False


def test_exceeds_90_words(check):
    words = " ".join(["word"] * 95)
    content = _make_content(f"This is {words} in a sentence.")
    result = check.run(content)
    assert result.score == 0
    assert result.details.word_count > 90


def test_between_61_and_90_words(check):
    words = " ".join(["important"] * 65)
    content = _make_content(f"This is {words} in a sentence.")
    result = check.run(content)
    assert result.score == 8
    assert 61 <= result.details.word_count <= 90


def test_exactly_61_words(check):
    words = " ".join(["data"] * 59)
    content = _make_content(f"This is {words}.")
    result = check.run(content)
    assert result.score == 8
    assert result.details.word_count == 61


def test_hedge_phrase_detected(check):
    content = _make_content("Python is a programming language. It depends on the use case which one to pick.")
    result = check.run(content)
    assert result.details.has_hedge_phrase is True
    assert result.score == 12


def test_not_declarative_question(check):
    content = _make_content("What is Python used for in web development?")
    result = check.run(content)
    assert result.details.is_declarative is False
    assert result.score == 12


def test_empty_paragraph(check):
    content = _make_content("")
    result = check.run(content)
    assert result.details.word_count == 0
    assert result.score == 0
    assert result.details.is_declarative is False
    assert result.recommendation is not None


def test_hedge_with_declarative(check):
    content = _make_content("The best framework may vary depending on project requirements.")
    result = check.run(content)
    assert result.details.has_hedge_phrase is True
    assert result.score == 12


def test_recommendation_for_long_paragraph(check):
    words = " ".join(["word"] * 95)
    content = _make_content(f"This is {words} in a sentence.")
    result = check.run(content)
    assert result.recommendation is not None
    assert "Trim" in result.recommendation


def test_no_recommendation_when_perfect(check):
    content = _make_content("Python is a high-level programming language.")
    result = check.run(content)
    assert result.recommendation is None
