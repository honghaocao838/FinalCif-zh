"""Split all CIF dictionary help texts into translation work packages.

Reads the dict literals from finalcif/cif/*_dict.py plus additional_keywords
from all_cif_dicts.py and writes localization/dict_work/partN_in.json.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(__file__).resolve().parent / 'dict_work'
PARTS = 18


def dict_from_module(path: Path, varname: str) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == varname:
            data = {}
            for k, v in zip(node.value.keys, node.value.values):
                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                    data[k.value] = v.value
            return data
    return {}


def main() -> None:
    sources = [
        ('core_dict.py', 'cif_core'),
        ('modulation_dict.py', 'modulation_dict'),
        ('powder_dict.py', 'powder_dict'),
        ('restraints_dict.py', 'restraints_dict'),
        ('twin_dict.py', 'twinning_dict'),
    ]
    merged = {}
    for fname, var in sources:
        data = dict_from_module(ROOT / 'finalcif' / 'cif' / fname, var)
        print(f'{fname}: {len(data)} entries')
        merged.update(data)
    extra = dict_from_module(ROOT / 'finalcif' / 'cif' / 'all_cif_dicts.py', 'additional_keywords')
    print(f'additional_keywords: {len(extra)} entries')
    merged.update(extra)

    print(f'total keys: {len(merged)}, chars: {sum(len(v) for v in merged.values())}')
    items = sorted(merged.items(), key=lambda kv: -len(kv[1]))
    buckets = [[] for _ in range(PARTS)]
    sizes = [0] * PARTS
    for key, text in items:
        i = sizes.index(min(sizes))
        buckets[i].append((key, text))
        sizes[i] += len(text)

    WORK.mkdir(parents=True, exist_ok=True)
    for i, bucket in enumerate(buckets, start=1):
        bucket.sort()
        data = dict(bucket)
        out = WORK / f'part{i}_in.json'
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'{out.name}: {len(data)} entries, {sum(len(v) for v in data.values())} chars')


if __name__ == '__main__':
    main()
