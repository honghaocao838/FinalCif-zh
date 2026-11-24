"""Apply the Chinese translation tables to the FinalCif source tree.

The tables in ``translations/*.json`` map module paths (as they appear in the
original .pyc layout) to English -> Chinese pairs. This script parses each
source file with :mod:`ast` and rewrites the matching string literals by their
exact source span, so implicitly concatenated literals and f-string chunks are
handled correctly.

Files that were replaced as a whole (generated UI module, table model, start
script) are skipped here and handled separately.

Usage: python localization/apply_translations.py [--dry-run]
"""
import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TRANS = HERE / 'translations'

# Replaced wholesale by localized versions:
SKIP = {
    'gui/finalcif_gui_ui.pyc',
    'gui/cif_table_model.pyc',
    'finalcif_start.pyc',
}
# Third-party package, patched at package-build time:
SKIP_PREFIX = ('fastmolwidget/',)


def _line_byte_starts(text: str) -> list[int]:
    starts, pos = [], 0
    for line in text.splitlines(keepends=True):
        starts.append(pos)
        pos += len(line.encode('utf-8'))
    starts.append(pos)
    return starts


def _lookup(value: str, mapping: dict) -> tuple[str, str] | None:
    """Exact match, or match ignoring trailing padding (padding is kept)."""
    if value in mapping:
        return value, mapping[value]
    stripped = value.rstrip()
    if stripped != value and stripped in mapping:
        return stripped, mapping[stripped] + value[len(stripped):]
    return None


def _fstring_chunk_literal(text: str, start: int, end: int, zh: str) -> str | None:
    """Build a quoted literal that is safe inside an existing f-string chunk.

    Returns None when the node spans a literal boundary (ff-string + adjacent
    literal), because the closing quote sits inside that span.
    """
    raw = text.encode('utf-8')
    chunk = raw[start:end].decode('utf-8', 'ignore')
    if "'" in chunk or '"' in chunk:
        return None
    prefix = raw[:start].decode('utf-8', 'ignore')
    pos_single = prefix.rfind("f'")
    pos_double = prefix.rfind('f"')
    if pos_single < 0 and pos_double < 0:
        return None
    delim = "'" if pos_single > pos_double else '"'
    other = '"' if delim == "'" else "'"
    body = zh.replace('\\', '\\\\').replace(other, '\\' + other)
    body = body.replace('\n', '\\n')
    body = body.replace('{', '{{').replace('}', '}}')
    return other + body + other


def apply_file(path: Path, mapping: dict, dry: bool) -> tuple[int, list[str]]:
    text = path.read_text(encoding='utf-8')
    tree = ast.parse(text)
    starts = _line_byte_starts(text)

    inside_fstring = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            for part in node.values:
                if isinstance(part, ast.Constant):
                    inside_fstring.add(id(part))

    edits, used, skipped_fstring = [], set(), []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        found = _lookup(node.value, mapping)
        if found is None:
            continue
        key, zh = found
        if key == zh:
            continue
        start = starts[node.lineno - 1] + node.col_offset
        end = starts[node.end_lineno - 1] + node.end_col_offset
        if id(node) in inside_fstring:
            literal = _fstring_chunk_literal(text, start, end, zh)
            if literal is None:
                skipped_fstring.append(key)
                continue
        else:
            literal = json.dumps(zh, ensure_ascii=False)
        edits.append((start, end, literal))
        used.add(key)

    misses = [k for k in mapping if k not in used and k != mapping[k]]
    if not edits:
        return 0, misses, skipped_fstring

    raw = text.encode('utf-8')
    for start, end, literal in sorted(edits, reverse=True):
        raw = raw[:start] + literal.encode('utf-8') + raw[end:]
    if not dry:
        path.write_bytes(raw)
    return len(edits), misses, skipped_fstring


def main() -> None:
    dry = '--dry-run' in sys.argv
    total = 0
    all_misses = {}
    for map_file in sorted(TRANS.glob('*.json')):
        if map_file.name.startswith('checkdef_zh'):
            continue
        data = json.loads(map_file.read_text(encoding='utf-8'))
        for module, mapping in data.items():
            if module in SKIP or module.startswith(SKIP_PREFIX):
                continue
            src = ROOT / 'finalcif' / module.replace('.pyc', '.py')
            if not src.exists():
                print(f'MISSING SOURCE {module}')
                continue
            hits, misses, skipped = apply_file(src, mapping, dry)
            if skipped:
                print(f'{module}: {len(skipped)} f-string chunks need manual patching: {skipped[:5]}')
            total += hits
            if misses:
                all_misses[module] = misses
    print(f"{'DRY-RUN: ' if dry else ''}replaced {total} literals")
    if all_misses:
        print('--- literals not found (upstream changed?) ---')
        for module, misses in all_misses.items():
            print(f'{module}: {len(misses)}')
            for m in misses[:6]:
                print('   ', repr(m)[:120])


if __name__ == '__main__':
    main()
