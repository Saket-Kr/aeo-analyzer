import pytest

from app.services.aeo_checks.readability import ReadabilityCheck
from app.services.content_parser import ParsedContent


def _make_content(text: str, sentences: list[str] | None = None) -> ParsedContent:
    return ParsedContent(
        first_paragraph="",
        headings=[],
        clean_text=text,
        sentences=sentences or text.split(". "),
        is_html=False,
        raw=text,
    )


@pytest.fixture
def check():
    return ReadabilityCheck()


def test_grade_in_target_range(check):
    text = (
        "Good writing makes your website easier to find online. "
        "Short sentences help readers follow your main ideas. "
        "Using simple words keeps people on the page longer. "
        "Each article should focus on just one clear topic. "
        "Adding helpful examples makes complex ideas easier to understand."
    )
    sentences = [s.strip() for s in text.split(". ") if s.strip()]
    content = _make_content(text, sentences)
    result = check.run(content)
    assert 7.0 <= result.details.fk_grade_level <= 9.0
    assert result.score == 20
    assert result.passed is True


def test_too_complex(check):
    text = (
        "The epistemological ramifications of computational linguistics "
        "necessitate a comprehensive understanding of morphosyntactic phenomena. "
        "Interdisciplinary methodological frameworks facilitate the disambiguation "
        "of polysemous lexical constructions through distributional semantics. "
        "The theoretical underpinnings of transformational generative grammar "
        "have substantially influenced contemporary natural language processing architectures."
    )
    sentences = [s.strip() for s in text.split(". ") if s.strip()]
    content = _make_content(text, sentences)
    result = check.run(content)
    assert result.details.fk_grade_level > 11.0
    assert result.score == 0


def test_too_simple(check):
    text = "The cat sat. The dog ran. A bird flew. I ate food. He is big."
    sentences = [s.strip() for s in text.split(". ") if s.strip()]
    content = _make_content(text, sentences)
    result = check.run(content)
    assert result.details.fk_grade_level < 5.0
    assert result.score == 0


def test_complex_sentences_returns_top_3(check):
    text = (
        "Dogs are great pets. "
        "The multifaceted epistemological investigation reveals contradictions. "
        "Cats sleep a lot. "
        "Comprehensive methodological frameworks necessitate interdisciplinary collaboration. "
        "Fish live in water. "
        "The ontological presuppositions underlying phenomenological hermeneutics are debatable."
    )
    sentences = [s.strip() for s in text.split(". ") if s.strip()]
    content = _make_content(text, sentences)
    result = check.run(content)
    assert len(result.details.complex_sentences) == 3


def test_fewer_than_3_sentences(check):
    text = "Simple test. Another one."
    sentences = ["Simple test.", "Another one."]
    content = _make_content(text, sentences)
    result = check.run(content)
    assert len(result.details.complex_sentences) == 2


def test_empty_text(check):
    content = _make_content("", [])
    result = check.run(content)
    assert result.details.fk_grade_level == 0.0
    assert result.details.complex_sentences == []


def test_target_range_field(check):
    content = _make_content("This is a test sentence for the readability check.", ["This is a test sentence for the readability check."])
    result = check.run(content)
    assert result.details.target_range == "7-9"


def test_recommendation_for_complex(check):
    text = (
        "The epistemological ramifications of computational linguistics "
        "necessitate comprehensive understanding of morphosyntactic phenomena. "
        "Interdisciplinary methodological frameworks facilitate disambiguation "
        "of polysemous constructions through distributional semantics."
    )
    sentences = [s.strip() for s in text.split(". ") if s.strip()]
    content = _make_content(text, sentences)
    result = check.run(content)
    assert result.details.fk_grade_level > 9.0
    assert result.recommendation is not None
    assert "Shorten sentences" in result.recommendation


def test_recommendation_for_simple(check):
    text = "The cat sat. The dog ran. A bird flew. He is big. She is tall."
    sentences = [s.strip() for s in text.split(". ") if s.strip()]
    content = _make_content(text, sentences)
    result = check.run(content)
    assert result.details.fk_grade_level < 7.0
    assert result.recommendation is not None
    assert "substantive" in result.recommendation
