from shutil import rmtree
import os

from PyQt5.QtWidgets import QDialog, QTabWidget, QMessageBox, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

from .general_tab import GeneralTab
from .source_tab import SourceTab
from .processing_tab import ProcessingTab
from .anki_tab import AnkiTab
from .network_tab import NetworkTab
from .tracking_tab import TrackingTab
from .interface_tab import InterfaceTab
from .misc_tab import MiscTab
from ..global_names import settings, logger


class ConfigDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        logger.debug("Initializing settings dialog")
        self._parent = parent
        self.resize(700, 500)
        if settings.value("config_ver") is None \
                and settings.value("target_language") is not None:
            settings.clear()
        settings.setValue("config_ver", 1)
        self.setWindowTitle("Configure VocabSieve")
        self.initTabs()
        self.setupTabs()

    def initTabs(self):
        self.tabs = QTabWidget()
        self.tab_g = GeneralTab()
        self.tab_s = SourceTab()
        self.tab_p = ProcessingTab()
        self.tab_a = AnkiTab()
        self.tab_n = NetworkTab()
        self.tab_t = TrackingTab()
        self.tab_i = InterfaceTab()
        self.tab_m = MiscTab()

        self.tabs.resize(400, 400)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)

        self.tabs.addTab(self.tab_g, "General")
        self.tabs.addTab(self.tab_s, "Sources")
        self.tabs.addTab(self.tab_p, "Processing")
        self.tabs.addTab(self.tab_a, "Anki")
        self.tabs.addTab(self.tab_n, "Network")
        self.tabs.addTab(self.tab_t, "Tracking")
        self.tabs.addTab(self.tab_i, "Interface")
        self.tabs.addTab(self.tab_m, "Misc")

    def setupTabs(self):
        self.tab_g.sources_reloaded_signal.connect(self.tab_s.reloadSources)
        self.tab_s.sg2_visibility_changed.connect(self.changeMainLayout)
        self.tab_g.sources_reloaded_signal.connect(self.tab_p.setupSelector)
        self.tab_m.nuke.connect(self.nuke_profile)
        self.tab_m.reset.connect(self.reset_settings)
        self.tab_g.load_dictionaries()

    def reset_settings(self):
        answer = QMessageBox.question(
            self,
            "Confirm Reset<",
            "<h1>Danger!</h1>"
            "Are you sure you want to reset all settings? "
            "This action cannot be undone. "
            "This will also close the configuration window.",
            defaultButton=QMessageBox.StandardButton.No
        )
        if answer == QMessageBox.Yes:
            settings.clear()
            self.close()

    def nuke_profile(self):
        datapath = self._parent.datapath
        answer = QMessageBox.question(
            self,
            "Confirm Reset",
            "<h1>Danger!</h1>"
            "Are you sure you want to delete all user data? "
            "The following directory will be deleted:<br>" + datapath
            + "<br>This action cannot be undone. "
            "This will also close the program.",
            defaultButton=QMessageBox.StandardButton.No
        )
        if answer == QMessageBox.Yes:
            settings.clear()
            rmtree(datapath)
            os.mkdir(datapath)
            self._parent.close()

    def errorNoConnection(self, error):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(
            str(error) + "\nAnkiConnect must be running to set Anki-related options."
            "\nIf you have AnkiConnect set up at a different endpoint, set that now "
            "and reopen the config tool.")
        msg.exec()

    @pyqtSlot(bool)
    def changeMainLayout(self, checked: bool):
        if checked:
            # This means user has changed from one source to two source mode,
            # need to redraw main window
            if settings.value("orientation", "Vertical") == "Vertical":
                self._parent._layout.removeWidget(self._parent.definition)
                self._parent._layout.addWidget(
                    self._parent.definition, 6, 0, 2, 3)
                self._parent._layout.addWidget(
                    self._parent.definition2, 8, 0, 2, 3)
                self._parent.definition2.setVisible(True)
        else:
            self._parent._layout.removeWidget(self._parent.definition)
            self._parent._layout.removeWidget(self._parent.definition2)
            self._parent.definition2.setVisible(False)
            self._parent._layout.addWidget(self._parent.definition, 6, 0, 4, 3)
