from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "ja_structure_lint.py"
SPEC = importlib.util.spec_from_file_location("ja_structure_lint", SCRIPT)
assert SPEC and SPEC.loader
LINT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LINT
SPEC.loader.exec_module(LINT)


class JaStructureLintTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = LINT.load_config(ROOT / "config" / "default.json")
        cls.rules = LINT.load_rules(cls.config)

    def test_heading_jump_is_error(self) -> None:
        text = "# 根\n\n説明です。\n\n### 飛んだ見出し\n\n詳細です。\n"
        findings = LINT.lint_document(text, self.config, self.rules)
        self.assertIn("STRUCT001", {item.rule_id for item in findings})

    def test_protected_regions_do_not_trigger_rules(self) -> None:
        text = (
            "# 保護領域\n\n"
            "通常の説明です。\n\n"
            "```text\n必ず完全にすることができる\n### 見出しではない\n```\n\n"
            "> 必ず実行することができる\n\n"
            "[参照](https://example.com/必ず/することができる)\n"
        )
        findings = LINT.lint_document(text, self.config, self.rules)
        rule_ids = {item.rule_id for item in findings}
        self.assertNotIn("CLAIM001", rule_ids)
        self.assertNotIn("SURFACE001", rule_ids)
        self.assertNotIn("STRUCT001", rule_ids)

    def test_long_paragraph_is_reported(self) -> None:
        config = dict(self.config)
        config["max_paragraph_chars"] = 20
        text = "# 長い段落\n\nこれは一つの段落に多くの情報を詰め込んだため、分割候補として検出される説明です。\n"
        findings = LINT.lint_document(text, config, self.rules)
        self.assertIn("LOAD001", {item.rule_id for item in findings})

    def test_outline_keeps_heading_tree(self) -> None:
        text = (ROOT / "tests" / "fixtures" / "layered-good.md").read_text(encoding="utf-8")
        items = LINT.make_outline(text)
        self.assertEqual([1, 2, 3, 2], [item["depth"] for item in items])
        self.assertEqual("境界付き完全性", items[1]["title"])
        self.assertTrue(items[1]["topic"].startswith("完全性は"))

    def test_safe_fix_changes_only_unprotected_prose(self) -> None:
        text = "説明することができる。\n\n`実行することができる`\n"
        fixed, count = LINT.apply_safe_fixes(text, self.rules)
        self.assertEqual(1, count)
        self.assertIn("説明できる。", fixed)
        self.assertIn("`実行することができる`", fixed)

    def test_unclosed_fence_is_error(self) -> None:
        findings = LINT.lint_document("# 文書\n\n```text\n未完\n", self.config, self.rules)
        self.assertIn("MD002", {item.rule_id for item in findings})

    def test_shorter_fence_inside_code_does_not_close_block(self) -> None:
        text = "# 文書\n\n````text\n```\n必ず実行することができる\n````\n"
        findings = LINT.lint_document(text, self.config, self.rules)
        rule_ids = {item.rule_id for item in findings}
        self.assertNotIn("CLAIM001", rule_ids)
        self.assertNotIn("SURFACE001", rule_ids)

    def test_thematic_break_at_start_is_not_frontmatter(self) -> None:
        findings = LINT.lint_document("---\n\n# 文書\n\n説明です。\n", self.config, self.rules)
        self.assertNotIn("MD001", {item.rule_id for item in findings})

    def test_short_boundary_case_is_not_forced_into_deeper_layers(self) -> None:
        text = (ROOT / "tests" / "fixtures" / "short-boundary.md").read_text(encoding="utf-8")
        findings = LINT.lint_document(text, self.config, self.rules)
        self.assertEqual([], findings)


if __name__ == "__main__":
    unittest.main()
