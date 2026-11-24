"""Merge and validate the translated check.def alerts.

- parses localization/work/partN_zh.json
- checks keys against the English input files
- checks that $ placeholders are preserved
- writes the consolidated mapping used by the application
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WORK = HERE / 'work'
OUT_APP = ROOT / 'finalcif' / 'datafiles' / 'checkdef_zh.json'
OUT_REPO = HERE / 'checkdef_zh.json'
PLACEHOLDER = re.compile(r'\$[A-Z]')


def main() -> None:
    merged = {}
    existing = ROOT / 'finalcif' / 'datafiles' / 'checkdef_zh.json'
    if existing.exists():
        merged.update(json.loads(existing.read_text(encoding='utf-8')))

    problems = []
    for i in range(1, 7):
        inp = WORK / f'part{i}_in.json'
        out = WORK / f'part{i}_zh.json'
        en = json.loads(inp.read_text(encoding='utf-8'))
        zh = json.loads(out.read_text(encoding='utf-8'))
        if set(en) != set(zh):
            problems.append(f'part{i}: key mismatch ({len(en)} vs {len(zh)})')
        for code, text in zh.items():
            source = en.get(code, '')
            if not text.strip():
                problems.append(f'{code}: empty translation')
            if sorted(PLACEHOLDER.findall(source)) != sorted(PLACEHOLDER.findall(text)):
                problems.append(f'{code}: placeholder mismatch '
                                f'{PLACEHOLDER.findall(source)} vs {PLACEHOLDER.findall(text)}')
            if text == source:
                problems.append(f'{code}: not translated')
        merged.update(zh)
        print(f'part{i}: {len(zh)} entries')

    if problems:
        print('--- problems ---')
        for p in problems[:40]:
            print(p)
        print(f'total problems: {len(problems)}')

    OUT_APP.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding='utf-8')
    OUT_REPO.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'wrote {len(merged)} entries to {OUT_APP.relative_to(ROOT)} and localization/checkdef_zh.json')


if __name__ == '__main__':
    main()
