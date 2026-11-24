"""Source-level changes that are not plain string replacements.

- bundled check.def is preferred over the one in the home directory
- AlertHelp prepends the Chinese explanation (datafiles/checkdef_zh.json)
- upstream auto-update is disabled (it would replace this localized build)
- finalcif_start loads Qt's own Chinese translation (OK/Cancel/Yes/No)
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def patch(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if new in text:
        print(f'already patched: {rel}')
        return
    if old not in text:
        print(f'PATTERN NOT FOUND: {rel}')
        return
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print(f'patched {rel}')


def main() -> None:
    patch('finalcif/appwindow.py',
          """    def _get_check_def(self) -> None:
        if self.checkdef_file.exists() and file_age_in_days(self.checkdef_file) < 60:""",
          """    def _get_check_def(self) -> None:
        # Prefer the copy shipped with this build: alert help works offline and
        # is not replaced by an English download.
        bundled = application_path / 'datafiles' / 'check.def'
        if bundled.exists():
            self.checkdef = bundled.read_text(encoding='utf-8', errors='ignore').splitlines(keepends=False)
            return
        if self.checkdef_file.exists() and file_age_in_days(self.checkdef_file) < 60:""")

    patch('finalcif/appwindow.py',
          """    def check_for_update_version(self) -> None:
        if os.environ.get('NO_NETWORK'):""",
          """    def check_for_update_version(self) -> None:
        # Chinese edition: the upstream installer would replace this localized
        # build. Updates are published in this repository's Releases.
        return
        if os.environ.get('NO_NETWORK'):""")

    patch('finalcif/cif/checkcif/checkcif.py',
          """    def get_help(self, alert: str) -> str:
        checkdef_help = self._parse_checkdef(alert)
        if not checkdef_help or 'PLAT' not in alert:
            return ''
        return checkdef_help""",
          """    def _load_chinese(self) -> dict:
        zh_file = Path(__file__).resolve().parents[2] / 'datafiles' / 'checkdef_zh.json'
        try:
            return json.loads(zh_file.read_text(encoding='utf-8'))
        except Exception:
            return {}

    def get_help(self, alert: str) -> str:
        checkdef_help = self._parse_checkdef(alert)
        if not checkdef_help or 'PLAT' not in alert:
            return ''
        code = alert[4:] if len(alert) > 4 else alert
        chinese = self._load_chinese().get(code, '')
        if not chinese:
            return checkdef_help
        return f'【中文】\\n{chinese}\\n\\n【English 原文（PLATON check.def）】\\n{checkdef_help}'""")

    patch('finalcif/finalcif_start.py',
          """from qtpy.QtGui import QIcon""",
          """from qtpy.QtCore import QLibraryInfo, QTranslator
from qtpy.QtGui import QIcon""")

    patch('finalcif/finalcif_start.py',
          """def main():
    if not DEBUG:""",
          """def _install_zh_translator() -> None:
    \"\"\"Load Qt's own Chinese texts (OK/Cancel/Yes/No, standard dialogs).\"\"\"
    translator = QTranslator(app)
    path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load('qtbase_zh_CN', path):
        app.installTranslator(translator)
        app._zh_cn_translator = translator


def main():
    if not DEBUG:""")

    patch('finalcif/finalcif_start.py',
          """    app.setQuitOnLastWindowClosed(True)
    w = AppWindow(file=file)""",
          """    _install_zh_translator()
    app.setQuitOnLastWindowClosed(True)
    w = AppWindow(file=file)""")


if __name__ == '__main__':
    main()
