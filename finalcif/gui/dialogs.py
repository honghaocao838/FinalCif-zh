from __future__ import annotations

import os
import re
import sys
import threading
import traceback
from pathlib import Path

from qtpy import QtCore, compat
from qtpy import QtWidgets
from qtpy.QtCore import QProcess
from qtpy.QtWidgets import QApplication, QWidget
from qtpy.QtWidgets import QMessageBox, QMainWindow, QVBoxLayout, QTextEdit, QPushButton, QFrame, QProgressDialog

from finalcif import VERSION
from finalcif.tools.misc import running_inside_unit_test
from finalcif.tools.selfupdate import ElevationRefused, UpdateCancelled, UpdateError, can_self_update, \
    download_installer, start_exit_watchdog, start_installer, start_user_installer, user_installation_directory

# Keeps the running downloads alive, a local variable would be garbage collected:
_running_updates: set = set()
# The same for a message box without a parent:
_open_message_boxes: set = set()


class InstallerDownload:
    """Downloads the FinalCif installer in a background thread.

    Not a single Qt object is touched from that thread; the GUI polls the state of the
    download with a timer instead (see :func:`update_installation`).
    """

    def __init__(self, version: str) -> None:
        self.version = version
        self.setup_file: Path | None = None
        self.error = ''
        self.finished = False
        self._lock = threading.Lock()
        self._received = 0
        self._total = 0
        self._cancelled = False

    def start(self) -> None:
        threading.Thread(target=self.run, daemon=True).start()

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def progress(self) -> tuple[int, int]:
        with self._lock:
            return self._received, self._total

    def _report_progress(self, received: int, total: int) -> None:
        with self._lock:
            self._received = received
            self._total = total

    def run(self) -> None:
        try:
            self.setup_file = download_installer(self.version,
                                                 progress=self._report_progress,
                                                 should_cancel=lambda: self._cancelled)
        except UpdateCancelled:
            pass
        except UpdateError as err:
            self.error = str(err)
        except Exception as err:  # The dialog would wait forever for a thread that died:
            traceback.print_exc()
            self.error = f'安装程序无法下载：\n{err!r}'
        finally:
            self.finished = True


def do_update_program(version: str, parent: QWidget | None = None) -> None:
    if can_self_update():
        update_installation(version, parent)
    else:
        print('No update available.')


def update_installation(version: str, parent: QWidget | None = None) -> None:
    """Download the installer and hand the installation directory over to it."""
    progress_dialog = QProgressDialog("正在下载 FinalCif 安装程序…", "取消", 0, 100, parent)
    progress_dialog.setWindowTitle("FinalCif 更新")
    progress_dialog.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
    progress_dialog.setAutoClose(False)
    progress_dialog.setAutoReset(False)
    progress_dialog.setMinimumDuration(0)
    progress_dialog.setValue(0)
    downloader = InstallerDownload(version)
    # Everything below runs in the GUI thread, driven by this timer:
    timer = QtCore.QTimer(progress_dialog)
    timer.setInterval(200)
    # Plain local variables would be garbage collected while the thread is downloading:
    running_update = (downloader, progress_dialog)

    def show_progress() -> None:
        received, total = downloader.progress
        if total:
            progress_dialog.setRange(0, 100)
            progress_dialog.setValue(int(100 * received / total))
        elif received:
            # Without a content-length there is nothing to calculate a percentage from:
            progress_dialog.setRange(0, 0)
        if received and received == total:
            progress_dialog.setLabelText("正在校验下载的安装程序…")
        else:
            progress_dialog.setLabelText(f'Downloading the FinalCif installer... '
                                         f'({received / 1024 ** 2:.1f}" MB）"')

    def on_failed(message: str) -> None:
        progress_dialog.close()
        show_general_warning(parent, warn_text="更新失败。", info_text=message,
                             window_title="FinalCif 更新")

    def on_downloaded(setup_file: Path) -> None:
        progress_dialog.setLabelText("正在关闭 FinalCif 以进行安装…")
        progress_dialog.setRange(0, 100)
        progress_dialog.setValue(100)
        QApplication.processEvents()
        release_installation_directory()
        try:
            start_installer(setup_file)
        except ElevationRefused as err:
            progress_dialog.close()
            if not install_into_user_directory(setup_file, str(err), parent):
                return
        except UpdateError as err:
            on_failed(str(err))
            return
        progress_dialog.close()
        quit_application()

    def check_download() -> None:
        show_progress()
        if not downloader.finished:
            return
        timer.stop()
        _running_updates.discard(running_update)
        if downloader.error:
            on_failed(downloader.error)
        elif downloader.setup_file is not None:
            on_downloaded(downloader.setup_file)
        else:
            progress_dialog.close()

    timer.timeout.connect(check_download)
    progress_dialog.canceled.connect(downloader.cancel)
    _running_updates.add(running_update)
    downloader.start()
    progress_dialog.show()
    timer.start()


def install_into_user_directory(setup_file: Path, reason: str, parent: QWidget | None = None) -> bool:
    """Offer the per-user installation to accounts without administrator rights."""
    question = QMessageBox(parent)
    question.setWindowTitle("FinalCif 更新")
    question.setIcon(QMessageBox.Icon.Question)
    question.setText("也可以将 FinalCif 安装到你的个人文件夹中。")
    question.setInformativeText(f'{reason}\n\n'
                                f'是否改为将 FinalCif 安装到\n{user_installation_directory()}？\n'
                                f'这不需要管理员权限。\n\n'
                                f'当前安装保持不变。之后请从你的个人开始菜单启动新的 FinalCif。')
    question.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    question.setDefaultButton(QMessageBox.StandardButton.Yes)
    if question.exec() != QMessageBox.StandardButton.Yes:
        return False
    try:
        start_user_installer(setup_file)
    except UpdateError as err:
        show_general_warning(parent, warn_text="更新失败。", info_text=str(err),
                             window_title="FinalCif 更新")
        return False
    return True


def release_installation_directory() -> None:
    """Kill child processes like PLATON, they lock their executable in the installation dir."""
    app = QApplication.instance()
    if app is None:
        return
    for widget in app.topLevelWidgets():
        for process in widget.findChildren(QProcess):
            if process.state() != QProcess.ProcessState.NotRunning:
                process.kill()
                process.waitForFinished(3000)


def quit_application() -> None:
    """Leave FinalCif so that the installer can replace all files."""
    start_exit_watchdog()
    app = QApplication.instance()
    if app is None:
        os._exit(0)
    app.closeAllWindows()
    app.quit()


def unable_to_open_message(parent: QWidget | None, filepath: Path, not_ok: Exception) -> None:
    """
    Shows a message if the current cif file can not be opened.
    """
    if running_inside_unit_test():
        print('DBG> Running inside a pytest -> not showing error message.')
        return
    info = QMessageBox(parent=parent)
    info.setIcon(QMessageBox.Icon.Information)
    print('Output from gemmi:', not_ok)
    try:
        line = str(not_ok)[4:].split(':')[1]
    except IndexError:
        line = None
    info.setText("此 cif 文件无法读取！                                           ")
    if line:
        try:
            int(line)
            info.setInformativeText(f'\n请检查第 {line} 行\n{filepath.name}')
        except ValueError:
            info.setInformativeText(f'"{filepath.name}"\n{not_ok}')
    else:
        info.setInformativeText(f'"{filepath.name}"\n{not_ok}')
    info.setModal(True)
    info.show()


def show_res_checksum_warning(parent: QWidget | None) -> None:
    """
    A message box to display if the checksums do not agree.
    """
    if running_inside_unit_test():
        print('DBG> Running inside a pytest -> not showing error message.')
        return
    info = QMessageBox(parent=parent)
    info.setIcon(QMessageBox.Icon.Warning)
    info.setText("\"_shelx_res_checksum\" 与 .res 文件内容不一致！\n\n此错误可能源于 SHELX 文件中的非 ASCII 字符（如德文变音字母）。")
    info.setModal(True)
    info.show()


def show_hkl_checksum_warning(parent: QWidget | None) -> None:
    """
    A message box to display if the checksums do not agree.
    """
    if running_inside_unit_test():
        print('DBG> Running inside a pytest -> not showing error message.')
        return
    info = QMessageBox(parent=parent)
    info.setIcon(QMessageBox.Icon.Warning)
    info.setText("\"_shelx_hkl_checksum\" 与\n.hkl 文件内容不一致！")
    info.setModal(True)
    info.show()


def show_general_warning(parent: QWidget | None, warn_text: str = '', info_text: str = '', window_title=' ') -> None:
    """
    A message box to display if the checksums do not agree.
    warn_text is displayed bold.
    info_text is displayed regular.
    """
    if not warn_text:
        return None
    if running_inside_unit_test():
        print(f'DBG> Running inside a pytest -> not showing error message:\n{warn_text}\n{info_text}')
        return None
    box = QMessageBox(parent=parent)
    box.setTextFormat(QtCore.Qt.TextFormat.AutoText)
    box.setWindowTitle(window_title)
    box.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextBrowserInteraction)
    box.setText(warn_text)
    box.setModal(True)
    if info_text:
        box.setInformativeText(info_text)
        box.setStyleSheet("QLabel{min-width:600 px; font-size: 14px;}")
    box.show()
    if parent is None:
        box.exec()
        box.close()


_CJK_RE = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff]')
_CJK_ANY_RE = re.compile(r'[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]')
_PRE_RE = re.compile(r'(<pre>)(.*?)(</pre>)', re.DOTALL)


def _is_help_code_line(line: str) -> bool:
    """Whether a line inside <pre> is code/formula/example, not prose."""
    stripped = line.strip()
    if not stripped:
        return False
    if '<h2>' in line or '</h2>' in line or '<h3>' in line:
        return True
    if line.startswith('    '):
        return True
    if re.search(r'[=^~|]', stripped):
        return True
    if re.search(r'\s{3,}', stripped):
        return True
    if re.match(r'^[-*+]\s', stripped) or re.match(r'^\d+[.)]\s', stripped):
        return True
    if not _CJK_ANY_RE.search(stripped):
        return True
    return False


def _join_help_prose(parts: list[str]) -> str:
    """Join Chinese prose lines, keeping a space where Chinese meets ASCII."""
    def is_ascii_word(char: str) -> bool:
        return char.isascii() and (char.isalnum() or char == '_')

    def needs_space(left: str, right: str) -> bool:
        left_ascii, right_ascii = is_ascii_word(left), is_ascii_word(right)
        left_cjk, right_cjk = bool(_CJK_RE.match(left)), bool(_CJK_RE.match(right))
        return (left_ascii and right_ascii) or (left_cjk and right_ascii) or (left_ascii and right_cjk)

    joined = ''
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if joined and needs_space(joined[-1], part[0]):
            joined += ' '
        joined += part
    return joined


def _reflow_pre_body(body: str) -> str:
    """Undo the English line wrapping of translated dictionary prose.

    Formulas, examples and table-like lines keep their line breaks; ordinary
    Chinese sentences are joined so that the help window wraps them naturally.
    """
    out: list[str] = []
    buffer: list[str] = []
    in_example = False

    def flush() -> None:
        if buffer:
            joined = _join_help_prose(buffer)
            if joined:
                out.append(joined)
            buffer.clear()

    for line in body.splitlines():
        header = re.match(r'^(\s*<h2>.*?</h2>)(.*)$', line, re.DOTALL)
        if header:
            flush()
            out.append(header.group(1).strip())
            remainder = header.group(2)
            if remainder.strip():
                buffer.append(remainder)
            continue
        if '<h3>' in line:
            flush()
            in_example = True
            out.append(line.rstrip())
            continue
        if in_example:
            out.append(line.rstrip())
            continue
        if not line.strip():
            flush()
            if out and out[-1] != '':
                out.append('')
            continue
        if _is_help_code_line(line):
            flush()
            out.append(line.rstrip())
        else:
            buffer.append(line)
    flush()
    return '\n'.join(out)


def reflow_help_html(helptext: str) -> str:
    """Reflow Chinese <pre> prose without touching formulas or examples."""
    if '<pre>' not in helptext or not _CJK_RE.search(helptext):
        return helptext

    def replace(match: re.Match) -> str:
        body = match.group(2)
        if not _CJK_RE.search(body):
            return match.group(0)
        # <pre> never wraps.  pre-wrap keeps formula/example line breaks but
        # lets the joined Chinese prose wrap to the help window width.
        return ('<div style="white-space: pre-wrap; font-family: monospace; line-height: 150%;">'
                + _reflow_pre_body(body) + '</div>')

    return _PRE_RE.sub(replace, helptext)


def show_keyword_help(parent: QWidget | None, helptext: str, title: str = ''):
    """
    A window to display help texts from the CIF dictionaries.
    """
    helptext = reflow_help_html(helptext)
    nlines = len(helptext.splitlines())
    window = QMainWindow(parent=parent)
    window.setWindowTitle(title)

    def close_window(event) -> None:
        if event.key() == QtCore.Qt.Key.Key_Escape:
            window.close()

    window.keyPressEvent = close_window
    widget = QFrame()
    layout = QVBoxLayout()
    button = QPushButton("关闭")
    textedit = QTextEdit()
    textedit.setReadOnly(True)
    help_font = textedit.font()
    help_font.setFamily('monospace')
    help_font.setPointSize(12)
    textedit.setFont(help_font)
    textedit.setText(helptext)
    textedit.document().setDocumentMargin(10)
    layout.addWidget(textedit)
    layout.addWidget(button)
    widget.setLayout(layout)
    window.setCentralWidget(widget)
    width = textedit.fontMetrics().horizontalAdvance('X' * 70)
    height = textedit.fontMetrics().horizontalAdvance('X' * nlines)
    textedit.setMinimumWidth(max([600, width]))
    textedit.setMinimumHeight(max([400, height]))
    window.move(300, 100)
    window.show()
    button.clicked.connect(window.close)


def show_ok_cancel_warning(parent: QWidget | None, warn_text: str = '') -> bool:
    box = QMessageBox(parent=parent)
    box.setTextFormat(QtCore.Qt.TextFormat.AutoText)
    box.setWindowTitle(" ")
    box.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextBrowserInteraction)
    box.setText(warn_text)
    box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
    box.setDefaultButton(QMessageBox.StandardButton.Ok)
    box.setModal(True)
    box.show()
    return box.result() == QMessageBox.StandardButton.Ok


def show_update_warning(parent: QWidget | None, remote_version: int = 0) -> None:
    """
    A message box to display if the checksums do not agree.
    """
    warn_text = "FinalCif 有新版本 {} 可用，下载地址：<br><a href='https://dkratzert.de/finalcif.html'>https://dkratzert.de/finalcif.html</a>"
    box = QMessageBox(parent)
    box.setTextFormat(QtCore.Qt.TextFormat.AutoText)
    box.setWindowTitle("FinalCif 更新")
    box.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextBrowserInteraction)
    if sys.platform.startswith("win"):
        warn_text += "<br><br>现在更新将结束所有正在运行的 FinalCIF 程序！"
        update_button = box.addButton("立即更新", QMessageBox.ButtonRole.AcceptRole)
        update_button.clicked.connect(lambda: do_update_program(str(remote_version), parent))
    box.setText(warn_text.format(remote_version))
    box.setModal(True)
    _open_message_boxes.add(box)
    box.finished.connect(lambda _: _open_message_boxes.discard(box))
    box.show()
    # The main window is shown right after this box during startup and covers it otherwise:
    box.raise_()
    box.activateWindow()


def bad_z_message(parent: QWidget | None, z: float) -> None:
    zinfo = QMessageBox(parent)
    zinfo.setIcon(QMessageBox.Icon.Information)
    zinfo.setText(f'分子式单位数 Z={z:.0f} is probably wrong.\n'
                  f'You may restart refinement with a correct value.')
    zinfo.setModal(True)
    zinfo.show()


def show_bug_found_warning(logfile) -> None:
    window = QMainWindow()
    title = "恭喜，你在 FinalCif 中发现了一个 bug！"
    text = (f'<br>请将文件 <br>'
            f'<a href={logfile.resolve()}>{logfile.resolve()}</a> '
            f'<br>发送给 Daniel Kratzert：  '
            f'<a href="mailto:dkratzert@gmx.de?subject=FinalCif version {VERSION} crash report">'
            f'dkratzert@gmx.de</a><br>'
            f'<br>如有可能，也请附上对应的 CIF 文件。'
            f'<br><br><b>Honghao Cao 汉化，问题请联系 honghaocao838@gmail.com（汉化自 FinalCif v180）</b>')
    box = QMessageBox(parent=window)
    box.setWindowTitle("警告")
    box.setText(title)
    box.setInformativeText(text)
    box.setTextFormat(QtCore.Qt.TextFormat.RichText)
    box.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextBrowserInteraction)
    box.exec()
    window.show()


def show_yes_now_question(title: str, question: str, parent: QWidget | None = None) -> bool:
    response = QMessageBox.question(parent, title, question,
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)
    if response == QMessageBox.StandardButton.Yes:
        return True
    else:
        return False


def cif_file_open_dialog(parent: QWidget | None = None, filter: str = "CIF 文件 (*.cif)", last_dir='', options=None) -> str:
    """
    Returns a cif file name from a file dialog.
    """
    filename, _ = compat.getopenfilename(parent=parent,
                                         caption="打开 .cif 文件",
                                         basedir=last_dir,
                                         filters=filter,
                                         selectedfilter=filter,
                                         options=options
                                         )
    return filename


def cif_file_save_dialog(filename: str, parent: QWidget | None = None) -> str:
    """
    Returns a cif file name from a file dialog.
    """
    filter = "CIF 文件 (*.cif)"
    filename, _ = compat.getsavefilename(parent=parent,
                                         filters=filter,
                                         caption="保存 .cif 文件",
                                         selectedfilter=filter)
    return filename


def fcf_file_open_dialog(parent: QWidget | None = None, last_dir: str = '', options=None) -> str:
    """
    Returns the name of a structure factor file from a file dialog.
    """
    file_filter = "结构因子文件 (*.fcf)"
    filename, _ = compat.getopenfilename(parent=parent,
                                         caption="选择此 CIF 对应的结构因子 (.fcf) 文件",
                                         basedir=last_dir,
                                         filters=file_filter,
                                         selectedfilter=file_filter,
                                         options=options
                                         )
    return filename


def video_file_open_dialog(parent: QWidget | None = None, filter: str = "视频文件 (*.vzs; *.jpg)", last_dir='',
                           options=None) -> str:
    filename, _ = compat.getopenfilename(parent=parent,
                                         caption="打开晶体视频文件",
                                         basedir=last_dir,
                                         filters=filter,
                                         selectedfilter=filter,
                                         options=options
                                         )
    return filename


if __name__ == '__main__':
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    window = QtWidgets.QMainWindow()
    w = QtWidgets.QWidget()
    window.setCentralWidget(w)
    l = QtWidgets.QVBoxLayout()
    w.setLayout(l)
    # answer = show_yes_now_question(title='Delete templates', question='Fobar?', parent=w)
    # bad_z_message(parent=w, z=3.0)
    # show_update_warning(parent=w, remote_version=123)
    # show_bug_found_warning(Path(r'test.txt'))
    # show_ok_cancel_warning(parent=w, warn_text='foobar')
    # show_keyword_help(parent=w, helptext="This is a helptext", title='A Title')
    # show_general_warning(parent=w, warn_text='Warning text', info_text='Info text', window_title='Title')
    # show_hkl_checksum_warning(parent=w)
    # show_res_checksum_warning(parent=w)
    unable_to_open_message(parent=w, not_ok=Exception('foo'), filepath=Path('C:/foo.txt'))
    # do_update_program('170')
    w.show()

    app.exec()
