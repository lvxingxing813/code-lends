import tempfile
import unittest
from pathlib import Path

from codelens.parsers.frontend_parser import parse_frontend_file


class FrontendParserTest(unittest.TestCase):
    def test_parse_next_page_and_api_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            component = root / "frontend" / "src" / "components" / "LoginForm.tsx"
            component.parent.mkdir(parents=True)
            component.write_text("export function LoginForm() { return null; }", encoding="utf-8")
            page = root / "frontend" / "src" / "app" / "login" / "page.tsx"
            page.parent.mkdir(parents=True)
            page.write_text(
                """
import { LoginForm } from "../../components/LoginForm";

export default function LoginPage() {
  return <LoginForm />;
}

async function submit() {
  await fetch("/api/login", { method: "POST" });
}
""".strip(),
                encoding="utf-8",
            )

            result = parse_frontend_file(page, root)
            node_ids = {node.id for node in result.nodes}

            self.assertIn("page:frontend/src/app/login/page.tsx", node_ids)
            self.assertIn("component:frontend/src/app/login/page.tsx:LoginPage", node_ids)
            self.assertIn("api:POST /api/login", node_ids)
            self.assertTrue(
                any(
                    edge.source == "page:frontend/src/app/login/page.tsx"
                    and edge.target == "component:frontend/src/components/LoginForm.tsx"
                    for edge in result.edges
                )
            )

    def test_parse_component_with_interaction_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            component = root / "frontend" / "src" / "components" / "LoginForm.tsx"
            component.parent.mkdir(parents=True)
            component.write_text(
                """
export function LoginForm() {
  return <button onClick={login}>登录</button>;
}
""".strip(),
                encoding="utf-8",
            )

            result = parse_frontend_file(component, root)

            self.assertTrue(any(node.type == "Component" and node.name == "LoginForm" for node in result.nodes))
            self.assertTrue(any(node.metadata.get("interaction") == "onClick" for node in result.nodes))
            self.assertTrue(any(node.type == "Feature" and node.name == "点击：登录" for node in result.nodes))


if __name__ == "__main__":
    unittest.main()
