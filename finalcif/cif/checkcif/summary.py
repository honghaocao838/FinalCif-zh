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

_ALERT_HTML_RE = re.compile(
    r'PLAT(\d{3})_ALERT_(\d)_([A-G])\s*</a>\s*([^<\n]*)', re.IGNORECASE)
_ALERT_PLAIN_RE = re.compile(
    r'(?:PLAT(?P<plat>\d{3})|(?P<num>\d{3}))_ALERT_(?P<atype>\d)_(?P<level>[A-G])\b'
    r'\s*(?P<desc>.*)', re.IGNORECASE)
_COUNT_RE = re.compile(
    r'(\d+)\s*(?:<[^>]+>\s*)*ALERT\s+level\s+([A-G])', re.IGNORECASE)
_COUNT_ALT_RE = re.compile(
    r'Alert\s+level\s+([A-G])\s*[:=]\s*(\d+)', re.IGNORECASE)
_COUNT_CHK_RE = re.compile(
    r'(\d+)\s+ALERT_Level_([A-G])', re.IGNORECASE)
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
    seen: set[tuple[str, str, str]] = set()
    for match in _ALERT_PLAIN_RE.finditer(text):
        number = match.group('plat') or match.group('num')
        level = match.group('level').upper()
        summary = _clean(match.group('desc'))
        code = f'PLAT{number}'
        key = (code, level, summary)
        if not summary or key in seen:
            continue
        seen.add(key)
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
    try:
        counts: dict[str, int] = {}
        for value, level in _COUNT_RE.findall(html):
            counts.setdefault(level.upper(), int(value))
        for level, value in _COUNT_ALT_RE.findall(html):
            counts.setdefault(level.upper(), int(value))

        items: list[AlertItem] = []
        seen: set[tuple[str, str, str]] = set()
        for number, _atype, level, description in _ALERT_HTML_RE.findall(html):
            summary = _clean(description)
            code = f'PLAT{number}'
            key = (code, level.upper(), summary)
            if not summary or key in seen:
                continue
            seen.add(key)
            items.append(AlertItem(code=code, level=level.upper(),
                                   summary=summary, source='online'))
        if not items:
            items = _items_from_text(_clean(html), 'online')
        if not counts:
            counts = _counts_from_items(items)
        plain = _clean(html)
        return CheckCifSummary(counts=_normalise_counts(counts), items=items,
                               mentioned_keys=extract_cif_keys(plain), raw_text=plain)
    except Exception:
        return CheckCifSummary()


def parse_chk(text: str) -> CheckCifSummary:
    """Parse the plain-text PLATON ``.chk`` output."""
    try:
        counts: dict[str, int] = {}
        for value, level in _COUNT_RE.findall(text):
            counts.setdefault(level.upper(), int(value))
        for level, value in _COUNT_ALT_RE.findall(text):
            counts.setdefault(level.upper(), int(value))
        for value, level in _COUNT_CHK_RE.findall(text):
            counts.setdefault(level.upper(), int(value))
        items = _items_from_text(text, 'offline')
        if not counts:
            counts = _counts_from_items(items)
        return CheckCifSummary(counts=_normalise_counts(counts), items=items,
                               mentioned_keys=extract_cif_keys(text), raw_text=text)
    except Exception:
        return CheckCifSummary()
