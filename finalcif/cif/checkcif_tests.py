"""Chinese advice for IUCr checkCIF tests that are neither PLAT nor prefilter.

PLAT alerts are described by PLATON's ``check.def``; the IUCr prefilter table
covers the rules on the prefilter page.  A few checkCIF tests (for example
``THETM01``) have their own procedure pages and are stored here.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TESTS_FILENAME = 'checkcif_tests_zh.json'


def _datafiles_dir() -> Path:
    return Path(__file__).resolve().parent.parent / 'datafiles'


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def normalize_code(code: str) -> str:
    """THETM_01 / thetm01 -> THETM01."""
    return code.strip().replace('_', '').upper()


def load_checkcif_tests(path: Path | None = None) -> dict[str, dict]:
    bundled = Path(path) if path is not None else _datafiles_dir() / TESTS_FILENAME
    entries: dict[str, dict] = {}
    for code, value in _load_json(bundled).items():
        if code == '_meta' or not isinstance(code, str) or not isinstance(value, dict):
            continue
        zh = value.get('zh')
        if not isinstance(zh, str) or not zh.strip():
            continue
        entry = dict(value)
        entry['keys'] = [key for key in value.get('keys', [])
                         if isinstance(key, str) and key.startswith('_')]
        entries[normalize_code(code)] = entry
    return entries


def lookup_checkcif_test(data: dict[str, dict], code: str) -> dict | None:
    if not data or not code:
        return None
    return data.get(normalize_code(code))


def format_checkcif_test_help(code: str, entry: dict) -> str:
    keys = '、'.join(entry.get('keys', [])) or '（该规则不针对单个 CIF 键）'
    return (f'【IUCr CheckCIF 检查项 {normalize_code(code)}】\n'
            f'{entry.get("zh", "").strip()}\n\n'
            f'涉及 CIF 键：{keys}\n\n'
            f'【English 原文（IUCr checkCIF）】\n{entry.get("en", "").strip()}')
