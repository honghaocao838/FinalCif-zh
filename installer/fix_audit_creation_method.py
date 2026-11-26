#!/usr/bin/env python3
"""Replace the translated _audit_creation_method value with the English original.

The Chinese edition before 2026-11-26 wrote

    _audit_creation_method 'FinalCif V180，作者 Daniel Kratzert，Freiburg 2026，https://...'

into generated CIF files.  CIF data values must stay in English, so this script
rewrites that single line and leaves the rest of the file untouched.

Usage:
    python fix_audit_creation_method.py file.cif [more.cif ...]
    python fix_audit_creation_method.py "D:\\data"     # all *.cif in the folder

The script is standalone (standard library only).  It also works with the
python.exe that ships with FinalCif.
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

TAG = '_audit_creation_method'
LINE_RE = re.compile(r'^(\s*_audit_creation_method\s+)(.*?)(\r?\n)?$')
VERSION_RE = re.compile(r'V(\d+)')
YEAR_RE = re.compile(r'Freiburg\s+(\d{4})')


def fix_text(text: str) -> tuple[str, int, int]:
    lines = text.splitlines(keepends=True)
    changed = 0
    skipped = 0
    for index, line in enumerate(lines):
        match = LINE_RE.match(line)
        if not match:
            continue
        value = match.group(2).strip()
        if not value or value.startswith(';'):
            skipped += 1
            continue
        if 'by Daniel Kratzert' in value and 'https://dkratzert.de/finalcif.html' in value:
            continue
        version_match = VERSION_RE.search(value)
        year_match = YEAR_RE.search(value)
        version = version_match.group(1) if version_match else '180'
        year = year_match.group(1) if year_match else '2026'
        replacement = (
            f"{match.group(1)}'FinalCif V{version} by Daniel Kratzert, "
            f"Freiburg {year}, https://dkratzert.de/finalcif.html'{match.group(3) or ''}"
        )
        lines[index] = replacement
        changed += 1
    return ''.join(lines), changed, skipped


def fix_file(path: Path) -> tuple[int, int]:
    with io.open(path, 'r', encoding='utf-8-sig', newline='') as handle:
        text = handle.read()
    fixed, changed, skipped = fix_text(text)
    if changed:
        temp = path.with_name(path.name + '.tmp')
        with io.open(temp, 'w', encoding='utf-8', newline='') as handle:
            handle.write(fixed)
        temp.replace(path)
    return changed, skipped


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip())
        return 1
    paths: list[Path] = []
    for arg in argv:
        path = Path(arg)
        if path.is_dir():
            paths.extend(sorted(path.glob('*.cif')))
        elif path.is_file():
            paths.append(path)
        else:
            print(f'not found: {path}')
    total = 0
    for path in paths:
        try:
            changed, skipped = fix_file(path)
        except Exception as exc:
            print(f'FAILED {path}: {exc}')
            continue
        total += changed
        if changed:
            print(f'fixed {path} ({changed} line(s))')
        elif skipped:
            print(f'skipped {path} (unusual multiline value)')
        else:
            print(f'unchanged {path}')
    print(f'done: {total} line(s) fixed in {len(paths)} file(s)')
    return 0 if total or paths else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
