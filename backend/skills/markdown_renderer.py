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


def markdown_to_html(text: Any) -> str:
    """Convert Markdown text to styled HTML."""
    if not text:
        return ""

    html = str(text)

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

    return (
        '<div style="font-family: \'Segoe UI\', sans-serif; '
        'line-height: 1.6; color: #F5F5F5; '
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
    """Convert 1. 2. list items to <ol><li>."""
    lines = text.split("\n")
    result = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        match = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if match:
            if not in_list:
                result.append(
                    "<ol style='margin: 6px 0; padding-left: 24px;'>"
                )
                in_list = True
            content = match.group(2)
            result.append("<li style='margin: 3px 0;'>" + content + "</li>")
        else:
            if in_list:
                result.append("</ol>")
                in_list = False
            result.append(line)

    if in_list:
        result.append("</ol>")

    return "\n".join(result)


def _convert_blockquotes(text: str) -> str:
    """Convert > blockquotes to styled blockquotes."""
    pattern = r"^>\s+(.+)$"

    def replacer(match):
        content = match.group(1)
        return (
            '<blockquote style="border-left: 3px solid #6C63FF; '
            "background: rgba(108, 99, 255, 0.08); "
            'padding: 8px 12px; margin: 8px 0; '
            'border-radius: 4px; color: #C0C0D0;">'
            + content
            + "</blockquote>"
        )

    return re.sub(pattern, replacer, text, flags=re.MULTILINE)


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
    """Convert double newlines to paragraph breaks."""
    # Protect pre and code blocks from line break conversion
    def _protect_pre(match):
        return match.group(0).replace("\n", "\x00")

    protected = re.sub(r"<pre.*?</pre>", _protect_pre, text, flags=re.DOTALL)

    # Double newlines = paragraph break
    protected = protected.replace("\n\n", "</p><p style='margin: 8px 0;'>")
    # Single newlines = line break
    protected = protected.replace("\n", "<br>")

    # Restore protected blocks
    protected = protected.replace("\x00", "\n")

    # Wrap in paragraph if not already wrapped
    if not protected.startswith("<"):
        protected = "<p style='margin: 8px 0;'>" + protected + "</p>"
    # Remove empty paragraphs
    protected = protected.replace(
        "<p style='margin: 8px 0;'></p>", ""
    )
    return protected
