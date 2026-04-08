#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS = [
    ROOT / "data" / "world_politics" / "analysis" / "sentiment_latest.json",
    ROOT / "data" / "world_politics" / "analysis" / "view_model_latest.json",
    ROOT / "analysis" / "prediction" / "prediction_latest.json",
]
DEFAULT_REQUIRED_LANGS = ["en"]
DEFAULT_OPTIONAL_LANGS = ["ja", "th"]


@dataclass
class Issue:
    level: str  # ERROR | WARN
    file: str
    path: str
    message: str


@dataclass
class FileReport:
    path: Path
    errors: List[Issue]
    warnings: List[Issue]
    meta: Dict[str, Any]


class Validator:
    def __init__(
        self,
        *,
        required_langs: Sequence[str],
        optional_langs: Sequence[str],
        enforce_declared_langs: bool,
        check_empty_strings: bool,
    ) -> None:
        self.required_langs = list(dict.fromkeys(required_langs))
        self.optional_langs = list(dict.fromkeys(optional_langs))
        self.enforce_declared_langs = enforce_declared_langs
        self.check_empty_strings = check_empty_strings

    def validate_file(self, path: Path) -> FileReport:
        errors: List[Issue] = []
        warnings: List[Issue] = []
        data = self._load_json(path, errors)
        meta: Dict[str, Any] = {
            "lang_default": None,
            "languages": [],
            "i18n_nodes": 0,
        }
        if data is None:
            return FileReport(path=path, errors=errors, warnings=warnings, meta=meta)
        if not isinstance(data, dict):
            errors.append(Issue("ERROR", str(path), "$", "root must be a JSON object"))
            return FileReport(path=path, errors=errors, warnings=warnings, meta=meta)

        lang_default = data.get("lang_default")
        languages = data.get("languages")
        meta["lang_default"] = lang_default
        meta["languages"] = languages if isinstance(languages, list) else []

        if not isinstance(lang_default, str) or not lang_default.strip():
            errors.append(Issue("ERROR", str(path), "$.lang_default", "missing or invalid lang_default"))
        if not isinstance(languages, list) or not all(isinstance(x, str) and x.strip() for x in languages):
            errors.append(Issue("ERROR", str(path), "$.languages", "missing or invalid languages list"))
            declared_langs: List[str] = []
        else:
            declared_langs = [str(x).strip() for x in languages]
            if "en" not in declared_langs:
                errors.append(Issue("ERROR", str(path), "$.languages", "languages must include 'en'"))
            if isinstance(lang_default, str) and lang_default.strip() and lang_default not in declared_langs:
                errors.append(Issue("ERROR", str(path), "$.lang_default", "lang_default must exist in languages"))

        for issue in self._walk(data, "$", data, declared_langs, parent_key=None):
            if issue.level == "ERROR":
                errors.append(issue)
            else:
                warnings.append(issue)

        meta["i18n_nodes"] = self._count_i18n_nodes(data)
        return FileReport(path=path, errors=errors, warnings=warnings, meta=meta)

    def _load_json(self, path: Path, errors: List[Issue]) -> Any | None:
        if not path.exists():
            errors.append(Issue("ERROR", str(path), "$", "file does not exist"))
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(Issue("ERROR", str(path), "$", f"failed to parse JSON: {exc}"))
            return None

    def _count_i18n_nodes(self, node: Any) -> int:
        if isinstance(node, dict):
            count = sum(1 for k in node if isinstance(k, str) and k.endswith("_i18n"))
            for value in node.values():
                count += self._count_i18n_nodes(value)
            return count
        if isinstance(node, list):
            return sum(self._count_i18n_nodes(x) for x in node)
        return 0

    def _walk(
        self,
        node: Any,
        path: str,
        root_doc: dict,
        declared_langs: Sequence[str],
        parent_key: str | None,
    ) -> Iterable[Issue]:
        if isinstance(node, dict):
            for key, value in node.items():
                child_path = f"{path}.{key}" if path != "$" else f"$.{key}"
                if isinstance(key, str) and key.endswith("_i18n"):
                    yield from self._validate_i18n_field(
                        key=key,
                        value=value,
                        path=child_path,
                        container=node,
                        declared_langs=declared_langs,
                    )
                yield from self._walk(value, child_path, root_doc, declared_langs, parent_key=key if isinstance(key, str) else None)
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                yield from self._walk(item, f"{path}[{idx}]", root_doc, declared_langs, parent_key=parent_key)

    def _validate_i18n_field(
        self,
        *,
        key: str,
        value: Any,
        path: str,
        container: Dict[str, Any],
        declared_langs: Sequence[str],
    ) -> Iterable[Issue]:
        if not isinstance(value, dict):
            yield Issue("ERROR", "", path, "*_i18n field must be an object")
            return

        if self._is_lang_map(value):
            yield from self._validate_lang_map(
                key=key,
                lang_map=value,
                path=path,
                container=container,
                declared_langs=declared_langs,
            )
            return

        if not value:
            yield Issue("WARN", "", path, "structured *_i18n object is empty")

    def _is_lang_map(self, value: Dict[str, Any]) -> bool:
        keys = set(value.keys())
        if not keys:
            return False
        lang_like = {"en", "ja", "th"}
        return bool(keys & lang_like)

    def _validate_lang_map(
        self,
        *,
        key: str,
        lang_map: Dict[str, Any],
        path: str,
        container: Dict[str, Any],
        declared_langs: Sequence[str],
    ) -> Iterable[Issue]:
        if "en" not in lang_map:
            yield Issue("ERROR", "", path, "missing required language 'en'")

        for lang in self.required_langs:
            if lang not in lang_map:
                yield Issue("ERROR", "", path, f"missing required language '{lang}'")

        langs_to_enforce = list(declared_langs) if self.enforce_declared_langs and declared_langs else []
        for lang in langs_to_enforce:
            if lang not in lang_map:
                yield Issue("WARN", "", path, f"missing declared language '{lang}'")

        for lang in self.optional_langs:
            if declared_langs and lang in declared_langs and lang not in lang_map:
                yield Issue("WARN", "", path, f"missing optional language '{lang}'")

        base_key = key[:-5]
        base_value = container.get(base_key)
        if base_key in container:
            yield from self._validate_base_pair(base_key, base_value, lang_map, path)

        list_lengths: Dict[str, int] = {}
        for lang, translated in lang_map.items():
            lang_path = f"{path}.{lang}"
            if translated is None:
                yield Issue("ERROR", "", lang_path, "language value must not be null")
                continue
            if isinstance(translated, str):
                if self.check_empty_strings and not translated.strip():
                    yield Issue("WARN", "", lang_path, "empty string")
            elif isinstance(translated, list):
                list_lengths[lang] = len(translated)
                for idx, item in enumerate(translated):
                    item_path = f"{lang_path}[{idx}]"
                    if item is None:
                        yield Issue("ERROR", "", item_path, "list item must not be null")
                    elif isinstance(item, str) and self.check_empty_strings and not item.strip():
                        yield Issue("WARN", "", item_path, "empty string")
            elif isinstance(translated, dict):
                if not translated:
                    yield Issue("WARN", "", lang_path, "empty object")
            else:
                yield Issue("WARN", "", lang_path, f"unexpected language value type: {type(translated).__name__}")

        if len(set(list_lengths.values())) > 1:
            detail = ", ".join(f"{lang}={length}" for lang, length in sorted(list_lengths.items()))
            yield Issue("ERROR", "", path, f"list lengths differ across languages ({detail})")

    def _validate_base_pair(self, base_key: str, base_value: Any, lang_map: Dict[str, Any], path: str) -> Iterable[Issue]:
        if isinstance(base_value, str):
            for lang, value in lang_map.items():
                if not isinstance(value, str):
                    yield Issue("ERROR", "", f"{path}.{lang}", f"base field '{base_key}' is string, so translated value must be string")
        elif isinstance(base_value, list):
            base_len = len(base_value)
            for lang, value in lang_map.items():
                if not isinstance(value, list):
                    yield Issue("ERROR", "", f"{path}.{lang}", f"base field '{base_key}' is list, so translated value must be list")
                    continue
                if len(value) != base_len:
                    yield Issue("ERROR", "", f"{path}.{lang}", f"list length mismatch vs base field '{base_key}' ({len(value)} != {base_len})")
        elif isinstance(base_value, dict):
            # structured shadow fields are allowed; shape checking is intentionally light here.
            return


def _normalize_issue_file(report: FileReport) -> None:
    for bucket in (report.errors, report.warnings):
        for issue in bucket:
            if not issue.file:
                issue.file = str(report.path)


def _format_issue(issue: Issue) -> str:
    return f"[{issue.level}] {issue.file} :: {issue.path} :: {issue.message}"


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate GenesisPrediction *_i18n completeness in generated artifacts.")
    parser.add_argument(
        "--targets",
        nargs="*",
        default=[str(path) for path in DEFAULT_TARGETS],
        help="JSON artifact paths to validate",
    )
    parser.add_argument(
        "--require-lang",
        dest="required_langs",
        action="append",
        default=list(DEFAULT_REQUIRED_LANGS),
        help="language code that must exist in every leaf *_i18n map (default: en)",
    )
    parser.add_argument(
        "--optional-lang",
        dest="optional_langs",
        action="append",
        default=list(DEFAULT_OPTIONAL_LANGS),
        help="language code that should exist when declared in languages (default: ja, th)",
    )
    parser.add_argument(
        "--enforce-declared-langs",
        action="store_true",
        help="warn when any language listed in root.languages is missing from a leaf *_i18n map",
    )
    parser.add_argument(
        "--allow-empty-strings",
        action="store_true",
        help="do not warn on empty string values inside *_i18n maps",
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="exit with code 1 when warnings exist",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON summary",
    )
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    validator = Validator(
        required_langs=args.required_langs,
        optional_langs=args.optional_langs,
        enforce_declared_langs=args.enforce_declared_langs,
        check_empty_strings=not args.allow_empty_strings,
    )

    reports: List[FileReport] = []
    for raw_path in args.targets:
        path = Path(raw_path)
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        report = validator.validate_file(path)
        _normalize_issue_file(report)
        reports.append(report)

    total_errors = sum(len(r.errors) for r in reports)
    total_warnings = sum(len(r.warnings) for r in reports)

    if args.json:
        payload = {
            "targets": [
                {
                    "path": str(r.path),
                    "meta": r.meta,
                    "errors": [issue.__dict__ for issue in r.errors],
                    "warnings": [issue.__dict__ for issue in r.warnings],
                }
                for r in reports
            ],
            "summary": {
                "errors": total_errors,
                "warnings": total_warnings,
                "status": "FAIL" if (total_errors or (args.fail_on_warn and total_warnings)) else "OK",
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("=== i18n completeness check ===")
        for report in reports:
            print(f"[FILE] {report.path}")
            print(
                f"  lang_default={report.meta.get('lang_default')} "
                f"languages={report.meta.get('languages')} "
                f"i18n_nodes={report.meta.get('i18n_nodes')}"
            )
            if not report.errors and not report.warnings:
                print("  [OK] no issues")
                continue
            for issue in report.errors:
                print("  " + _format_issue(issue))
            for issue in report.warnings:
                print("  " + _format_issue(issue))
        print("=== summary ===")
        print(f"errors={total_errors} warnings={total_warnings}")
        print("status=" + ("FAIL" if (total_errors or (args.fail_on_warn and total_warnings)) else "OK"))

    return 1 if (total_errors or (args.fail_on_warn and total_warnings)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
