"""Patch message fragments that the bulk translator cannot splice safely."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PATCHES = [
    ('finalcif/report/templated_report.py',
     '''                                 warn_text=f'"文档 "{output_filename} could not be opened to write the report.\\n'
                                           f'Is the file already opened?')''',
     '''                                 warn_text=f'文档 {output_filename} 无法打开以写入报告。\\n'
                                           f'该文件是否已被打开？')'''),

    ('finalcif/appwindow.py',
     '''                                 f'文档 {report_filename.name} could not be opened to '
                                 f'write the report.\\nIs the file already opened?')''',
     '''                                 f'文档 {report_filename.name} 无法打开以写入报告。\\n'
                                 f'该文件是否已被打开？')'''),

    ('finalcif/cif/checkcif/checkcif.py',
     '''                show_general_warning(self, f'"文档 "{pdfobj.name} could not be opened to '
                                           f'write the report.\\nIs the file already opened?')''',
     '''                show_general_warning(self, f'文档 {pdfobj.name} 无法打开以写入报告。\\n'
                                           f'该文件是否已被打开？')'''),

    ('finalcif/datafiles/bruker_data.py',
     """            show_general_warning(self.app, '<b>Warning of impossible temperature specification</b>:<br>'
                                           'You probably entered &minus;273.15 °C instead '
                                           'of &minus;173.15 °C into the SHELX instruction file.<br>'
                                           'A temperature of 0 K is likely to be wrong.')""",
     """            show_general_warning(self.app, '<b>温度设定不可能</b>：<br>'
                                           '你可能在 SHELX 指令文件中输入了 −273.15 °C，'
                                           '而不是 −173.15 °C。<br>'
                                           '0 K 的温度很可能是错的。')"""),

    ('finalcif/datafiles/bruker_data.py',
     """                                 f'<b>Warning</b>: The temperature from the measurement and from SHELX '
                                 f'differ. Please double-check for correctness.'
                                 f'<br><br>SHELX says: {self.cif["_diffrn_ambient_temperature"].split("(")[0]} K'
                                 f'<br>The P4P file says: {temp2} {"K" if temp2 else ""}<br>Frame header says: '
                                 f'{temp1} {"K" if temp2 else ""}<br><br>You may add a '
                                 f'<a href="http://shelx.uni-goettingen.de/shelxl_html.php#TEMP">TEMP</a> '
                                 f'instruction to your SHELX file (in °C).')""",
     """                                 f'<b>警告</b>：测量温度与 SHELX 中的温度不一致，请核实。'
                                 f'<br><br>SHELX：{self.cif["_diffrn_ambient_temperature"].split("(")[0]} K'
                                 f'<br>P4P 文件：{temp2} {"K" if temp2 else ""}<br>帧头：'
                                 f'{temp1} {"K" if temp2 else ""}<br><br>可以在 SHELX 文件中加入 '
                                 f'<a href="http://shelx.uni-goettingen.de/shelxl_html.php#TEMP">TEMP</a> '
                                 f'指令（单位为 °C）。')"""),

    ('finalcif/datafiles/bruker_data.py',
     """            return (f'"计算自 "{source_path(self.cif.fileobj)} '
                    f'(singles of twin component {self._reference_domain()}, '
                    f'merged in {self.cif.space_group})')""",
     """            return (f'计算自 {source_path(self.cif.fileobj)} '
                    f'（孪晶分量 {self._reference_domain()}，'
                    f'合并于 {self.cif.space_group}）')"""),

    ('finalcif/datafiles/bruker_data.py',
     """            return (f'{source}"（孪晶分量 "{statistics.component}, '
                    f'point group {dataset.equivalents_point_group})')""",
     """            return (f'{source}（孪晶分量 {statistics.component}，'
                    f'点群 {dataset.equivalents_point_group}）')"""),

    ('finalcif/cif/cod/deposit.py',
     """            f'Starting deposition of {self.cif.fileobj.name} in "{deposition_type}" mode ...'""",
     """            f'正在提交 {self.cif.fileobj.name}（模式 "{deposition_type}"）…'"""),

    ('finalcif/equip_property/author_loop_templates.py',
     """                show_general_warning(self.app, f'A template named "{new_name}" already exists.')""",
     """                show_general_warning(self.app, f'名为 "{new_name}" 的模板已存在。')"""),

    ('finalcif/equip_property/equipment.py',
     """                show_general_warning(self.app, f'A template named "{new_name}" already exists.')""",
     """                show_general_warning(self.app, f'名为 "{new_name}" 的模板已存在。')"""),
]


def main() -> None:
    for rel, old, new in PATCHES:
        path = ROOT / rel
        text = path.read_text(encoding='utf-8')
        if new in text:
            print(f'already patched: {rel}')
            continue
        if old not in text:
            print(f'PATTERN NOT FOUND: {rel}')
            continue
        path.write_text(text.replace(old, new, 1), encoding='utf-8')
        print(f'patched {rel}')


if __name__ == '__main__':
    main()
