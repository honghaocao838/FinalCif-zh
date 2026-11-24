"""Patch string constants inside .pyc files (used for the bundled fastmolwidget).

Usage: python patch_pyc.py <root> <map.json>
Map format: {"fastmolwidget/density_controls.pyc": {"English": "中文"}}
"""
import json
import marshal
import sys
import types
from collections import Counter
from pathlib import Path

HEADER = 16  # magic(4) + flags(4) + mtime/size or hash(8)


def protect(c: str, mapping: dict) -> tuple[str, str] | None:
    if c in mapping:
        return c, mapping[c]
    stripped = c.rstrip()
    if stripped != c and stripped in mapping:
        return stripped, mapping[stripped] + c[len(stripped):]
    return None


def walk(code: types.CodeType, mapping: dict, hits: Counter) -> tuple[types.CodeType, bool]:
    consts, changed = [], False
    for c in code.co_consts:
        if isinstance(c, str):
            found = protect(c, mapping)
            if found:
                key, repl = found
                hits[key] += 1
                consts.append(repl)
                changed = True
            else:
                consts.append(c)
        elif isinstance(c, types.CodeType):
            new_c, ch = walk(c, mapping, hits)
            consts.append(new_c)
            changed |= ch
        elif isinstance(c, (tuple, list, frozenset)):
            new_items, ch = [], False
            for item in c:
                if isinstance(item, str):
                    found = protect(item, mapping)
                    if found:
                        key, repl = found
                        hits[key] += 1
                        new_items.append(repl)
                        ch = True
                    else:
                        new_items.append(item)
                else:
                    new_items.append(item)
            if ch:
                consts.append(type(c)(new_items))
                changed = True
            else:
                consts.append(c)
        else:
            consts.append(c)
    if not changed:
        return code, False
    return code.replace(co_consts=tuple(consts)), True


def main() -> None:
    root = Path(sys.argv[1])
    mapping = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
    total = 0
    for module, pairs in mapping.items():
        pyc = root / module
        if not pyc.exists():
            print(f'missing {module}')
            continue
        raw = pyc.read_bytes()
        code = marshal.loads(raw[HEADER:])
        hits: Counter = Counter()
        new_code, changed = walk(code, pairs, hits)
        if changed:
            pyc.write_bytes(raw[:HEADER] + marshal.dumps(new_code))
            total += sum(hits.values())
            print(f'{module}: {sum(hits.values())} strings')
        else:
            print(f'{module}: nothing to do')
    print(f'total {total}')


if __name__ == '__main__':
    main()
