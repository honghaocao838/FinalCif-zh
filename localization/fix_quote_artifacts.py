"""Remove stray quotation marks that the bulk translator inserted into f-strings.

When a translated literal was spliced into an f-string chunk, json quoting could
leave literal " characters around the Chinese text. A chunk is an artifact when
the quoted form is not a known translation but the unquoted form is.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANS = Path(__file__).resolve().parent / 'translations'


def zh_values() -> set[str]:
    values = set()
    for f in TRANS.glob('*.json'):
        if f.name.startswith('checkdef_zh'):
            continue
        data = json.loads(f.read_text(encoding='utf-8'))
        for pairs in data.values():
            values.update(pairs.values())
    return values


def line_byte_starts(text: str) -> list[int]:
    starts, pos = [], 0
    for line in text.splitlines(keepends=True):
        starts.append(pos)
        pos += len(line.encode('utf-8'))
    starts.append(pos)
    return starts


def main() -> None:
    dry = '--dry-run' in sys.argv
    known = zh_values()
    total = 0
    for path in sorted((ROOT / 'finalcif').rglob('*.py')):
        if '__pycache__' in str(path):
            continue
        text = path.read_text(encoding='utf-8')
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        starts = line_byte_starts(text)
        raw = text.encode('utf-8')
        edits = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.JoinedStr):
                continue
            for part in node.values:
                if not (isinstance(part, ast.Constant) and isinstance(part.value, str)):
                    continue
                v = part.value
                if not any('\u4e00' <= c <= '\u9fff' for c in v):
                    continue
                if v in known:
                    continue
                stripped = v.strip('"')
                if stripped in known:
                    start = starts[part.lineno - 1] + part.col_offset
                    end = starts[part.end_lineno - 1] + part.end_col_offset
                    chunk = raw[start:end].decode('utf-8')
                    if chunk != v:
                        continue
                    edits.append((start, end, stripped))
        if not edits:
            continue
        for start, end, value in sorted(edits, reverse=True):
            raw = raw[:start] + value.encode('utf-8') + raw[end:]
        if not dry:
            path.write_bytes(raw)
        total += len(edits)
        print(f'{path.relative_to(ROOT)}: {len(edits)} fixed')
    print(f"{'DRY-RUN ' if dry else ''}total {total}")


if __name__ == '__main__':
    main()
