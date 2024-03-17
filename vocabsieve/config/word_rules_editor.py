from PyQt5.QtWidgets import QDialog, QFormLayout, QLabel, QPushButton, QPlainTextEdit
import json
import shlex
from ..global_names import settings


class WordRulesEditor(QDialog):
    def __init__(self, parent):
        super().__init__()
        layout = QFormLayout()
        self.setWindowTitle("Edit word preprocessing rules")
        self.parent = parent

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            "# Example rules:\n"
            "# This would 'colour' with 'color', 'honour' with 'honor', etc if no definitions are found\n"
            "# Some characters may need to be escaped with backslashes\n"
            '"our$" "or"'
        )
        data: list[list[str]] = json.loads(settings.value("word_regex", "[]"))
        for rule in data:
            self.editor.appendPlainText(f"{rule[0]} {rule[1]}")

        save_button = QPushButton("Save")
        self.setLayout(layout)
        layout.addRow(QLabel("<h3>Word preprocessing rules</h3>"))
        layout.addRow(QLabel("Enter regex rules to match and replace words, one per line."))
        layout.addRow(QLabel("The rules are applied when no definitions are found, in the order they are listed."))
        layout.addRow(QLabel("Syntax: <item> <replacement>"))
        layout.addRow(self.editor)
        layout.addRow(save_button)
        save_button.clicked.connect(self.saveSettings)

    def saveSettings(self):
        data = self.editor.toPlainText()
        datajson: str = json.dumps([shlex.split(line)[:2]
                                   for line in data.splitlines() if not line.startswith("#") and line.strip()])
        settings.setValue("word_regex", datajson)
