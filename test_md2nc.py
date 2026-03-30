import unittest

import md2nc


class RenderMarkdownTests(unittest.TestCase):
    def test_nested_list_blockquote_and_block_formula(self) -> None:
        lines = [
            "- outer item",
            "  1. inner item",
            "     > quoted line",
            "     > $$",
            "     > x+y",
            "     > $$",
        ]

        rendered = md2nc.render_markdown(lines)

        self.assertIn("<ul>", rendered)
        self.assertIn("<ol>", rendered)
        self.assertIn("<blockquote>", rendered)
        self.assertIn("quoted line<br />", rendered)
        self.assertIn("<center><img", rendered)
        self.assertIn("tex=x%2By", rendered)

    def test_inline_markdown_variants(self) -> None:
        rendered = md2nc.render_inline(
            "plain *italic* **bold** ==mark== ~~gone~~ `code` $x$ [link](https://example.com) <span>tag</span>"
        )

        self.assertIn("<em>italic</em>", rendered)
        self.assertIn("<strong>bold</strong>", rendered)
        self.assertIn("<mark>mark</mark>", rendered)
        self.assertIn("<del>gone</del>", rendered)
        self.assertIn("<code>code</code>", rendered)
        self.assertIn('tex=x', rendered)
        self.assertIn('<a href="https://example.com">link</a>', rendered)
        self.assertIn("<span>tag</span>", rendered)

    def test_inline_delimiters_do_not_capture_plain_operators(self) -> None:
        rendered = md2nc.render_inline("3 * 4 * 5 and a == b == c")

        self.assertEqual("3 * 4 * 5 and a == b == c", rendered)

    def test_headings_and_fenced_code_blocks(self) -> None:
        lines = [
            "## 小标题",
            "",
            "```cpp",
            "int main() {",
            "    return 0;",
            "}",
            "```",
        ]

        rendered = md2nc.render_markdown(lines)

        self.assertIn("<h2>小标题</h2>", rendered)
        self.assertIn("<pre><code class=\"language-cpp\">", rendered)
        self.assertIn("int main() {", rendered)
        self.assertIn("    return 0;", rendered)

    def test_underscore_emphasis_variants(self) -> None:
        rendered = md2nc.render_inline("__bold__ and _italic_")

        self.assertIn("<strong>bold</strong>", rendered)
        self.assertIn("<em>italic</em>", rendered)


if __name__ == "__main__":
    unittest.main()
