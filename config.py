from PyQt6.QtWidgets import QDialog, QCheckBox, QVBoxLayout, QLineEdit, QComboBox

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.settings = parent.settings

    def initWidgets(self):
        self.disallow_editing = QCheckBox("Disallow editing")
        self.disallow_editing.clicked.connect(self.sync_settings)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.disallow_editing)

    def sync_settings(self):
        self.settings.setValue("Checked", self.disallow_editing.isChecked())
        self.settings.sync()