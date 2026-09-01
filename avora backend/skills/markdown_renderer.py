"""
========================================================================
markdown_renderer.py
NOVA - Markdown to HTML converter for rich chat messages
========================================================================
Converts Markdown text to styled HTML for QTextBrowser rendering.
Supports: bold, italic, code, code blocks, lists, tables, headings,
links, images, and blockquotes.
========================================================================
"""

import re
from typing import Any

_AMP = "&" + "amp;"
_LT = "&" + "lt;"
_GT = "&" + "gt;"


def _mask_incomplete_markers(text: str) -> str:
    """Hide trailing incomplete Markdown markers while streaming so the
    user never sees raw '###', '**', or a dangling backtick/fence.

    Only touches markers at the very END of the text (streaming edge);
    complete markers earlier in the text are untouched.
    """
    # Fenced code block opened but not closed: drop the raw opening fence
    # line (including the language tag) to avoid rendering raw ``` while
    # the block streams in.
    if text.count("```") % 2 == 1:
        idx = text.rfind("```")
        rest = text[idx + 3:]
        nl = rest.find("\n")
        text = text[:idx] + (rest[nl + 1:] if nl != -1 else "")
        if not text.strip():
            return ""
    # Trailing bare heading marker(s) with no content yet.
    text = re.sub(r"(?:^|\n)#{1,6}\s*$", "", text)
    # Unbalanced bold/inline-code markers at the tail.
    if text.count("**") % 2 == 1:
        text = text[: text.rfind("**")]
    for marker in ("__", "`"):
        if text.count(marker) % 2 == 1:
            text = text[: text.rfind(marker)]
    # Single trailing '*' or '_' that is not a bullet/list item and not
    # part of a closing '**'/'__' emphasis pair.
    if text.endswith("*") and not text.endswith("**") and not re.search(
        r"(?:^|\n)\*\s", text[-4:]
    ):
        text = text[:-1]
    elif text.endswith("_") and not text.endswith("__") and not re.search(
        r"(?:^|\n)_\s", text[-4:]
    ):
        text = text[:-1]
    return text


def markdown_to_html(text: Any, streaming: bool = False) -> str:
    """Convert Markdown text to styled HTML."""
    if not text:
        return ""

    html = str(text)

    # Normalize line endings so CRLF streaming / model output does not
    # collapse paragraph and list block structure.
    html = html.replace("\r\n", "\n").replace("\r", "\n")

    # While streaming, hide trailing incomplete markers (raw ### / ** / `)
    # so the user never sees Markdown syntax mid-stream.
    if streaming:
        html = _mask_incomplete_markers(html)

    # Escape HTML entities first
    html = _escape_html(html)

    # Process in order (blocks first, then inline)
    html = _convert_code_blocks(html)
    html = _convert_blockquotes(html)
    html = _convert_tables(html)
    html = _convert_headings(html)
    html = _convert_horizontal_rules(html)
    html = _convert_unordered_lists(html)
    html = _convert_ordered_lists(html)
    html = _convert_inline_code(html)
    html = _convert_images(html)
    html = _convert_links(html)
    html = _convert_bold(html)
    html = _convert_italic(html)
    html = _convert_strikethrough(html)
    html = _convert_line_breaks(html)
    # Strip LLM-generated inline citation markers (applied AFTER conversion so
    # it hits text nodes inside <p>/<li> but leaves code/link/table blocks and
    # legitimate bracketed content untouched).
    html = _strip_citation_markers(html)
    return (
        '<div style="font-family: \'Segoe UI\', sans-serif; '
        'font-size: 15px; line-height: 1.65; color: #F5F5F5; '
        'overflow-wrap: break-word; word-wrap: break-word; word-break: break-word;">'
        + html
        + "</div>"
    )


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    text = text.replace("&", _AMP)
    text = text.replace("<", _LT)
    text = text.replace(">", _GT)
    return text


def _unescape_html(text: str) -> str:
    """Reverse HTML escaping."""
    text = text.replace(_GT, ">")
    text = text.replace(_LT, "<")
    text = text.replace(_AMP, "&")
    return text


# -----------------------------------------------------------------
# Inline citation / step-badge cleanup
# -----------------------------------------------------------------
# Some models append inline citation markers ("[1]", "[2]", ...) to their own
# text. These are NOT part of the intended answer — they render as small
# numeric badges inside normal sentences. This cleanup removes them at the
# rendering boundary while preserving legitimate bracketed content:
#   - non-numeric brackets            -> [release]
#   - decimal / version brackets      -> [1.2]
#   - 4-digit years                   -> [2026]
#   - markers near reference language -> "reference [1]"
# Code blocks, inline code, links and tables are protected from the cleanup so
# code/link text that legitimately contains a bracket is never altered.
# -----------------------------------------------------------------

_CITE_TOKEN = re.compile(r"\[\s*(\d+)\s*\]")
_CITE_PROTECT = re.compile(
    r"(<pre\b.*?</pre>"
    r"|<code\b.*?</code>"
    r"|<a\b[^>]*>.*?</a>"
    r"|<table\b.*?</table>)",
    re.DOTALL,
)
_REFERENCE_WORDS = frozenset({
    "reference", "references", "source", "sources", "figure", "fig",
    "table", "item", "items", "section", "step", "version",
    "footnote", "note",
})


def _strip_citation_markers(html: str) -> str:
    """Remove inline citation markers from rendered HTML (documented above)."""
    parts = _CITE_PROTECT.split(html)
    rebuilt = []
    for part in parts:
        if part and _CITE_PROTECT.fullmatch(part):
            rebuilt.append(part)  # protect code / link / table regions
            continue
        rebuilt.append(_strip_cites_in_text(part))
    return "".join(rebuilt)


def _strip_cites_in_text(text: str) -> str:
    def replacer(match):
        number = match.group(1)
        # 4-digit tokens look like years, not citations -> keep [2026]
        if len(number) == 4 and number.isdigit():
            return match.group(0)
        before = text[max(0, match.start() - 60):match.start()]
        after = text[match.end():match.end() + 80]
        if _tail_reference(before) or _head_reference(after):
            return match.group(0)  # keep legitimate reference-like markers
        return ""

    return _CITE_TOKEN.sub(replacer, text)


def _tail_reference(before: str) -> bool:
    """True if a reference-noun appears just before the marker."""
    words = re.findall(r"[A-Za-z]+", before.lower())
    return any(w in _REFERENCE_WORDS for w in words[-3:])


def _head_reference(after: str) -> bool:
    """True if a reference-noun follows the marker within a few tokens."""
    words = re.findall(r"[A-Za-z]+", after.lower())
    return any(w in _REFERENCE_WORDS for w in words[:6])


def _convert_code_blocks(text: str) -> str:
    """Convert ```code blocks``` to <pre><code>."""
    pattern = r"```(\w*)?\s*\n(.*?)```"

    def replacer(match):
        language = match.group(1) or ""
        code = match.group(2)
        # Remove trailing newline if present
        code = _unescape_html(code).rstrip("\n")
        lang_class = (
            ' class="language-' + language + '"' if language else ""
        )
        escaped_code = _escape_html(code)
        return (
            '<pre style="background: #1A1A2E; border: 1px solid #303044; '
            'border-radius: 8px; padding: 12px; overflow-x: auto; '
            'margin: 8px 0;"><code'
            + lang_class
            + ' style="color: #E8E8E8; font-family: '
            + "'Cascadia Code', 'Fira Code', monospace; "
            + 'font-size: 13px; line-height: 1.5;">'
            + escaped_code
            + "</code></pre>"
        )

    return re.sub(pattern, replacer, text, flags=re.DOTALL)


def _convert_inline_code(text: str) -> str:
    """Convert `inline code` to <code>."""
    # Only match inline code (not inside pre blocks)
    pattern = r"(?<!`)`([^`]+)`(?!`)"

    def replacer(match):
        code = match.group(1).strip()
        return (
            '<code style="background: #1E1E32; border: 1px solid #3A3A50; '
            'border-radius: 4px; padding: 2px 6px; font-family: '
            + "'Cascadia Code', 'Fira Code', monospace; "
            + 'font-size: 13px; color: #FF9E64;">'
            + code
            + "</code>"
        )

    return re.sub(pattern, replacer, text)


def _convert_bold(text: str) -> str:
    """Convert **bold** to <b>."""
    return re.sub(
        r"\*\*(.+?)\*\*",
        '<b style="color: #FFFFFF; font-weight: 700;">\\1</b>',
        text,
    )


def _convert_italic(text: str) -> str:
    """Convert *italic* to <i>."""
    return re.sub(
        r"(?<!\*)\*([^*]+)\*(?!\*)",
        "<i>\\1</i>",
        text,
    )


def _convert_strikethrough(text: str) -> str:
    """Convert ~~strikethrough~~ to <s>."""
    return re.sub(r"~~(.+?)~~", "<s>\\1</s>", text)


def _convert_headings(text: str) -> str:
    """Convert # headings to <h1-h6>."""
    for level in range(6, 0, -1):
        pattern = r"^" + "#" * level + r"\s+(.+?)$"
        replacement = (
            '<h'
            + str(level)
            + ' style="color: #FFFFFF; margin: 12px 0 6px 0; '
            + 'font-weight: 600;">\\1</h'
            + str(level)
            + ">"
        )
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
    return text


def _convert_unordered_lists(text: str) -> str:
    """Convert - or * list items to <ul><li>."""
    lines = text.split("\n")
    result = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        # Graceful streaming: drop dangling markers with no content yet
        if re.match(r"^(\d+\.|[-*+])\s*$", stripped):
            continue
        match = re.match(r"^[-*+]\s+(.+)$", stripped)
        if match:
            if not in_list:
                result.append(
                    "<ul style='margin: 6px 0; padding-left: 24px; "
                    "list-style-type: disc;'>"
                )
                in_list = True
            content = match.group(1)
            result.append("<li style='margin: 3px 0;'>" + content + "</li>")
        else:
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append(line)

    if in_list:
        result.append("</ul>")

    return "\n".join(result)


def _convert_ordered_lists(text: str) -> str:
    """Convert 1. 2. list items to <ol><li>.

    Also breaks a numerically-crammed single line ("1. A 2. B 3. C") into
    separate <li> items so compressed model output does not collapse into one
    run-on item.
    """
    lines = text.split("\n")
    result = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        # Graceful streaming: drop dangling markers with no content yet
        if re.match(r"^(\d+\.|[-*+])\s*$", stripped):
            continue
        items = _split_numbered_line(stripped)
        if items:
            if not in_list:
                result.append(
                    "<ol style='margin: 6px 0; padding-left: 24px;'>"
                )
                in_list = True
            for content in items:
                result.append("<li style='margin: 3px 0;'>" + content + "</li>")
        else:
            if in_list:
                result.append("</ol>")
                in_list = False
            result.append(line)

    if in_list:
        result.append("</ol>")

    return "\n".join(result)


def _split_numbered_line(stripped: str):
    """Split a line starting with a numbered marker into its list items.

    Returns a list of item contents, or None if the line is not a numbered
    list line. Handles both the normal one-marker-per-line case and the
    crammed single-line case ("1. A 2. B 3. C").
    """
    match = re.match(r"^(\d+)\.\s+(.+)$", stripped)
    if not match:
        return None
    rest = match.group(2)
    # Split consecutive markers on the same line:  "A 2. B 3. C" -> ["A","B","C"]
    pieces = re.split(r"\s+\d+\.\s+", rest)
    items = [piece.strip() for piece in pieces if piece.strip()]
    return items if items else None


def _convert_blockquotes(text: str) -> str:
    """Convert > blockquotes to styled blockquotes.

    NOTE: this runs AFTER HTML escaping, so '>' is already '&gt;'.
    The old pattern '^>\\s+' could never match — quotes rendered as raw
    '&gt;' text. Consecutive quote lines are grouped into one block.
    """
    lines = text.split("\n")
    result = []
    quote_buf = []

    def flush_quote():
        if not quote_buf:
            return
        content = "<br>".join(quote_buf)
        result.append(
            '<blockquote style="border-left: 3px solid #00CC6A; '
            "background: rgba(0, 255, 136, 0.06); "
            'padding: 8px 12px; margin: 8px 0; '
            'border-radius: 4px; color: #C8D8CC;">'
            + content
            + "</blockquote>"
        )
        quote_buf.clear()

    for line in lines:
        match = re.match(r"^&gt;\s?(.*)$", line.strip())
        if match:
            quote_buf.append(match.group(1))
        else:
            flush_quote()
            result.append(line)
    flush_quote()
    return "\n".join(result)


def _convert_tables(text: str) -> str:
    """Convert Markdown tables to HTML tables."""
    lines = text.split("\n")
    result = []
    in_table = False
    table_lines = []

    for line in lines:
        stripped = line.strip()
        is_table_row = stripped.startswith("|") and stripped.endswith("|")

        if is_table_row:
            table_lines.append(stripped)
            if not in_table:
                in_table = True
        else:
            if in_table:
                result.append(_render_table(table_lines))
                table_lines = []
                in_table = False
            result.append(line)

    if in_table:
        result.append(_render_table(table_lines))

    return "\n".join(result)


def _render_table(rows: list) -> str:
    """Render parsed table rows as HTML."""
    if len(rows) < 2:
        return "\n".join(rows)

    html_parts = ['<div style="overflow-x: auto; margin: 8px 0;">']
    html_parts.append(
        '<table style="border-collapse: collapse; width: 100%; '
        'border: 1px solid #303044;">'
    )

    # Header row
    headers = [h.strip() for h in rows[0].strip("|").split("|")]
    html_parts.append("<thead><tr>")
    for header in headers:
        html_parts.append(
            '<th style="border: 1px solid #303044; padding: 8px 12px; '
            'background: #1A1A2E; color: #FFFFFF; font-weight: 600; '
            'text-align: left;">' + header + "</th>"
        )
    html_parts.append("</tr></thead>")

    # Data rows
    html_parts.append("<tbody>")
    data_rows = rows[2:] if len(rows) > 2 else []
    for i, row in enumerate(data_rows):
        cells = [c.strip() for c in row.strip("|").split("|")]
        bg = "#151525" if i % 2 == 0 else "#0F0F1E"
        html_parts.append('<tr style="background: ' + bg + ';">')
        for cell in cells:
            html_parts.append(
                '<td style="border: 1px solid #303044; padding: 8px 12px; '
                'color: #E0E0E8;">' + cell + "</td>"
            )
        html_parts.append("</tr>")
    html_parts.append("</tbody>")

    html_parts.append("</table>")
    html_parts.append("</div>")
    return "\n".join(html_parts)


def _convert_images(text: str) -> str:
    """Convert ![alt](src) to <img>."""
    pattern = r"!\[([^\]]*)\]\(([^)]+)\)"

    def replacer(match):
        alt = match.group(1) or ""
        src = match.group(2)
        return (
            '<img src="' + src + '" alt="' + alt + '" '
            'style="max-width: 100%; max-height: 400px; '
            'border-radius: 8px; margin: 8px 0; '
            'border: 1px solid #303044;" />'
        )

    return re.sub(pattern, replacer, text)


def _convert_links(text: str) -> str:
    """Convert [text](url) to <a>."""
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    def replacer(match):
        link_text = match.group(1)
        url = match.group(2)
        return (
            '<a href="' + url + '" style="color: #6C63FF; '
            'text-decoration: none; border-bottom: 1px solid '
            'rgba(108, 99, 255, 0.3);">' + link_text + "</a>"
        )

    return re.sub(pattern, replacer, text)


def _convert_horizontal_rules(text: str) -> str:
    """Convert --- or *** to <hr>."""
    pattern = r"^[-*]{3,}\s*$"
    return re.sub(
        pattern,
        '<hr style="border: none; border-top: 1px solid #303044; '
        'margin: 16px 0;" />',
        text,
        flags=re.MULTILINE,
    )


def _convert_line_breaks(text: str) -> str:
    """Convert newlines to paragraph/line breaks WITHOUT corrupting block HTML.

    Previous implementation only protected <pre>, which injected stray </p>
    fragments and <br> tags inside <h1-6>, <ol>/<ul>, <table> and
    <blockquote> blocks — producing malformed HTML that Qt's rich-text
    engine rendered as a wall of text. Block-level elements are now left
    untouched; only plain text segments get paragraph conversion.
    """
    block_pattern = re.compile(
        r"(<pre.*?</pre>"
        r"|<div style=\"overflow-x[^\"]*\"[^>]*>.*?</div>"
        r"|<table.*?</table>"
        r"|<ol.*?</ol>"
        r"|<ul.*?</ul>"
        r"|<blockquote.*?</blockquote>"
        r"|<h[1-6].*?</h[1-6]>"
        r"|<hr[^>]*/?>)",
        re.DOTALL,
    )

    def _convert_segment(segment: str) -> str:
        segment = segment.strip("\n")
        if not segment.strip():
            return ""
        paragraphs = segment.split("\n\n")
        parts = []
        for para in paragraphs:
            para = para.strip("\n")
            if not para.strip():
                continue
            # Soft line breaks inside a paragraph
            para = para.replace("\n", "<br>")
            parts.append("<p style='margin: 8px 0;'>" + para + "</p>")
        return "".join(parts)

    parts = block_pattern.split(text)
    out = []
    for part in parts:
        if not part:
            continue
        if block_pattern.fullmatch(part):
            out.append(part)  # leave block-level HTML intact
        else:
            out.append(_convert_segment(part))
    return "".join(out)
