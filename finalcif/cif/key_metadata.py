"""Helpers for CIF key aliases and required-key hints.

The bundled data lives in ``finalcif/datafiles``.  Users may override either
file by placing a copy in the FinalCif configuration directory.  All loaders
degrade gracefully and never raise for missing or broken files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

KEY_ALIASES_FILENAME = 'key_aliases.json'
KEY_REQUIRED_FILENAME = 'key_required.json'

REQUIRED_LEVELS = frozenset({'required', 'recommended'})

_MENTION_RE = re.compile(r'(?<![A-Za-z0-9_])_[A-Za-z][A-Za-z0-9_]*')
_TRAILING_PUNCTUATION = '.,;:!?()[]{}<>"\'“”‘’，。；：！？（）【】《》'


def _datafiles_dir() -> Path:
    """Return the bundled datafiles directory."""
    return Path(__file__).resolve().parent.parent / 'datafiles'


def _parse_json(path: Path) -> dict[str, Any] | None:
    """Return the JSON object at *path*, or None if it cannot be read."""
    try:
        with Path(path).open('r', encoding='utf-8') as file:
            data = json.load(file)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from *path*, returning {} on any error."""
    data = _parse_json(path)
    return data if data is not None else {}


def _valid_aliases(data: dict[str, Any]) -> dict[str, list[str]]:
    """Filter raw alias data down to valid key/alias pairs."""
    aliases: dict[str, list[str]] = {}
    for key, value in data.items():
        if not isinstance(key, str) or not key.startswith('_') or not isinstance(value, list):
            continue
        cleaned = [alias.strip() for alias in value if isinstance(alias, str) and alias.strip()]
        if cleaned:
            aliases[key] = list(dict.fromkeys(cleaned))
    return aliases


def load_key_aliases(path: Path | None = None,
                     user_path: Path | None = None) -> dict[str, list[str]]:
    """Load CIF key aliases, preferring a valid user override.

    Args:
        path: Bundled alias file; defaults to the packaged ``key_aliases.json``.
        user_path: Optional user file that takes priority when it parses as a dict.

    Returns:
        Mapping of CIF keys to non-empty alias lists, or {} on failure.
    """
    bundled = Path(path) if path is not None else _datafiles_dir() / KEY_ALIASES_FILENAME
    if user_path is not None and Path(user_path).is_file():
        user_data = _parse_json(Path(user_path))
        if user_data is not None:
            return _valid_aliases(user_data)
    return _valid_aliases(_load_json(bundled))


def _valid_required(data: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Split raw required-key data into entries and metadata."""
    entries: dict[str, dict[str, Any]] = {}
    for key, value in data.items():
        if key == '_meta' or not isinstance(key, str) or not key.startswith('_'):
            continue
        if not isinstance(value, dict):
            continue
        level = value.get('level')
        note = value.get('note')
        if level not in REQUIRED_LEVELS or not isinstance(note, str) or not note.strip():
            continue
        entry = dict(value)
        entry['level'] = level
        entry['note'] = note.strip()
        entries[key] = entry
    meta = data.get('_meta')
    return entries, dict(meta) if isinstance(meta, dict) else {}


def load_key_required(path: Path | None = None,
                      user_path: Path | None = None) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Load required/recommended key hints and file metadata.

    Args:
        path: Bundled required-key file; defaults to the packaged ``key_required.json``.
        user_path: Optional user file that takes priority when it parses as a dict.

    Returns:
        ``(entries, meta)`` where entries contain only valid levels and notes.
        Returns ``({}, {})`` on failure.
    """
    bundled = Path(path) if path is not None else _datafiles_dir() / KEY_REQUIRED_FILENAME
    if user_path is not None and Path(user_path).is_file():
        user_data = _parse_json(Path(user_path))
        if user_data is not None:
            return _valid_required(user_data)
    return _valid_required(_load_json(bundled))


def user_config_path(filename: str) -> Path:
    """Return the user configuration path for *filename*.

    The settings import happens lazily so importing this module never loads Qt.
    """
    from finalcif.tools.settings import _default_config_dir
    return _default_config_dir() / filename


def alias_index(aliases: dict[str, list[str]]) -> dict[str, set[str]]:
    """Build a case-insensitive alias lookup mapping aliases to CIF keys."""
    index: dict[str, set[str]] = {}
    for key, values in aliases.items():
        if not isinstance(key, str) or not key.startswith('_') or not isinstance(values, list):
            continue
        for alias in values:
            if not isinstance(alias, str):
                continue
            normalized = alias.strip().lower()
            if normalized:
                index.setdefault(normalized, set()).add(key)
    return index


def mentioned_keys(text: str) -> set[str]:
    """Return unique CIF data names mentioned in plain text."""
    keys: set[str] = set()
    for match in _MENTION_RE.findall(text):
        key = match.rstrip(_TRAILING_PUNCTUATION)
        if len(key) > 3:
            keys.add(key)
    return keys


def required_note(key: str) -> str:
    """Return the Chinese note for *key*, or an empty string."""
    entries, _meta = load_key_required()
    return entries.get(key, {}).get('note', '')
