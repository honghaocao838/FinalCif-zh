from qtpy import QtWidgets, QtCore


class ComboBoxWithContextMenu(QtWidgets.QComboBox):
    delete_signal = QtCore.Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def contextMenuEvent(self, event):
        context_menu = QtWidgets.QMenu(self)
        delete_action = context_menu.addAction(f"删除数据块 '{self.currentText()}'")
        action = context_menu.exec(self.mapToGlobal(event.pos()))
        if action == delete_action and self.count() > 1:
            self.delete_signal.emit(self.currentIndex())


def delete_block(index):
    # For testing only
    print(f"'索引为 '{index}' 的数据块已删除。'")


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(window)

    combo_box = ComboBoxWithContextMenu()
    combo_box.addItems(["Item 1", "Item 2", "Item 3"])
    layout.addWidget(combo_box)

    combo_box.delete_signal.connect(delete_block)

    window.show()
    app.exec()
