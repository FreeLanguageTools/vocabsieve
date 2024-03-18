from PyQt5.QtWidgets import (QFormLayout, QCheckBox, QLabel, QLineEdit,
                             QSpinBox)
from .base_tab import BaseTab


class NetworkTab(BaseTab):
    def initWidgets(self):
        self.check_updates = QCheckBox("Check for updates")
        self.reader_enabled = QCheckBox("Enable VocabSieve Web Reader")
        self.reader_host = QLineEdit()
        self.reader_port = QSpinBox()
        self.gtrans_api = QLineEdit()
        #self.api_enabled = QCheckBox("Enable VocabSieve local API")
        #self.api_host = QLineEdit()
        #self.api_port = QSpinBox()
        #self.api_port.setMinimum(1024)
        #self.api_port.setMaximum(49151)

    def setupWidgets(self):
        self.reader_port.setMinimum(1024)
        self.reader_port.setMaximum(49151)

    def setupLayout(self):
        layout = QFormLayout(self)
        layout.addRow(QLabel(
            '<h3>Network settings</h3>'
            '◊ All settings on this tab require a restart to take effect.'
            '<br>◊ Most users should not need to change these settings.</i>'
        ))
        layout.addRow(self.check_updates)
        #layout.addRow(QLabel("<h4>Local API</h4>"))
        #layout.addRow(self.api_enabled)
        #layout.addRow(QLabel("API host"), self.api_host)
        #layout.addRow(QLabel("API port"), self.api_port)
        layout.addRow(QLabel("<h4>Web Reader</h4>"))
        layout.addRow(self.reader_enabled)
        layout.addRow(QLabel("Web reader host"), self.reader_host)
        layout.addRow(QLabel("Web reader port"), self.reader_port)
        layout.addRow(QLabel("Google Translate API"), self.gtrans_api)

    def setAvailable(self):
        #self.api_host.setEnabled(self.api_enabled.isChecked())
        #self.api_port.setEnabled(self.api_enabled.isChecked())
        self.reader_host.setEnabled(self.reader_enabled.isChecked())
        self.reader_port.setEnabled(self.reader_enabled.isChecked())

    def setupAutosave(self):
        self.register_config_handler(self.check_updates, 'check_updates', False, True)

        #self.api_enabled.clicked.connect(self.setAvailable)
        self.reader_enabled.clicked.connect(self.setAvailable)

        #self.register_config_handler(self.api_enabled, 'api_enabled', True)
        #self.register_config_handler(self.api_host, 'api_host', '127.0.0.1')
        #self.register_config_handler(self.api_port, 'api_port', 39284)
        self.register_config_handler(
            self.reader_enabled, 'reader_enabled', True)
        self.register_config_handler(
            self.reader_host, 'reader_host', '127.0.0.1')
        self.register_config_handler(self.reader_port, 'reader_port', 39285)
        self.register_config_handler(
            self.gtrans_api,
            'gtrans_api',
            'https://lingva.lunar.icu')
