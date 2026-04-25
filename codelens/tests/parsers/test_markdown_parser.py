import tempfile
import unittest
from pathlib import Path

from codelens.parsers.markdown_parser import parse_markdown_file


class MarkdownParserTest(unittest.TestCase):
    def test_parse_markdown_headings_as_features(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            doc = root / "docs" / "prd.md"
            doc.parent.mkdir()
            doc.write_text(
                """
# 用户登录

支持手机号验证码登录。

## 批量导入

支持 Excel 上传。
""".strip(),
                encoding="utf-8",
            )

            result = parse_markdown_file(doc, root)
            names = {node.name for node in result.nodes}

            self.assertIn("用户登录", names)
            self.assertIn("批量导入", names)
            self.assertTrue(any(edge.type == "MENTIONS" for edge in result.edges))


if __name__ == "__main__":
    unittest.main()

