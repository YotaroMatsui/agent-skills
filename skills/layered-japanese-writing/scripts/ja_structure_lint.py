#!/usr/bin/env python3
"""日本語Markdownの構造と表層規則を決定的に検査する。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "default.json"
SEVERITY_RANK = {"suggestion": 1, "warning": 2, "error": 3}
SENTENCE_END_RE = re.compile(r"[。！？!?]+")
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
FENCE_CLOSE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})[ \t]*$")
URL_RE = re.compile(r"(?:https?://|mailto:)[^\s)>]+")
INLINE_CODE_RE = re.compile(r"(?<!`)`[^`\n]+`(?!`)")
LINK_TARGET_RE = re.compile(r"(?<=\]\()[^)\n]+(?=\))")


class LintConfigurationError(ValueError):
    """設定または規則を読み込めない場合のエラー。"""


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    message: str
    line: int
    column: int
    excerpt: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["id"] = data.pop("rule_id")
        return data


@dataclass(frozen=True)
class Rule:
    rule_id: str
    severity: str
    pattern: re.Pattern[str]
    message: str
    replacement: str | None
    autofix: bool


@dataclass(frozen=True)
class Heading:
    depth: int
    title: str
    line: int
    start: int
    end: int
    parent_index: int | None


@dataclass(frozen=True)
class Paragraph:
    text: str
    line: int
    start: int
    end: int


def load_config(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LintConfigurationError(f"設定を読み込めません: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise LintConfigurationError(f"設定のルートはobjectである必要があります: {path}")
    data["_config_dir"] = str(path.resolve().parent)
    return data


def _regex_flags(value: str) -> int:
    flags = 0
    for char in value:
        if char == "i":
            flags |= re.IGNORECASE
        elif char == "m":
            flags |= re.MULTILINE
        elif char == "s":
            flags |= re.DOTALL
        else:
            raise LintConfigurationError(f"未対応の正規表現flagです: {char}")
    return flags


def load_rules(config: dict[str, Any]) -> list[Rule]:
    config_dir = Path(config["_config_dir"])
    rules: list[Rule] = []
    seen_ids: set[str] = set()
    for configured_path in config.get("rule_files", []):
        rule_path = (config_dir / configured_path).resolve()
        try:
            lines = rule_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise LintConfigurationError(f"規則を読み込めません: {rule_path}: {exc}") from exc
        for line_number, raw_line in enumerate(lines, start=1):
            if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                continue
            try:
                item = json.loads(raw_line)
                rule_id = str(item["id"])
                severity = str(item["severity"])
                pattern = re.compile(str(item["pattern"]), _regex_flags(str(item.get("flags", ""))))
                message = str(item["message"])
            except (KeyError, TypeError, ValueError, re.error, json.JSONDecodeError) as exc:
                raise LintConfigurationError(
                    f"規則が不正です: {rule_path}:{line_number}: {exc}"
                ) from exc
            if severity not in SEVERITY_RANK:
                raise LintConfigurationError(
                    f"severityが不正です: {rule_path}:{line_number}: {severity}"
                )
            if rule_id in seen_ids:
                raise LintConfigurationError(f"規則IDが重複しています: {rule_id}")
            seen_ids.add(rule_id)
            replacement = item.get("replacement")
            autofix = bool(item.get("autofix", False))
            if autofix and replacement is None:
                raise LintConfigurationError(f"autofix規則にreplacementがありません: {rule_id}")
            rules.append(
                Rule(
                    rule_id=rule_id,
                    severity=severity,
                    pattern=pattern,
                    message=message,
                    replacement=str(replacement) if replacement is not None else None,
                    autofix=autofix,
                )
            )
    return rules


def _mask_range(chars: list[str], start: int, end: int) -> None:
    for index in range(start, end):
        if chars[index] != "\n":
            chars[index] = " "


def mask_protected_regions(text: str) -> tuple[str, list[Finding]]:
    """コード、URL、引用などを同じ長さの空白へ置き換える。"""

    chars = list(text)
    findings: list[Finding] = []
    lines = text.splitlines(keepends=True)
    offset = 0
    fence_token: str | None = None
    fence_line = 0
    frontmatter_probe = lines[1:50]
    in_frontmatter = bool(
        lines
        and lines[0].strip() == "---"
        and any(re.match(r"^[A-Za-z0-9_-]+[ \t]*:", line) for line in frontmatter_probe)
    )
    frontmatter_closed = not in_frontmatter

    for line_number, line in enumerate(lines, start=1):
        stripped = line.rstrip("\r\n")
        line_end = offset + len(line)

        if in_frontmatter:
            _mask_range(chars, offset, line_end)
            if line_number > 1 and stripped.strip() == "---":
                in_frontmatter = False
                frontmatter_closed = True
            offset = line_end
            continue

        fence_match = FENCE_RE.match(stripped)
        if fence_token is not None:
            _mask_range(chars, offset, line_end)
            fence_close = FENCE_CLOSE_RE.match(stripped)
            if (
                fence_close
                and fence_close.group(1)[0] == fence_token[0]
                and len(fence_close.group(1)) >= len(fence_token)
            ):
                fence_token = None
            offset = line_end
            continue
        if fence_match:
            fence_token = fence_match.group(1)
            fence_line = line_number
            _mask_range(chars, offset, line_end)
            offset = line_end
            continue

        if re.match(r"^[ \t]*(?:>| {4}|\t)", stripped):
            _mask_range(chars, offset, line_end)
        elif stripped.count("|") >= 2 and re.match(r"^[ \t]*\|?.*\|", stripped):
            _mask_range(chars, offset, line_end)
        offset = line_end

    if not frontmatter_closed:
        findings.append(
            Finding("MD001", "error", "frontmatterが閉じていません。", 1, 1, "---")
        )
    if fence_token is not None:
        findings.append(
            Finding("MD002", "error", "コードフェンスが閉じていません。", fence_line, 1, fence_token)
        )

    masked = "".join(chars)
    chars = list(masked)
    for pattern in (INLINE_CODE_RE, LINK_TARGET_RE, URL_RE):
        for match in pattern.finditer(masked):
            _mask_range(chars, match.start(), match.end())
    return "".join(chars), findings


def _line_column(text: str, position: int) -> tuple[int, int]:
    line = text.count("\n", 0, position) + 1
    previous_newline = text.rfind("\n", 0, position)
    column = position - previous_newline
    return line, column


def _line_excerpt(text: str, line: int, limit: int = 120) -> str:
    lines = text.splitlines()
    if 1 <= line <= len(lines):
        return lines[line - 1].strip()[:limit]
    return ""


def parse_headings(text: str, masked: str) -> list[Heading]:
    headings: list[Heading] = []
    stack: list[int] = []
    for match in HEADING_RE.finditer(masked):
        depth = len(match.group(1))
        line, _ = _line_column(text, match.start())
        original_line = text.splitlines()[line - 1]
        title_match = re.match(r"^#{1,6}[ \t]+(.+?)[ \t]*$", original_line)
        title = title_match.group(1).strip() if title_match else match.group(2).strip()
        while stack and headings[stack[-1]].depth >= depth:
            stack.pop()
        parent_index = stack[-1] if stack else None
        headings.append(Heading(depth, title, line, match.start(), match.end(), parent_index))
        stack.append(len(headings) - 1)
    return headings


def _strip_markdown_prefix(line: str) -> str:
    line = re.sub(r"^[ \t]*(?:[-+*]|\d+[.)])[ \t]+", "", line)
    line = re.sub(r"^[ \t]*#{1,6}[ \t]+", "", line)
    return line.strip()


def extract_paragraphs(text: str, masked: str, start: int = 0, end: int | None = None) -> list[Paragraph]:
    end = len(text) if end is None else end
    segment_text = text[start:end]
    segment_masked = masked[start:end]
    paragraphs: list[Paragraph] = []
    current: list[str] = []
    current_start: int | None = None
    cursor = start

    def flush(paragraph_end: int) -> None:
        nonlocal current, current_start
        if current and current_start is not None:
            value = " ".join(part for part in current if part).strip()
            if value:
                line, _ = _line_column(text, current_start)
                paragraphs.append(Paragraph(value, line, current_start, paragraph_end))
        current = []
        current_start = None

    for raw_text, raw_masked in zip(
        segment_text.splitlines(keepends=True), segment_masked.splitlines(keepends=True)
    ):
        prose = _strip_markdown_prefix(raw_masked.rstrip("\r\n"))
        is_heading = bool(re.match(r"^[ \t]*#{1,6}[ \t]+", raw_masked))
        is_rule = bool(re.match(r"^[ \t]*(?:---+|___+|\*\*\*+)[ \t]*$", raw_masked))
        is_list_item = bool(re.match(r"^[ \t]*(?:[-+*]|\d+[.)])[ \t]+", raw_masked))
        if not prose or is_heading or is_rule:
            flush(cursor)
        else:
            if is_list_item:
                flush(cursor)
            if current_start is None:
                current_start = cursor
            current.append(prose)
            if is_list_item:
                flush(cursor + len(raw_text))
        cursor += len(raw_text)
    flush(end)
    return paragraphs


def _visible_char_count(value: str) -> int:
    return len(re.sub(r"\s+", "", value))


def _first_sentence(value: str, limit: int = 140) -> str:
    match = SENTENCE_END_RE.search(value)
    sentence = value[: match.end()] if match else value
    sentence = re.sub(r"\s+", " ", sentence).strip()
    return sentence if len(sentence) <= limit else sentence[: limit - 1] + "…"


def make_outline(text: str) -> list[dict[str, Any]]:
    masked, _ = mask_protected_regions(text)
    headings = parse_headings(text, masked)
    items: list[dict[str, Any]] = []
    for index, heading in enumerate(headings):
        direct_end = headings[index + 1].start if index + 1 < len(headings) else len(text)
        paragraphs = extract_paragraphs(text, masked, heading.end, direct_end)
        topic = _first_sentence(paragraphs[0].text) if paragraphs else ""
        items.append(
            {
                "depth": heading.depth,
                "title": heading.title,
                "line": heading.line,
                "topic": topic,
            }
        )
    return items


def _structural_findings(
    text: str, masked: str, config: dict[str, Any], headings: Sequence[Heading]
) -> list[Finding]:
    findings: list[Finding] = []
    jump_limit = int(config.get("max_heading_depth_jump", 1))
    max_depth = int(config.get("max_heading_depth", 6))
    sibling_titles: set[tuple[int | None, str]] = set()

    for index, heading in enumerate(headings):
        if index and heading.depth - headings[index - 1].depth > jump_limit:
            findings.append(
                Finding(
                    "STRUCT001",
                    "error",
                    f"見出し階層が{headings[index - 1].depth}から{heading.depth}へ飛んでいます。",
                    heading.line,
                    1,
                    _line_excerpt(text, heading.line),
                )
            )
        if heading.depth > max_depth:
            findings.append(
                Finding(
                    "STRUCT002",
                    "warning",
                    f"見出し深さ{heading.depth}は参考上限{max_depth}を超えています。",
                    heading.line,
                    1,
                    _line_excerpt(text, heading.line),
                )
            )
        sibling_key = (heading.parent_index, heading.title)
        if sibling_key in sibling_titles:
            findings.append(
                Finding(
                    "STRUCT003",
                    "warning",
                    "同じ親の直下に同名の見出しがあります。役割を区別できるか確認してください。",
                    heading.line,
                    1,
                    _line_excerpt(text, heading.line),
                )
            )
        sibling_titles.add(sibling_key)

    paragraphs = extract_paragraphs(text, masked)
    paragraph_char_limit = int(config.get("max_paragraph_chars", 0))
    paragraph_sentence_limit = int(config.get("max_paragraph_sentences", 0))
    for paragraph in paragraphs:
        char_count = _visible_char_count(paragraph.text)
        sentence_count = len(SENTENCE_END_RE.findall(paragraph.text))
        if paragraph_char_limit and char_count > paragraph_char_limit:
            findings.append(
                Finding(
                    "LOAD001",
                    "warning",
                    f"段落が{char_count}文字あり、参考上限{paragraph_char_limit}を超えています。主題を分けられるか確認してください。",
                    paragraph.line,
                    1,
                    _line_excerpt(text, paragraph.line),
                )
            )
        if paragraph_sentence_limit and sentence_count > paragraph_sentence_limit:
            findings.append(
                Finding(
                    "LOAD002",
                    "warning",
                    f"段落に{sentence_count}文あり、参考上限{paragraph_sentence_limit}を超えています。",
                    paragraph.line,
                    1,
                    _line_excerpt(text, paragraph.line),
                )
            )

    section_char_limit = int(config.get("max_section_chars", 0))
    section_paragraph_limit = int(config.get("max_section_paragraphs", 0))
    for index, heading in enumerate(headings):
        direct_end = headings[index + 1].start if index + 1 < len(headings) else len(text)
        direct_paragraphs = extract_paragraphs(text, masked, heading.end, direct_end)
        char_count = sum(_visible_char_count(p.text) for p in direct_paragraphs)
        if section_char_limit and char_count > section_char_limit:
            findings.append(
                Finding(
                    "LOAD003",
                    "warning",
                    f"節の直下本文が{char_count}文字あり、参考上限{section_char_limit}を超えています。下位層へ分けられるか確認してください。",
                    heading.line,
                    1,
                    _line_excerpt(text, heading.line),
                )
            )
        if section_paragraph_limit and len(direct_paragraphs) > section_paragraph_limit:
            findings.append(
                Finding(
                    "LOAD004",
                    "suggestion",
                    f"節の直下に{len(direct_paragraphs)}段落あり、参考上限{section_paragraph_limit}を超えています。",
                    heading.line,
                    1,
                    _line_excerpt(text, heading.line),
                )
            )

    if bool(config.get("sentence_per_line", False)):
        for line_number, line in enumerate(masked.splitlines(), start=1):
            if len(SENTENCE_END_RE.findall(line)) > 1:
                findings.append(
                    Finding(
                        "SOURCE001",
                        "suggestion",
                        "一つのソース行に複数の文があります。差分可読性のため一文一行を検討してください。",
                        line_number,
                        1,
                        _line_excerpt(text, line_number),
                    )
                )

    if bool(config.get("check_style_consistency", False)):
        polite = list(re.finditer(r"(?:です|ます|でした|ません)[。！？!?]", masked))
        plain = list(re.finditer(r"(?:である|だ)[。！？!?]", masked))
        total = len(polite) + len(plain)
        minimum = int(config.get("style_min_sentences", 8))
        minor_ratio = float(config.get("style_minor_ratio", 0.2))
        if total >= minimum and polite and plain and min(len(polite), len(plain)) / total >= minor_ratio:
            position = min(polite[0].start(), plain[0].start())
            line, column = _line_column(text, position)
            findings.append(
                Finding(
                    "STYLE001",
                    "warning",
                    "敬体と常体が混在しています。意図的な切替か確認してください。",
                    line,
                    column,
                    _line_excerpt(text, line),
                )
            )
    return findings


def _rule_findings(text: str, masked: str, rules: Iterable[Rule]) -> list[Finding]:
    findings: list[Finding] = []
    for rule in rules:
        for match in rule.pattern.finditer(masked):
            line, column = _line_column(text, match.start())
            findings.append(
                Finding(
                    rule.rule_id,
                    rule.severity,
                    rule.message,
                    line,
                    column,
                    _line_excerpt(text, line),
                )
            )
    return findings


def lint_document(text: str, config: dict[str, Any], rules: Sequence[Rule]) -> list[Finding]:
    masked, markdown_findings = mask_protected_regions(text)
    headings = parse_headings(text, masked)
    findings = markdown_findings
    findings.extend(_structural_findings(text, masked, config, headings))
    findings.extend(_rule_findings(text, masked, rules))
    return sorted(findings, key=lambda item: (item.line, item.column, -SEVERITY_RANK[item.severity], item.rule_id))


def apply_safe_fixes(text: str, rules: Sequence[Rule]) -> tuple[str, int]:
    masked, markdown_findings = mask_protected_regions(text)
    if any(item.severity == "error" for item in markdown_findings):
        raise LintConfigurationError("Markdown構造エラーがあるためautofixを適用できません。")
    replacements: list[tuple[int, int, str]] = []
    for rule in rules:
        if not rule.autofix or rule.replacement is None:
            continue
        for match in rule.pattern.finditer(masked):
            replacements.append((match.start(), match.end(), match.expand(rule.replacement)))
    accepted: list[tuple[int, int, str]] = []
    for candidate in sorted(replacements, key=lambda item: (item[0], -(item[1] - item[0]))):
        if accepted and candidate[0] < accepted[-1][1]:
            continue
        accepted.append(candidate)
    fixed = text
    for start, end, replacement in reversed(accepted):
        fixed = fixed[:start] + replacement + fixed[end:]
    return fixed, len(accepted)


def _read_document(path_value: str) -> tuple[str, str]:
    if path_value == "-":
        return sys.stdin.read(), "<stdin>"
    path = Path(path_value)
    try:
        return path.read_text(encoding="utf-8"), str(path)
    except OSError as exc:
        raise LintConfigurationError(f"文書を読み込めません: {path}: {exc}") from exc


def _print_findings(path: str, findings: Sequence[Finding], output_format: str) -> None:
    counts = {severity: sum(item.severity == severity for item in findings) for severity in SEVERITY_RANK}
    if output_format == "json":
        print(
            json.dumps(
                {"path": path, "findings": [item.to_dict() for item in findings], "summary": counts},
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    for item in findings:
        print(f"{path}:{item.line}:{item.column}: {item.severity} {item.rule_id} {item.message}")
    print(
        f"{path}: error={counts['error']} warning={counts['warning']} suggestion={counts['suggestion']}"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="JSON設定ファイル")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="文書を検査する")
    check.add_argument("path", help="入力Markdown。-で標準入力")
    check.add_argument("--format", choices=("text", "json"), default="text")
    check.add_argument("--fail-on", choices=("error", "warning", "suggestion", "none"), default="error")

    outline = subparsers.add_parser("outline", help="見出しと主題候補を抽出する")
    outline.add_argument("path", help="入力Markdown。-で標準入力")
    outline.add_argument("--format", choices=("text", "json"), default="text")

    fix = subparsers.add_parser("fix", help="安全指定された規則を別ファイルへ適用する")
    fix.add_argument("path", help="入力Markdown")
    fix.add_argument("--output", type=Path, required=True, help="出力先。入力とは別のパスが必要")
    fix.add_argument("--force", action="store_true", help="既存の出力先を上書きする")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        rules = load_rules(config)
        text, source_name = _read_document(args.path)
        if args.command == "check":
            findings = lint_document(text, config, rules)
            _print_findings(source_name, findings, args.format)
            if args.fail_on == "none":
                return 0
            threshold = SEVERITY_RANK[args.fail_on]
            return 1 if any(SEVERITY_RANK[item.severity] >= threshold for item in findings) else 0
        if args.command == "outline":
            items = make_outline(text)
            if args.format == "json":
                print(json.dumps({"path": source_name, "items": items}, ensure_ascii=False, indent=2))
            else:
                for item in items:
                    indent = "  " * (item["depth"] - 1)
                    topic = f" — {item['topic']}" if item["topic"] else ""
                    print(f"{indent}- {item['title']} (L{item['line']}){topic}")
            return 0
        if args.command == "fix":
            input_path = Path(args.path).resolve()
            output_path = args.output.resolve()
            if input_path == output_path:
                raise LintConfigurationError("入力と同じパスへは出力できません。")
            if output_path.exists() and not args.force:
                raise LintConfigurationError("出力先が既に存在します。--forceなしでは上書きしません。")
            fixed, count = apply_safe_fixes(text, rules)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(fixed, encoding="utf-8")
            print(f"{output_path}: {count}件のautofixを適用しました。")
            return 0
    except LintConfigurationError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
