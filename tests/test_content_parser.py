import pytest

from app.services.content_parser import parse_content


def test_html_first_paragraph():
    html = "<h1>Title</h1><p>First paragraph here.</p><p>Second paragraph.</p>"
    result = parse_content(html)
    assert result.first_paragraph == "First paragraph here."
    assert result.is_html is True


def test_plain_text_first_paragraph():
    text = "First paragraph here.\n\nSecond paragraph here."
    result = parse_content(text)
    assert result.first_paragraph == "First paragraph here."
    assert result.is_html is False


def test_headings_extraction():
    html = "<h1>Title</h1><h2>Section A</h2><h3>Sub</h3><h2>Section B</h2>"
    result = parse_content(html)
    assert result.headings == [
        ("h1", "Title"),
        ("h2", "Section A"),
        ("h3", "Sub"),
        ("h2", "Section B"),
    ]


def test_boilerplate_stripped():
    html = """
    <nav>Navigation stuff</nav>
    <main><p>Real content here.</p></main>
    <footer>Footer stuff</footer>
    """
    result = parse_content(html)
    assert "Navigation" not in result.clean_text
    assert "Footer" not in result.clean_text
    assert "Real content" in result.clean_text


def test_prefers_main_tag():
    html = """
    <header><h2>Site Title</h2></header>
    <main>
        <h1>Article</h1>
        <p>Content inside main.</p>
    </main>
    <aside><h3>Sidebar</h3></aside>
    """
    result = parse_content(html)
    assert result.first_paragraph == "Content inside main."


def test_sentence_splitting():
    html = "<p>First sentence. Second sentence. Third one.</p>"
    result = parse_content(html)
    assert len(result.sentences) >= 2


def test_empty_content():
    result = parse_content("")
    assert result.first_paragraph == ""
    assert result.headings == []
    assert result.sentences == []


def test_url_fetched_flag():
    html = "<html><body><p>Content</p></body></html>"
    result = parse_content(html, is_url_fetched=True)
    assert result.is_html is True


def test_plain_text_no_headings():
    text = "Just plain text without any HTML."
    result = parse_content(text)
    assert result.headings == []
    assert result.is_html is False


def test_html_without_p_tags():
    html = "<h1>Title</h1><div>Some content in divs only.</div>"
    result = parse_content(html)
    assert result.first_paragraph != ""
