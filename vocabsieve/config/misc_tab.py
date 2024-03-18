from PyQt5.QtWidgets import (QFormLayout, QCheckBox, QLabel,
                             QSpinBox, QPushButton, QComboBox)
from PyQt5.QtGui import QImageWriter
from PyQt5.QtCore import pyqtSignal
from .base_tab import BaseTab


class MiscTab(BaseTab):
    nuke = pyqtSignal()
    reset = pyqtSignal()

    def initWidgets(self):
        self.capitalize_first_letter = QCheckBox(
            "Capitalize first letter of sentence")
        self.capitalize_first_letter.setToolTip(
            "Capitalize the first letter of clipboard's content before pasting into the sentence field. Does not affect dictionary lookups.")

        self.reset_button = QPushButton("Reset settings")
        self.reset_button.setStyleSheet('QPushButton {color: red;}')
        self.nuke_button = QPushButton("Delete data")
        self.nuke_button.setStyleSheet('QPushButton {color: red;}')

        self.img_format = QComboBox()

        self.img_quality = QSpinBox()

    def setupWidgets(self):
        supported_img_formats = list(map(lambda s: bytes(s).decode(), QImageWriter.supportedImageFormats()))
        self.img_format.addItems(
            ['png', 'jpg', 'gif', 'bmp']
        )
        # WebP requires a plugin, which is commonly but not always installed
        if 'webp' in supported_img_formats:
            self.img_format.addItem('webp')
        self.img_quality.setMinimum(-1)
        self.img_quality.setMaximum(100)
        self.reset_button.clicked.connect(self.reset.emit)
        self.nuke_button.clicked.connect(self.nuke.emit)

    def setupLayout(self):
        layout = QFormLayout(self)
        layout.addRow(self.capitalize_first_letter)
        layout.addRow(QLabel("<h3>Images</h3>"))
        layout.addRow(QLabel("Image format"), self.img_format)
        layout.addRow(QLabel("<i>◊ WebP, JPG, GIF are lossy, which create smaller files.</i>"))
        layout.addRow(QLabel("Image quality"), self.img_quality)
        layout.addRow(QLabel("<i>◊ Between 0 and 100. -1 uses the default value from Qt.</i>"))
        layout.addRow(QLabel("<h3>Reset</h3>"))
        layout.addRow(QLabel("Your data will be lost forever! There is NO cloud backup."))
        layout.addRow(QLabel("<strong>Reset all settings to defaults</strong>"), self.reset_button)
        layout.addRow(QLabel("<strong>Delete all user data</strong>"), self.nuke_button)

    def setupAutosave(self):
        self.register_config_handler(self.capitalize_first_letter, 'capitalize_first_letter', False)
        self.register_config_handler(self.img_format, 'img_format', 'jpg')
        self.register_config_handler(self.img_quality, 'img_quality', -1)
