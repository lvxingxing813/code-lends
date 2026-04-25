import tempfile
import unittest
from pathlib import Path

from codelens.parsers.java_parser import parse_java_file


class JavaParserTest(unittest.TestCase):
    def test_parse_spring_controller(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src" / "main" / "java" / "com" / "demo" / "AuthController.java"
            source.parent.mkdir(parents=True)
            source.write_text(
                """
package com.demo;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AuthController {
    @PostMapping("/api/login")
    public String login() {
        return "ok";
    }
}
""".strip(),
                encoding="utf-8",
            )

            result = parse_java_file(source, root)
            node_ids = {node.id for node in result.nodes}

            self.assertIn("module:src/main/java/com/demo/AuthController.java", node_ids)
            self.assertIn("api:POST /api/login", node_ids)
            self.assertTrue(any(edge.type == "EXPOSES" for edge in result.edges))


if __name__ == "__main__":
    unittest.main()

