# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'order_ui.ui'
##
##
################################################################################

from qtpy.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from qtpy.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from qtpy.QtWidgets import (QAbstractItemView, QApplication, QGridLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_CifOrderForm(object):
    def setupUi(self, CifOrderForm):
        if not CifOrderForm.objectName():
            CifOrderForm.setObjectName(u"CifOrderForm")
        CifOrderForm.resize(679, 729)
        self.gridLayout = QGridLayout(CifOrderForm)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalSpacer_2 = QSpacerItem(20, 150, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_2, 5, 1, 1, 1)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.moveUpPushButton = QPushButton(CifOrderForm)
        self.moveUpPushButton.setObjectName(u"moveUpPushButton")

        self.verticalLayout.addWidget(self.moveUpPushButton)

        self.moveDownPushButton = QPushButton(CifOrderForm)
        self.moveDownPushButton.setObjectName(u"moveDownPushButton")

        self.verticalLayout.addWidget(self.moveDownPushButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.addKeyPushButton = QPushButton(CifOrderForm)
        self.addKeyPushButton.setObjectName(u"addKeyPushButton")

        self.verticalLayout.addWidget(self.addKeyPushButton)

        self.importCifPushButton = QPushButton(CifOrderForm)
        self.importCifPushButton.setObjectName(u"importCifPushButton")

        self.verticalLayout.addWidget(self.importCifPushButton)

        self.exportToCifPushButton = QPushButton(CifOrderForm)
        self.exportToCifPushButton.setObjectName(u"exportToCifPushButton")

        self.verticalLayout.addWidget(self.exportToCifPushButton)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_5)

        self.saveSettingPushButton = QPushButton(CifOrderForm)
        self.saveSettingPushButton.setObjectName(u"saveSettingPushButton")

        self.verticalLayout.addWidget(self.saveSettingPushButton)

        self.restoreDefaultPushButton = QPushButton(CifOrderForm)
        self.restoreDefaultPushButton.setObjectName(u"restoreDefaultPushButton")

        self.verticalLayout.addWidget(self.restoreDefaultPushButton)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_3)

        self.deleteKeyPushButton = QPushButton(CifOrderForm)
        self.deleteKeyPushButton.setObjectName(u"deleteKeyPushButton")

        self.verticalLayout.addWidget(self.deleteKeyPushButton)


        self.gridLayout.addLayout(self.verticalLayout, 4, 1, 1, 1)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_4, 3, 1, 1, 1)

        self.cifOrderTableWidget = QTableWidget(CifOrderForm)
        if (self.cifOrderTableWidget.columnCount() < 1):
            self.cifOrderTableWidget.setColumnCount(1)
        __qtablewidgetitem = QTableWidgetItem()
        self.cifOrderTableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        self.cifOrderTableWidget.setObjectName(u"cifOrderTableWidget")
        self.cifOrderTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cifOrderTableWidget.setProperty(u"showDropIndicator", False)
        self.cifOrderTableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cifOrderTableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cifOrderTableWidget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.cifOrderTableWidget.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.cifOrderTableWidget.horizontalHeader().setStretchLastSection(True)
        self.cifOrderTableWidget.verticalHeader().setVisible(False)

        self.gridLayout.addWidget(self.cifOrderTableWidget, 2, 0, 4, 1)

        self.helpTextLabel = QLabel(CifOrderForm)
        self.helpTextLabel.setObjectName(u"helpTextLabel")
        self.helpTextLabel.setWordWrap(True)

        self.gridLayout.addWidget(self.helpTextLabel, 1, 0, 1, 2)


        self.retranslateUi(CifOrderForm)
    # setupUi

    def retranslateUi(self, CifOrderForm):
        CifOrderForm.setWindowTitle(QCoreApplication.translate("CifOrderForm", "CIF 键顺序", None))
        self.moveUpPushButton.setText(QCoreApplication.translate("CifOrderForm", "上移", None))
        self.moveDownPushButton.setText(QCoreApplication.translate("CifOrderForm", "下移", None))
#if QT_CONFIG(whatsthis)
        self.addKeyPushButton.setWhatsThis(QCoreApplication.translate("CifOrderForm", "将一个或多个 CIF 关键字添加到列表。", None))
#endif // QT_CONFIG(whatsthis)
        self.addKeyPushButton.setText(QCoreApplication.translate("CifOrderForm", "添加键", None))
#if QT_CONFIG(whatsthis)
        self.importCifPushButton.setWhatsThis(QCoreApplication.translate("CifOrderForm", "<html><head/><body><p>导入 CIF 中关键字的顺序决定了列表中各项的顺序，从而决定 FinalCif 输出 CIF 中的顺序。</p></body></html>", None))
#endif // QT_CONFIG(whatsthis)
        self.importCifPushButton.setText(QCoreApplication.translate("CifOrderForm", "从 CIF 导入顺序 ", None))
        self.exportToCifPushButton.setText(QCoreApplication.translate("CifOrderForm", "将顺序导出到 CIF", None))
        self.saveSettingPushButton.setText(QCoreApplication.translate("CifOrderForm", "永久保存", None))
        self.restoreDefaultPushButton.setText(QCoreApplication.translate("CifOrderForm", "恢复默认顺序", None))
        self.deleteKeyPushButton.setText(QCoreApplication.translate("CifOrderForm", "删除所选键", None))
        ___qtablewidgetitem = self.cifOrderTableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("CifOrderForm", "CIF 键", None))
        self.helpTextLabel.setText(QCoreApplication.translate("CifOrderForm", "输出文件中 CIF 关键字的顺序。勾选表示强制保留在输出 CIF 中。", None))
    # retranslateUi

