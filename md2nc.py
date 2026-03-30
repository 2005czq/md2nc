#!/usr/bin/env python3
"""Convert a markdown problem statement into NowCoder-style HTML snippets."""

from __future__ import annotations

import argparse
import html
import re
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote


LIST_ITEM_RE = re.compile(r"^([ \t]*)([-+*]|\d+\.)\s+(.*)$")
BLOCKQUOTE_RE = re.compile(r"^[ \t]*>\s?(.*)$")
SECTION_KEYS = ("background", "description", "input", "output", "notation")
VOID_HTML_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


def normalize_heading(title: str) -> Optional[str]:
    normalized = title.strip().replace(" ", "")
    if "题目背景" in normalized:
        return "background"
    if "题目描述" in normalized:
        return "description"
    if "输入格式" in normalized:
        return "input"
    if "输出格式" in normalized:
        return "output"
    if "说明" in normalized or "提示" in normalized:
        return "notation"
    if "测试样例" in normalized or "样例" in normalized:
        return "sample"
    return None


def split_sections(markdown_text: str) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {key: [] for key in SECTION_KEYS}
    current: Optional[str] = None

    for raw_line in markdown_text.splitlines():
        heading_match = re.match(r"^#\s+(.*)$", raw_line)
        if heading_match:
            current = normalize_heading(heading_match.group(1))
            continue
        if current in sections:
            sections[current].append(raw_line)

    return sections


def indent_width(indent: str) -> int:
    width = 0
    for ch in indent:
        width += 4 if ch == "\t" else 1
    return width


def escape_formula_alt(formula: str, is_block: bool) -> str:
    alt_text = formula
    if is_block:
        alt_text = alt_text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br />")
    return html.escape(alt_text, quote=True)


def formula_to_img(formula: str, is_block: bool) -> str:
    encoded = quote(formula, safe="()")
    alt = escape_formula_alt(formula, is_block=is_block)
    return f'<img src="https://www.nowcoder.com/equation?tex={encoded}" alt="{alt}" />'


def is_escaped(text: str, idx: int) -> bool:
    slash_count = 0
    cursor = idx - 1
    while cursor >= 0 and text[cursor] == "\\":
        slash_count += 1
        cursor -= 1
    return slash_count % 2 == 1


def find_closing(text: str, start: int, delimiter: str) -> int:
    idx = start
    while True:
        idx = text.find(delimiter, idx)
        if idx == -1:
            return -1
        if not is_escaped(text, idx):
            return idx
        idx += len(delimiter)


def find_html_tag_end(text: str, start: int) -> Optional[int]:
    if start >= len(text) or text[start] != "<":
        return None

    if text.startswith("<!--", start):
        end = text.find("-->", start + 4)
        return end + 3 if end != -1 else None

    i = start + 1
    if i >= len(text):
        return None

    if text[i] == "/":
        i += 1
        if i >= len(text) or not text[i].isalpha():
            return None
    elif text[i] in "!?":
        i += 1
    elif not text[i].isalpha():
        return None

    if text[start + 1] not in "!?":
        while i < len(text) and (text[i].isalnum() or text[i] in "-_:"):
            i += 1

    quote_char: Optional[str] = None
    while i < len(text):
        ch = text[i]
        if quote_char is not None:
            if ch == quote_char:
                quote_char = None
        else:
            if ch in "\"'":
                quote_char = ch
            elif ch == ">":
                return i + 1
            elif ch == "<":
                return None
        i += 1

    return None


def is_html_only_line(text: str) -> bool:
    i = 0
    saw_tag = False

    while i < len(text):
        if text[i].isspace():
            i += 1
            continue

        end = find_html_tag_end(text, i)
        if end is None:
            return False

        saw_tag = True
        i = end

    return saw_tag


def classify_html_tag(tag: str) -> Tuple[str, Optional[str]]:
    if tag.startswith("<!--"):
        return "comment", None

    if len(tag) < 3:
        return "invalid", None

    i = 1
    if tag[i] == "/":
        i += 1
        start = i
        while i < len(tag) and (tag[i].isalnum() or tag[i] in "-_:"):
            i += 1
        return "close", tag[start:i].lower() or None

    if tag[i] in "!?":
        return "special", None

    start = i
    while i < len(tag) and (tag[i].isalnum() or tag[i] in "-_:"):
        i += 1

    name = tag[start:i].lower()
    if not name:
        return "invalid", None

    if tag[:-1].rstrip().endswith("/") or name in VOID_HTML_TAGS:
        return "self", name

    return "open", name


def is_raw_html_line(text: str) -> bool:
    if is_html_only_line(text):
        return True

    if not text.startswith("<"):
        return False

    stack: List[str] = []
    saw_tag = False
    i = 0

    while i < len(text):
        if text[i] != "<":
            if not stack:
                return False

            next_tag = text.find("<", i)
            if next_tag == -1:
                i = len(text)
            else:
                i = next_tag
            continue

        end = find_html_tag_end(text, i)
        if end is None:
            return False

        saw_tag = True
        tag_type, tag_name = classify_html_tag(text[i:end])
        if tag_type == "open":
            stack.append(tag_name or "")
        elif tag_type == "close":
            if not stack or stack[-1] != tag_name:
                return False
            stack.pop()
        elif tag_type == "invalid":
            return False

        i = end

    return saw_tag and not stack


def render_inline(text: str) -> str:
    parts: List[str] = []
    plain: List[str] = []
    i = 0

    def flush_plain() -> None:
        if plain:
            parts.append(html.escape("".join(plain), quote=False))
            plain.clear()

    while i < len(text):
        if text.startswith("`", i):
            end = find_closing(text, i + 1, "`")
            if end != -1:
                flush_plain()
                code = text[i + 1 : end]
                parts.append(f"<code>{html.escape(code, quote=False)}</code>")
                i = end + 1
                continue

        if text.startswith("**", i):
            end = find_closing(text, i + 2, "**")
            if end != -1:
                flush_plain()
                inner = render_inline(text[i + 2 : end])
                parts.append(f"<strong>{inner}</strong>")
                i = end + 2
                continue

        if text[i] == "$" and not text.startswith("$$", i):
            end = find_closing(text, i + 1, "$")
            if end != -1:
                flush_plain()
                formula = text[i + 1 : end]
                parts.append(formula_to_img(formula, is_block=False))
                i = end + 1
                continue

        if text[i] == "<":
            end = find_html_tag_end(text, i)
            if end is not None:
                flush_plain()
                parts.append(text[i:end])
                i = end
                continue

        plain.append(text[i])
        i += 1

    flush_plain()
    return "".join(parts)


def parse_block_formula(lines: List[str], start: int) -> Tuple[str, int]:
    line = lines[start].strip()
    remainder = line[2:]

    if "$$" in remainder:
        end_pos = remainder.find("$$")
        formula = remainder[:end_pos]
        return formula_to_img(formula, is_block=True), start + 1

    formula_lines: List[str] = []
    if remainder:
        formula_lines.append(remainder)

    i = start + 1
    while i < len(lines):
        current = lines[i]
        close_pos = current.find("$$")
        if close_pos != -1:
            before_close = current[:close_pos]
            if before_close:
                formula_lines.append(before_close)
            i += 1
            break
        formula_lines.append(current)
        i += 1

    formula = textwrap.dedent("\n".join(formula_lines)).strip("\n")
    return formula_to_img(formula, is_block=True), i


def parse_list(lines: List[str], start: int, base_indent: int, depth: int) -> Tuple[List[str], int]:
    first = LIST_ITEM_RE.match(lines[start])
    if first is None:
        return [], start

    is_ordered = first.group(2).endswith(".")
    tag = "ol" if is_ordered else "ul"

    depth_indent = "\t" * depth
    out: List[str] = [f"{depth_indent}<{tag}>"]
    i = start

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        match = LIST_ITEM_RE.match(line)
        if match is None:
            break

        indent = indent_width(match.group(1))
        marker = match.group(2)
        marker_ordered = marker.endswith(".")

        if indent < base_indent:
            break
        if indent > base_indent:
            break
        if marker_ordered != is_ordered:
            break

        li_indent = "\t" * (depth + 1)
        content_indent = "\t" * (depth + 2)
        out.append(f"{li_indent}<li>")

        item_content = match.group(3).strip()
        if item_content:
            out.append(f"{content_indent}{render_inline(item_content)}<br />")

        i += 1
        while i < len(lines):
            next_line = lines[i]
            if not next_line.strip():
                i += 1
                continue

            nested_match = LIST_ITEM_RE.match(next_line)
            if nested_match:
                nested_indent = indent_width(nested_match.group(1))
                if nested_indent == base_indent:
                    break
                if nested_indent < base_indent:
                    break
                nested_block, i = parse_list(lines, i, nested_indent, depth + 2)
                out.extend(nested_block)
                continue

            continuation_match = re.match(r"^([ \t]*)", next_line)
            continuation_indent = indent_width(continuation_match.group(1)) if continuation_match else 0
            if continuation_indent <= base_indent:
                break

            stripped_next = next_line.strip()
            if stripped_next.startswith("$$"):
                formula_img, i = parse_block_formula(lines, i)
                out.append(f"{content_indent}<center>{formula_img}</center>")
                continue

            out.append(f"{content_indent}{render_inline(stripped_next)}<br />")
            i += 1

        out.append(f"{li_indent}</li>")

    out.append(f"{depth_indent}</{tag}>")
    return out, i


def trim_blank_edges(lines: List[str]) -> List[str]:
    start = 0
    end = len(lines)
    while start < end and lines[start] == "":
        start += 1
    while end > start and lines[end - 1] == "":
        end -= 1
    return lines[start:end]


def indent_html_block(block: str, depth: int = 1) -> List[str]:
    prefix = "\t" * depth
    indented: List[str] = []
    for line in block.splitlines():
        indented.append(f"{prefix}{line}" if line else "")
    return indented


def strip_blockquote_marker(line: str) -> Optional[str]:
    match = BLOCKQUOTE_RE.match(line)
    if match is None:
        return None
    return match.group(1)


def parse_blockquote(lines: List[str], start: int) -> Tuple[List[str], int]:
    quote_lines: List[str] = []
    i = start

    while i < len(lines):
        quote_line = strip_blockquote_marker(lines[i])
        if quote_line is None:
            break
        quote_lines.append(quote_line)
        i += 1

    inner_html = render_markdown(quote_lines)
    out = ["<blockquote>"]
    out.extend(indent_html_block(inner_html))
    out.append("</blockquote>")
    return out, i


def render_markdown(lines: List[str]) -> str:
    rendered: List[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            rendered.append("")
            i += 1
            continue

        if stripped.startswith("$$"):
            formula_img, i = parse_block_formula(lines, i)
            rendered.append(f"<center>{formula_img}</center>")
            continue

        if strip_blockquote_marker(line) is not None:
            block, i = parse_blockquote(lines, i)
            rendered.extend(block)
            continue

        list_match = LIST_ITEM_RE.match(line)
        if list_match:
            base_indent = indent_width(list_match.group(1))
            block, i = parse_list(lines, i, base_indent, depth=0)
            rendered.extend(block)
            continue

        if is_raw_html_line(stripped):
            rendered.append(stripped)
        else:
            rendered.append(f"{render_inline(stripped)}<br />")
        i += 1

    return "\n".join(trim_blank_edges(rendered))


def compose_description(background_lines: List[str], description_lines: List[str]) -> str:
    chunks: List[str] = []
    background_html = render_markdown(background_lines)
    description_html = render_markdown(description_lines)

    if background_html:
        chunks.append("<blockquote>")
        chunks.extend(indent_html_block(background_html))
        chunks.append("</blockquote>")

    if description_html:
        if chunks:
            chunks.append("")
        chunks.extend(description_html.splitlines())

    return "\n".join(chunks)


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def convert(input_path: Path, description_path: Path, input_html_path: Path, output_html_path: Path, notation_path: Path) -> None:
    markdown_text = input_path.read_text(encoding="utf-8")
    sections = split_sections(markdown_text)

    description_html = compose_description(sections["background"], sections["description"])
    input_html = render_markdown(sections["input"])
    output_html = render_markdown(sections["output"])
    notation_html = render_markdown(sections["notation"])

    write_text(description_path, description_html)
    write_text(input_html_path, input_html)
    write_text(output_html_path, output_html)
    write_text(notation_path, notation_html)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert markdown problem statement to NowCoder html snippets")
    parser.add_argument("input", nargs="?", default="problem.md", help="Path to markdown input file")
    parser.add_argument("--description", default="description.html", help="Output path for description html")
    parser.add_argument("--input-html", default="input.html", help="Output path for input format html")
    parser.add_argument("--output-html", default="output.html", help="Output path for output format html")
    parser.add_argument("--notation", default="notation.html", help="Output path for notation html")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    base_dir = input_path.parent if input_path.parent != Path("") else Path(".")

    description_path = (base_dir / args.description).resolve()
    input_html_path = (base_dir / args.input_html).resolve()
    output_html_path = (base_dir / args.output_html).resolve()
    notation_path = (base_dir / args.notation).resolve()

    convert(
        input_path=input_path.resolve(),
        description_path=description_path,
        input_html_path=input_html_path,
        output_html_path=output_html_path,
        notation_path=notation_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
