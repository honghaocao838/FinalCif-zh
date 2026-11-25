"""IUCr checkCIF prefilter tests and their Chinese advice.

The PLATON ``check.def`` covers PLAT alerts only.  IUCr's checkCIF also runs
prefilter tests (SYMM001, EXPT005, ...), whose descriptions live on the IUCr
Journals site.  ``prefilter_zh.json`` bundles a Chinese summary of those rules
plus the CIF keys they inspect.  Lookup never raises and falls back to None.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PREFILTER_FILENAME = 'prefilter_zh.json'


def _datafiles_dir() -> Path:
    return Path(__file__).resolve().parent.parent / 'datafiles'


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_prefilter(path: Path | None = None,
                   user_path: Path | None = None) -> dict[str, dict]:
    """Load the prefilter table, preferring a valid user override."""
    bundled = Path(path) if path is not None else _datafiles_dir() / PREFILTER_FILENAME
    if user_path is not None and Path(user_path).is_file():
        user = _load_json(Path(user_path))
        if user:
            return _valid_entries(user)
    return _valid_entries(_load_json(bundled))


def _valid_entries(data: dict[str, Any]) -> dict[str, dict]:
    entries: dict[str, dict] = {}
    for code, value in data.items():
        if code == '_meta' or not isinstance(code, str) or not isinstance(value, dict):
            continue
        zh = value.get('zh')
        keys = value.get('keys')
        if not isinstance(zh, str) or not zh.strip() or not isinstance(keys, list):
            continue
        entry = dict(value)
        entry['keys'] = [key for key in keys if isinstance(key, str) and key.startswith('_')]
        entries[normalize_code(code)] = entry
    return entries


def normalize_code(code: str) -> str:
    """SYMM_001 / symm001 -> SYMM001; PLAT084 is handled elsewhere."""
    return code.strip().replace('_', '').upper()


def lookup_prefilter(data: dict[str, dict], code: str) -> dict | None:
    if not data or not code:
        return None
    return data.get(normalize_code(code))


def format_prefilter_help(code: str, entry: dict) -> str:
    """Full Chinese advice with the original IUCr text appended."""
    keys = '、'.join(entry.get('keys', [])) or '（该规则不针对单个 CIF 键）'
    return (f'【CIF 预检项 {normalize_code(code)}】\n'
            f'{entry.get("zh", "").strip()}\n\n'
            f'涉及 CIF 键：{keys}\n\n'
            f'【English 原文（IUCr prefilter）】\n{entry.get("en", "").strip()}')


