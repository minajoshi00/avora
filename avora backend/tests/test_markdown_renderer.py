import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skills.markdown_renderer import markdown_to_html


def test_heading_converts_and_strips_raw_hashes():
    html = markdown_to_html("### Important points")
    assert "<h3" in html and "Important points" in html
    assert "###" not in html


def test_bold_italic_inline_code():
    html = markdown_to_html("**bold** *italic* `code()`")
    assert "<b" in html and "bold" in html
    assert "<i>italic</i>" in html
    assert "<code" in html and "code()" in html
    assert "**" not in html and "`" not in html


def test_bullet_list_each_item_own_line():
    html = markdown_to_html("* First item\n* Second item\n* Third item")
    assert "<ul" in html
    assert html.count("<li") == 3


def test_numbered_list_not_collapsed():
    html = markdown_to_html("1. One\n2. Two\n3. Three")
    assert "<ol" in html
    assert html.count("<li") == 3
    # items must be inside <li>, not flattened text
    assert "<li style='margin: 3px 0;'>One</li>" in html


def test_paragraphs_preserve_separation():
    html = markdown_to_html("One.\n\nTwo.\n\nThree.")
    assert html.count("<p") == 3


def test_code_block_preserved():
    html = markdown_to_html("```python\nprint(\"hello\")\n```")
    assert "<pre" in html and "print(" in html and "hello" in html
    assert "language-python" in html


def test_table_renders():
    html = markdown_to_html("| A | B |\n| --- | --- |\n| 1 | 2 |")
    assert "<table" in html and "<td" in html


def test_blockquote_converts_not_raw_gt():
    html = markdown_to_html("> This is a quote.")
    assert "<blockquote" in html
    assert "&gt;" not in html


def test_empty_and_whitespace_return_empty():
    assert markdown_to_html("") == ""
    # whitespace-only produces no visible content (ghost-bubble protection
    # happens in the UI layer via .strip(), renderer must not crash)
    html = markdown_to_html("   ")
    assert "<p" not in html


def test_no_stray_p_or_br_inside_blocks_regression():
    """Regression: line-break conversion must not inject </p> or <br>
    inside headings/lists/tables (caused wall-of-text rendering)."""
    src = (
        "### Title\n\n"
        "Intro paragraph.\n\n"
        "1. One\n2. Two\n\n"
        "**End.**"
    )
    html = markdown_to_html(src)
    # No </p> directly after a heading close
    assert "</h3></p>" not in html
    # No <br> between <ol> open and first <li>
    assert "<ol" in html and "<br><li" not in html


def test_streaming_partial_list_drops_dangling_marker():
    html = markdown_to_html("### How this works\n\n1. First\n2.")
    assert "<li" in html and "First" in html
    # dangling "2." must not leak as raw text
    assert "2." not in html


# -----------------------------------------------------------------
# Citation / step-badge cleanup
# -----------------------------------------------------------------

def test_citation_markers_stripped_out_of_sentences():
    html = markdown_to_html(
        "This is an explanation [1] with a citation marker [2]."
    )
    assert "<p" in html
    assert "[1]" not in html and "[2]" not in html
    # the surrounding prose remains
    assert "explanation" in html and "citation marker" in html


def test_step_badges_stripped_not_wall_of_citations():
    src = ("First, open the application [1] then configure the settings [2] "
           "and finally restart it [3].")
    html = markdown_to_html(src)
    for badge in ("[1]", "[2]", "[3]"):
        assert badge not in html


def test_legitimate_brackets_preserved():
    html = markdown_to_html(
        "The 2026 [release] includes version [1.2] and year [2026] was big."
    )
    assert "[release]" in html
    assert "[1.2]" in html
    assert "[2026]" in html


def test_reference_context_marker_preserved():
    html = markdown_to_html("Use [1] as the first reference.")
    assert "[1]" in html


def test_citation_markers_not_stripped_from_code_blocks():
    html = markdown_to_html(
        "```python\n# refs [1] and [2]\nprint(1)\n```"
    )
    assert "[1]" in html and "[2]" in html


# -----------------------------------------------------------------
# Collapsed / run-on list structure
# -----------------------------------------------------------------

def test_crammed_single_line_numbered_list_split_into_items():
    html = markdown_to_html(
        "1. Start the application 2. Attach the file 3. Configure the settings"
    )
    assert html.count("<li") == 3
    assert "Start the application" in html
    assert "Attach the file" in html
    assert "Configure the settings" in html


def test_crlf_paragraphs_preserve_structure():
    html = markdown_to_html("One.\r\n\r\nTwo.\r\n\r\nThree.")
    assert html.count("<p") == 3


# -----------------------------------------------------------------
# Realistic live wall-of-text regression (screenshot scenario)
# -----------------------------------------------------------------

def _screenshot_response() -> str:
    """Replicates the content/shape that previously rendered as a wall of text."""
    return (
        "Scientific learning is a structured way to build knowledge.\n"
        "It uses these main steps that help keep things organized and logical:\n\n"
        "1. Observation: You notice something and wonder about it.\n"
        "2. Question: You ask a question about what you saw.\n"
        "3. Hypothesis: You make a guess about why it happens.\n"
        "4. Experiment: You test your guess with a fair test.\n"
        "5. Analysis & Conclusion: You look at the results.\n"
        "6. Share & Repeat: You share findings and try again.\n\n"
        "Let's walk through a super simple example...\n\n"
        "**Simple Example:** Why is my toast always burnt?\n\n"
        "1. Observation: The toast comes out dark almost every time.\n"
        "2. Question: Why does it keep getting burnt?"
    )


def _assert_not_wall_of_text(html, label):
    """Assert the HTML has separate list items, paragraphs and two lists."""
    assert html.count("<ol") == 2, f"{label}: expected two <ol>, got {html.count('<ol')}"
    assert html.count("<li") == 8, f"{label}: expected eight <li>, got {html.count('<li')}"
    # the separating prose must NOT be absorbed into a list item
    assert "walk through a super simple example" in html
    assert "<li style='margin: 3px 0;'>Share" in html  # list ends before prose
    assert html.count("<p") >= 3, f"{label}: expected >=3 paragraphs, got {html.count('<p')}"
    assert "<b" in html  # bold label survives


def test_screenshot_six_step_list_not_wall_of_text():
    html = markdown_to_html(_screenshot_response())
    _assert_not_wall_of_text(html, "LF")


def test_screenshot_six_step_list_crlf_identical():
    html = markdown_to_html(_screenshot_response().replace("\n", "\r\n"))
    _assert_not_wall_of_text(html, "CRLF")


def test_screenshot_streamed_via_chunk_helper_not_wall_of_text():
    """The full live path: streaming chunk helper + renderer must keep blocks."""
    full = _screenshot_response()
    try:
        from skills.chat_worker import _simulate_stream_chunks
    except Exception:
        import pytest
        pytest.skip("chat_worker unavailable in this environment")
    streamed = "".join(_simulate_stream_chunks(full))
    # the streaming helper must not collapse the newlines
    assert streamed == full, "streaming helper altered the response text"
    html = markdown_to_html(streamed)
    _assert_not_wall_of_text(html, "streamed")


def test_streaming_chunk_helper_preserves_newlines():
    from skills.chat_worker import _simulate_stream_chunks
    src = "Intro line.\n\n1. First item\n2. Second item\n\nNext paragraph."
    assert "".join(_simulate_stream_chunks(src)) == src
    assert "\n\n" in "".join(_simulate_stream_chunks(src))
