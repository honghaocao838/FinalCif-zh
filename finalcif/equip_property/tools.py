import gemmi.cif
from gemmi import cif

from finalcif.gui.dialogs import show_general_warning


def read_document_from_cif_file(filename: str) -> gemmi.cif.Document | None:
    doc: gemmi.cif.Document | None = None
    try:
        doc = cif.read_file(filename)
    except (RuntimeError, ValueError) as e:
        warning = "{}\n{}".format("此 CIF 无效：", str(e))
        if 'data_' in str(e):
            warning = f"{warning}\n\nCIF 必须以 'data_[some_name]' 开头。"
        show_general_warning(parent=None, warn_text=warning)
    except OSError as e:
        show_general_warning(parent=None, warn_text=f'无法打开文件 {filename}:\n{e!s}')
    return doc
