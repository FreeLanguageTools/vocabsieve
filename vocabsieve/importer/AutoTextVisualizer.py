from PyQt5.QtWidgets import QDialog, QListWidget, QVBoxLayout, QListWidgetItem, QLabel
from PyQt5 import QtCore


class AutoTextVisualizer(QDialog):
    def __init__(self, parent, content: list[str]):
        super().__init__(parent)
        self.setWindowTitle("Auto vocab detection")
        self.setMinimumSize(500, 500)
        #textedit = QTextEdit()
        #textedit.setReadOnly(True)
        #textedit.setText(content)
        listwidget = QListWidget()

        for item in content:
            listwidgetitem = QListWidgetItem(item)
            listwidgetitem.setData(QtCore.Qt.UserRole, item)
            listwidget.addItem(listwidgetitem)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Unknown words are enclosed in square brackets."))
        layout.addWidget(listwidget)
        self.setLayout(layout)
