"""Merge and validate translated CIF dictionary help texts.

Checks keys, HTML tag balance and CJK presence, then writes
finalcif/datafiles/cif_dict_zh.json (used by all_cif_dicts.py).
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WORK = HERE / 'dict_work'
OUT_APP = ROOT / 'finalcif' / 'datafiles' / 'cif_dict_zh.json'
PARTS = 18
CJK = re.compile(r'[\u4e00-\u9fff]')


def tag_counts(text: str) -> dict[str, int]:
    return {
        'pre': text.count('<pre>'),
        'pre_end': text.count('</pre>'),
        'h2': text.count('<h2>'),
        'h2_end': text.count('</h2>'),
        'h4': text.count('<h4>'),
        'h4_end': text.count('</h4>'),
    }


def main() -> None:
    merged = {}
    problems = []
    for i in range(1, PARTS + 1):
        inp = WORK / f'part{i}_in.json'
        out = WORK / f'part{i}_zh.json'
        if not out.exists():
            problems.append(f'part{i}: missing output')
            continue
        en = json.loads(inp.read_text(encoding='utf-8'))
        zh = json.loads(out.read_text(encoding='utf-8'))
        if set(en) != set(zh):
            problems.append(f'part{i}: key mismatch ({len(en)} vs {len(zh)})')
        for key, text in zh.items():
            source = en.get(key, '')
            if not text.strip():
                problems.append(f'{key}: empty')
                continue
            a, b = tag_counts(source), tag_counts(text)
            if a != b:
                problems.append(f'{key}: tag mismatch {a} -> {b}')
            if len(source) > 60 and not CJK.search(text):
                problems.append(f'{key}: no Chinese text')
        merged.update(zh)
        print(f'part{i}: {len(zh)} entries')

    if problems:
        print('--- problems ---')
        for p in problems[:60]:
            print(p)
        print(f'total problems: {len(problems)}')

    OUT_APP.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding='utf-8')
    total = sum(len(v) for v in merged.values())
    print(f'wrote {len(merged)} entries ({total} chars) to {OUT_APP.relative_to(ROOT)}')
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
