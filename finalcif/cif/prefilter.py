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


def required_key_notes(data: dict[str, dict]) -> dict[str, str]:
    """Return ``key -> note`` for prefilter rules that require the key.

    Several codes can cover the same key; the notes are merged in a stable
    order so the main-table tooltip names all relevant prefilter tests.
    """
    by_key: dict[str, list[tuple[str, str]]] = {}
    for code, entry in data.items():
        if not entry.get('required'):
            continue
        for key in entry.get('keys', []):
            by_key.setdefault(key, []).append((code, entry.get('zh', '')))
    notes: dict[str, str] = {}
    for key, values in by_key.items():
        codes = '、'.join(dict.fromkeys(code for code, _ in values))
        advice = values[0][1].strip()
        notes[key] = f'CIF 预检项（{codes}）：{advice}'
    return notes


def prefilter_codes_by_key(data: dict[str, dict]) -> dict[str, str]:
    """Return ``key -> 'CIF 预检项：CODE1、CODE2'`` for table tooltips."""
    by_key: dict[str, list[str]] = {}
    for code, entry in data.items():
        for key in entry.get('keys', []):
            by_key.setdefault(key, []).append(code)
    notes: dict[str, str] = {}
    for key, codes in by_key.items():
        unique = list(dict.fromkeys(codes))
        shown = '、'.join(unique[:3])
        if len(unique) > 3:
            shown += f' 等 {len(unique)} 项'
        notes[key] = 'CIF 预检项：' + shown
    return notes
