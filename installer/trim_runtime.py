"""Remove components of the FinalCif runtime that the application never loads.

Run by installer/build_installer.ps1 on the staged directory. Only modules that
FinalCif/fastmolwidget do not import are removed; OpenGL, Svg, widgets, plugins
for images and platforms are kept. The spell checker keeps the Hunspell engine
(and its dependency closure), which is what pyenchant uses for en_US/en_GB.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
SITE = ROOT / 'Lib' / 'site-packages'
PS = SITE / 'PySide6'

# Qt module families that FinalCif does not import (QtWidgets-based app).
QT_PREFIXES = (
    'Quick', 'Qml', 'Labs', 'Lottie', 'Designer', 'Help', 'Test', 'UiTools',
    'Network', 'Sql', 'DBus', 'PrintSupport', 'Pdf', 'Xml',
)
KEEP_QM = {'qtbase_zh_CN.qm', 'qt_zh_CN.qm'}
DROP_PLUGINS = ('qmltooling', 'designer', 'sqldrivers', 'tls', 'networkinformation',
                'vectorimageformats')
KEEP_DICTS = {'en_US', 'en_GB'}


def rm(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_dir():
        size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        shutil.rmtree(path, ignore_errors=True)
    else:
        size = path.stat().st_size
        path.unlink(missing_ok=True)
    return size


def main() -> None:
    removed = {}

    def cut(name: str, path: Path) -> None:
        n = rm(path)
        if n:
            removed[name] = removed.get(name, 0) + n

    # Qt translations: keep the two Chinese catalogues only.
    tr = PS / 'translations'
    if tr.exists():
        for f in tr.glob('*.qm'):
            if f.name not in KEEP_QM:
                cut('Qt translations', f)

    # Unused Qt DLLs and Python bindings.
    dll_prefixes = tuple('Qt6' + p for p in QT_PREFIXES)
    pyd_prefixes = tuple('Qt' + p for p in QT_PREFIXES)
    for f in list(PS.glob('Qt6*.dll')):
        if f.name.startswith(dll_prefixes):
            cut('Qt modules', f)
    for f in list(PS.glob('*.pyd')):
        if f.stem.startswith(pyd_prefixes):
            cut('Qt bindings', f)

    # Plugins for the removed modules.
    for name in DROP_PLUGINS:
        cut('Qt plugins', PS / 'plugins' / name)
    cut('Qt plugins', PS / 'plugins' / 'imageformats' / 'qpdf.dll')

    # Development-only files.
    for name in ('include', 'typesystems'):
        cut('PySide6 dev files', PS / name)
    cut('Scripts', ROOT / 'Scripts')
    for f in SITE.rglob('*.lib'):
        cut('Static import libs', f)

    # Spell checker: keep Hunspell and its dependency closure, drop nuspell/ICU.
    ench = SITE / 'enchant' / 'data' / 'mingw64'
    bin_dir = ench / 'bin'
    provider_dir = ench / 'lib' / 'enchant-2'
    if bin_dir.exists():
        try:
            import pefile
        except Exception:
            print('WARN: pefile not available, keeping all enchant DLLs')
        else:
            names = {p.name.lower(): p for p in bin_dir.glob('*.dll')}

            def imports(path: Path) -> set[str]:
                pe = pefile.PE(str(path), fast_load=True)
                pe.parse_data_directories(
                    directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
                return {e.dll.decode().lower() for e in (pe.DIRECTORY_ENTRY_IMPORT or [])}

            needed, queue = set(), ['libenchant-2.dll', 'libhunspell-1.7-0.dll']
            while queue:
                cur = queue.pop()
                if cur in needed or cur not in names:
                    continue
                needed.add(cur)
                queue.extend(imports(names[cur]))
            for name, path in names.items():
                if name not in needed:
                    cut('enchant runtime', path)
    if provider_dir.exists():
        for f in provider_dir.iterdir():
            if f.name != 'enchant_hunspell.dll':
                cut('enchant providers', f)
    hunspell_dir = ench / 'share' / 'enchant' / 'hunspell'
    if hunspell_dir.exists():
        for f in hunspell_dir.iterdir():
            if f.stem not in KEEP_DICTS:
                cut('Spell dictionaries', f)

    total = sum(removed.values()) / 1048576
    print(f'trimmed {total:.1f} MB from the staged runtime')
    for name, size in sorted(removed.items(), key=lambda kv: -kv[1]):
        print(f'  {name:22s} {size / 1048576:6.1f} MB')


if __name__ == '__main__':
    main()
