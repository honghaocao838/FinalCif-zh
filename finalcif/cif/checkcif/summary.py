"""Parsing of CheckCIF alert summaries.

Online CheckCIF reports contain both per-alert lines such as
``PLAT413_ALERT_2_C`` and summary lines such as ``2 ALERT level C``.  PLATON's
offline ``.chk`` file uses the same alert codes.  This module turns either form
into a small, UI-independent structure and never raises on malformed input.
"""
from __future__ import annotations

import html as html_module
import re
from dataclasses import dataclass, field

LEVELS = ('A', 'B', 'C', 'G')

_ALERT_RE = re.compile(
    r'(?P<code>[A-Z][A-Z0-9]*\d+|\d{3,})_ALERT_(?P<atype>\d)_(?P<level>[A-G])\b'
    r'\s*(?P<desc>.*)')
_COUNT_RE = re.compile(
    r'(\d+)[ \t]*(?:<[^>]+>[ \t]*)*ALERT\s+level[ \t]+([A-G])', re.IGNORECASE)
_COUNT_ALT_RE = re.compile(
    r'Alert[ \t]+level[ \t]+([A-G])[ \t]*[:=][ \t]*(\d+)', re.IGNORECASE)
_COUNT_CHK_RE = re.compile(
    r'(\d+)[ \t]+ALERT_Level_([A-G])', re.IGNORECASE)
_TAG_RE = re.compile(r'<[^>]+>')
_KEY_RE = re.compile(r'(?<![A-Za-z0-9_])_[A-Za-z][A-Za-z0-9_]*')
_TRAILING = '.,;:!?()[]{}<>"\'“”‘’，。；：！？（）【】《》'


@dataclass
class AlertItem:
    code: str
    level: str
    summary: str
    source: str = 'online'


@dataclass
class CheckCifSummary:
    counts: dict[str, int] = field(default_factory=lambda: {level: 0 for level in LEVELS})
    items: list[AlertItem] = field(default_factory=list)
    mentioned_keys: set[str] = field(default_factory=set)
    raw_text: str = ''
    parsed: bool = False

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def _clean(text: str) -> str:
    return re.sub(r'\s+', ' ', html_module.unescape(_TAG_RE.sub('', text))).strip()


def _normalise_counts(counts: dict[str, int]) -> dict[str, int]:
    return {level: int(counts.get(level, 0)) for level in LEVELS}


def _counts_from_items(items: list[AlertItem]) -> dict[str, int]:
    counts = {level: 0 for level in LEVELS}
    for item in items:
        if item.level in counts:
            counts[item.level] += 1
    return counts


def _items_from_text(text: str, source: str) -> list[AlertItem]:
    items: list[AlertItem] = []
    for match in _ALERT_RE.finditer(text):
        code = match.group('code').upper()
        if code.isdigit():
            # PLATON .chk files use 041_ALERT_1_C instead of PLAT041.
            code = f'PLAT{code}'
        level = match.group('level').upper()
        summary = _clean(match.group('desc'))
        if not summary:
            continue
        items.append(AlertItem(code=code, level=level, summary=summary, source=source))
    return items


def extract_cif_keys(text: str) -> set[str]:
    """Return CIF data names mentioned in plain text."""
    keys: set[str] = set()
    for match in _KEY_RE.findall(text):
        key = match.rstrip(_TRAILING)
        if len(key) > 3:
            keys.add(key)
    return keys


def parse_html(html: str) -> CheckCifSummary:
    """Parse an online CheckCIF HTML report."""
    if not html or not html.strip():
        return CheckCifSummary()
    try:
        counts: dict[str, int] = {}
        for value, level in _COUNT_RE.findall(html):
            counts.setdefault(level.upper(), int(value))
        for level, value in _COUNT_ALT_RE.findall(html):
            counts.setdefault(level.upper(), int(value))

        items: list[AlertItem] = _items_from_text(html, 'online')
        if not counts:
            counts = _counts_from_items(items)
        plain = _clean(html)
        return CheckCifSummary(counts=_normalise_counts(counts), items=items,
                               mentioned_keys=extract_cif_keys(plain), raw_text=plain,
                               parsed=True)
    except Exception:
        return CheckCifSummary()


def parse_chk(text: str) -> CheckCifSummary:
    """Parse the plain-text PLATON ``.chk`` output."""
    if not text or not text.strip():
        return CheckCifSummary()
    try:
        counts: dict[str, int] = {}
        for value, level in _COUNT_CHK_RE.findall(text):
            counts.setdefault(level.upper(), int(value))
        for level, value in _COUNT_ALT_RE.findall(text):
            counts.setdefault(level.upper(), int(value))
        for value, level in _COUNT_RE.findall(text):
            counts.setdefault(level.upper(), int(value))
        items = _items_from_text(text, 'offline')
        if not counts:
            counts = _counts_from_items(items)
        return CheckCifSummary(counts=_normalise_counts(counts), items=items,
                               mentioned_keys=extract_cif_keys(text), raw_text=text,
                               parsed=True)
    except Exception:
        return CheckCifSummary()
