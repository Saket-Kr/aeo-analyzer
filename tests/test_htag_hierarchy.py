import pytest

from app.services.aeo_checks.htag_hierarchy import HtagHierarchyCheck
from app.services.content_parser import ParsedContent


def _make_content(headings: list[tuple[str, str]]) -> ParsedContent:
    return ParsedContent(
        first_paragraph="",
        headings=headings,
        clean_text="",
        sentences=[],
        is_html=True,
        raw="",
    )


@pytest.fixture
def check():
    return HtagHierarchyCheck()


def test_valid_hierarchy(check):
    headings = [("h1", "Title"), ("h2", "Section"), ("h3", "Sub"), ("h2", "Another")]
    result = check.run(_make_content(headings))
    assert result.score == 20
    assert result.passed is True
    assert result.details.violations == []


def test_missing_h1(check):
    headings = [("h2", "Section"), ("h3", "Sub")]
    result = check.run(_make_content(headings))
    assert result.score == 0
    assert "Missing H1" in result.details.violations[0]


def test_multiple_h1(check):
    headings = [("h1", "First"), ("h2", "Section"), ("h1", "Second")]
    result = check.run(_make_content(headings))
    assert any("Multiple H1" in v for v in result.details.violations)


def test_skipped_level(check):
    headings = [("h1", "Title"), ("h3", "Skipped H2")]
    result = check.run(_make_content(headings))
    assert result.score == 12
    assert any("skipped" in v.lower() for v in result.details.violations)


def test_heading_before_h1(check):
    headings = [("h2", "Before"), ("h1", "Title"), ("h2", "After")]
    result = check.run(_make_content(headings))
    assert any("before the first H1" in v for v in result.details.violations)
    assert result.score == 12


def test_no_headings(check):
    result = check.run(_make_content([]))
    assert result.score == 0
    assert result.details.h_tags_found == []


def test_three_plus_violations_gives_zero(check):
    headings = [
        ("h3", "Before1"),
        ("h2", "Before2"),
        ("h4", "Before3"),
        ("h1", "Title"),
    ]
    result = check.run(_make_content(headings))
    assert result.score == 0
    assert len(result.details.violations) >= 3


def test_h_tags_found_ordered(check):
    headings = [("h1", "T"), ("h2", "A"), ("h2", "B"), ("h3", "C")]
    result = check.run(_make_content(headings))
    assert result.details.h_tags_found == ["h1", "h2", "h2", "h3"]


def test_recommendation_for_missing_h1(check):
    result = check.run(_make_content([("h2", "No title")]))
    assert result.recommendation is not None
    assert "H1" in result.recommendation


def test_no_recommendation_when_valid(check):
    headings = [("h1", "Title"), ("h2", "Section")]
    result = check.run(_make_content(headings))
    assert result.recommendation is None
