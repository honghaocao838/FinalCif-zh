"""Split the untranslated check.def alerts into work packages for translation.

Reads finalcif/datafiles/check.def, skips alerts that already have a Chinese
translation, and writes localization/work/partN_in.json ({code: english_text}).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK_DEF = ROOT / 'finalcif' / 'datafiles' / 'check.def'
DONE = ROOT / 'finalcif' / 'datafiles' / 'checkdef_zh.json'
WORK = Path(__file__).resolve().parent / 'work'
PARTS = 6


def parse_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        if line.startswith('_') and len(line) > 4 and line[1:4].isdigit():
            current = line[1:4]
            blocks[current] = []
            continue
        if current is not None:
            if line.startswith('#==='):
                current = None
            else:
                blocks[current].append(line)
    # The help text is everything after the header line and the short message line.
    return {code: '\n'.join(lines[2:]).strip() for code, lines in blocks.items()}


def main() -> None:
    blocks = parse_blocks(CHECK_DEF.read_text(encoding='utf-8', errors='ignore'))
    done = set(json.loads(DONE.read_text(encoding='utf-8')))
    todo = {c: t for c, t in blocks.items() if c not in done and t.strip()}
    print(f'blocks={len(blocks)} translated={len(done)} todo={len(todo)}')

    # Balance by text length so every part takes a similar amount of work.
    items = sorted(todo.items(), key=lambda kv: -len(kv[1]))
    buckets = [[] for _ in range(PARTS)]
    sizes = [0] * PARTS
    for code, text in items:
        i = sizes.index(min(sizes))
        buckets[i].append((code, text))
        sizes[i] += len(text)

    WORK.mkdir(parents=True, exist_ok=True)
    for i, bucket in enumerate(buckets, start=1):
        bucket.sort()
        data = dict(bucket)
        out = WORK / f'part{i}_in.json'
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'{out.name}: {len(data)} alerts, {sum(len(v) for v in data.values())} chars')


if __name__ == '__main__':
    main()
