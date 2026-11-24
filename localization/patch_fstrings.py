"""One-off patches for messages that are split across f-string literals.

The bulk translator (apply_translations.py) cannot splice those safely, so they
are rewritten here as whole, natural Chinese sentences.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PATCHES = [
    ('finalcif/appwindow.py',
     """                                                           f'Previous changes from a former FinalCif session '
                                                           f'were found in\\n{self.finalcif_changes_filename.name}.\\n\\n'
                                                           'Do you wish to reload them?',""",
     """                                                           f'发现先前 FinalCif 会话的更改，'
                                                           f'位于 {self.finalcif_changes_filename.name}。\\n\\n'
                                                           '是否重新加载？',"""),

    ('finalcif/appwindow.py',
     """                                 info_text=f'The file "{Path(self.cif.doc.source)}" has invalid '
                                           f'characters in line(s)'
                                           f' {", ".join([str(x + 1) for x in nums])}.'
                                           '\\n\\nOnly ascii characters are allowed.')""",
     """                                 info_text=(f'文件 "{Path(self.cif.doc.source)}" 在以下行中包含无效字符：'
                                            f' {", ".join([str(x + 1) for x in nums])}。'
                                            '\\n\\n只允许 ASCII 字符。'))"""),

    ('finalcif/appwindow.py',
     """                                 info_text=f'Data block name "<b>{cif2.block.name}</b>" '
                                           f'already present in current CIF!')""",
     """                                 info_text=f'数据块名称 "<b>{cif2.block.name}</b>" '
                                           f'已存在于当前 CIF 中！')"""),

    ('finalcif/appwindow.py',
     """            show_general_warning(self, f'"{blockname}" is not a valid cif keyword.')""",
     """            show_general_warning(self, f'"{blockname}" 不是有效的 cif 关键字。')"""),

    ('finalcif/gui/dialogs.py',
     """    text = (f'<br>Please send the file <br>'
            f'<a href={logfile.resolve()}>{logfile.resolve()}</a> '
            f'<br>to Daniel Kratzert:  '
            f'<a href="mailto:dkratzert@gmx.de?subject=FinalCif version {VERSION} crash report">'
            f'dkratzert@gmx.de</a><br>'
            f'<br>If possible, the corresponding CIF file is also desired.')""",
     """    text = (f'<br>请将文件 <br>'
            f'<a href={logfile.resolve()}>{logfile.resolve()}</a> '
            f'<br>发送给 Daniel Kratzert：  '
            f'<a href="mailto:dkratzert@gmx.de?subject=FinalCif version {VERSION} crash report">'
            f'dkratzert@gmx.de</a><br>'
            f'<br>如有可能，也请附上对应的 CIF 文件。'
            f'<br><br><b>H.C 汉化，问题请联系 honghaocao838@gmail.com（汉化自 FinalCif v180）</b>')"""),

    ('finalcif/gui/dialogs.py',
     """    question.setInformativeText(f'{reason}\\n\\n'
                                f'Install FinalCif into\\n{user_installation_directory()}\\ninstead? '
                                f'This needs no administrator rights.\\n\\n'
                                f'The current installation stays where it is. Start the new FinalCif '
                                f'from your personal start menu entry afterwards.')""",
     """    question.setInformativeText(f'{reason}\\n\\n'
                                f'是否改为将 FinalCif 安装到\\n{user_installation_directory()}？\\n'
                                f'这不需要管理员权限。\\n\\n'
                                f'当前安装保持不变。之后请从你的个人开始菜单启动新的 FinalCif。')"""),

    ('finalcif/gui/import_selector.py',
     """        self.ui.importInfoLabel.setText(f"'正在导入\\n'{self.import_cif.fileobj}\\n\\n"
                                        f"The CIF to import contains {self.keys_to_import} keys "
                                        f"and {self.loops_to_import}' 个循环，其中 '"
                                        f"{len(self.get_keys(include=True)) + len(self.get_loops(include=True))} "
                                        f"are selected for import.")""",
     """        self.ui.importInfoLabel.setText(f'正在导入\\n{self.import_cif.fileobj}\\n\\n'
                                        f'要导入的 CIF 包含 {self.keys_to_import} 个键'
                                        f'和 {self.loops_to_import} 个循环，其中 '
                                        f'{len(self.get_keys(include=True)) + len(self.get_loops(include=True))} '
                                        f'已选中用于导入。')"""),

    ('finalcif/gui/block_combobox.py',
     """        delete_action = context_menu.addAction(f"Delete block '{self.currentText()}'")""",
     """        delete_action = context_menu.addAction(f"删除数据块 '{self.currentText()}'")"""),

    ('finalcif/gui/spell_check_edit.py',
     """            learn_action = QtGui.QAction(f"Learn '{text}'", parent=menu)""",
     """            learn_action = QtGui.QAction(f"学习 '{text}'", parent=menu)"""),

    ('finalcif/equip_property/properties.py',
     """                show_general_warning(self.app, f'A template named "{new_name}" already exists.')""",
     """                show_general_warning(self.app, f'名为 "{new_name}" 的模板已存在。')"""),

    ('finalcif/equip_property/properties.py',
     """            show_general_warning(self.app, f'"{cif_key}" is not a valid cif keyword.')""",
     """            show_general_warning(self.app, f'"{cif_key}" 不是有效的 cif 关键字。')"""),

    ('finalcif/equip_property/equipment.py',
     """                                         f'"{key}" is not a valid keyword! \\n'
                                         f'Change the name in order to save.\\n'
                                         f'Keys must start with an underscore.')""",
     """                                         f'"{key}" 不是有效关键字！\\n'
                                         f'请修改名称后再保存。\\n'
                                         f'键必须以底线开头。')"""),

    ('finalcif/equip_property/equipment.py',
     """                show_general_warning(self.app, f'"{key}" is not an official CIF keyword!')""",
     """                show_general_warning(self.app, f'"{key}" 不是官方 CIF 关键字！')"""),

    ('finalcif/equip_property/tools.py',
     """            warning = f"{warning}\\n\\nA CIF needs to start with 'data_[some_name]'." """.rstrip(),
     """            warning = f"{warning}\\n\\nCIF 必须以 'data_[some_name]' 开头。" """.rstrip()),
]

TEXT_PATCHES = [
    ('finalcif/equip_property/equipment.py',
     """                show_general_warning(self.app, f'A template named "{new_name}" already exists.')""",
     """                show_general_warning(self.app, f'名为 "{new_name}" 的模板已存在。')""", 2),
    ('finalcif/tools/selfupdate.py',
     """                               'can only be updated with administrator rights, which were not granted.')""",
     """                               '只能在获得管理员权限的情况下更新，但权限未获批准。')""", 2),
]


def main() -> None:
    for rel, old, new, *rest in PATCHES + TEXT_PATCHES:
        path = ROOT / rel
        text = path.read_text(encoding='utf-8')
        count = rest[0] if rest else 1
        found = text.count(old)
        if found < count:
            print(f'SKIP {rel}: pattern not found ({found}/{count})')
            continue
        path.write_text(text.replace(old, new, count), encoding='utf-8')
        print(f'patched {rel} ({count})')


if __name__ == '__main__':
    main()
