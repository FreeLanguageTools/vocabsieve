from .base_tab import BaseTab
from PyQt5.QtWidgets import QLabel, QFormLayout, QPushButton, QComboBox, QSpinBox, QCheckBox
from PyQt5.QtCore import pyqtSlot
from ..models import DisplayMode, LemmaPolicy
from .word_rules_editor import WordRulesEditor


class ProcessingTab(BaseTab):
    def initWidgets(self):
        self.word_proc_button = QPushButton("Edit word preprocessing rules")
        self.postproc_selector = QComboBox()
        self.display_mode = QComboBox()
        self.lemma_policy = QComboBox()
        self.skip_top = QSpinBox()
        self.skip_top.setSuffix(" lines")
        self.cleanup_html = QCheckBox()
        self.cleanup_html.setDisabled(True)
        self.collapse_newlines = QSpinBox()
        self.collapse_newlines.setSuffix(" newlines")

    def setupWidgets(self):
        for mode in DisplayMode:
            self.display_mode.addItem(mode.value, mode)
        for policy in LemmaPolicy:
            self.lemma_policy.addItem(policy.value, policy)
        self.postproc_selector.currentTextChanged.connect(self.setupProcessing)
        self.word_proc_button.clicked.connect(self.openWordRulesEd)
        self.setupProcessing()
        self.deactivateProcessing()

    def setupLayout(self):
        layout = QFormLayout(self)
        layout.addRow(self.word_proc_button)

        layout.addRow(QLabel("<h3>Per-dictionary postprocessing options</h3>"))
        layout.addRow(QLabel("Configure for dictionary:"), self.postproc_selector)
        layout.addRow(QLabel("<hr>"))
        layout.addRow(QLabel("Lemmatization policy"), self.lemma_policy)
        layout.addRow(QLabel("Display mode"), self.display_mode)
        layout.addRow(QLabel("<i>◊ HTML mode does not support editing/processing. "
                             "Your edits will not be saved!</i>"))
        layout.addRow(QLabel("Do not display the top"), self.skip_top)
        layout.addRow(QLabel(
            "<i>◊ Use this if your dictionary repeats the word in the first line.</i>"))
        layout.addRow(QLabel("Collapse continuous newlines into"), self.collapse_newlines)
        layout.addRow(QLabel(
            "<i>◊ Set to 1 to remove blank lines. 0 will leave them intact.</i>"))
        layout.addRow(QLabel("Attempt to clean up HTML"), self.cleanup_html)
        layout.addRow(QLabel(
            "<i>◊ Try this if your mdx dictionary does not work.</i> (NOT IMPLEMENTED)"))

    @pyqtSlot(list, list)
    def setupSelector(self, dicts, _):
        self.postproc_selector.blockSignals(True)
        self.postproc_selector.clear()
        self.postproc_selector.addItems(dicts)
        self.postproc_selector.blockSignals(False)

    @pyqtSlot()
    def setupProcessing(self):
        """This will allow per-dictionary configurations.
        Whenever dictionary changes, the QSettings key name must change.
        """
        curr_dict = self.postproc_selector.currentText()
        # Remove all existing connections
        try:
            self.lemma_policy.currentTextChanged.disconnect()
            self.display_mode.currentTextChanged.disconnect()
            self.skip_top.valueChanged.disconnect()
            self.collapse_newlines.valueChanged.disconnect()
            self.cleanup_html.clicked.disconnect()
        except TypeError:
            # When there are no connected functions, it raises a TypeError
            # 2022-12-28 Apparently now in PyQt5 it returns RuntimeError instead
            pass
        # Reestablish config handlers
        self.register_config_handler(self.display_mode,
                                     f"{curr_dict}/" + "display_mode", DisplayMode.markdown_html)
        self.display_mode.currentTextChanged.connect(
            self.deactivateProcessing
        )
        self.register_config_handler(self.lemma_policy,
                                     f"{curr_dict}/" + "lemma_policy", LemmaPolicy.first_lemma)
        self.register_config_handler(self.skip_top,
                                     f"{curr_dict}/" + "skip_top", 0)
        self.register_config_handler(self.collapse_newlines,
                                     f"{curr_dict}/" + "collapse_newlines", 0)
        self.register_config_handler(self.cleanup_html,
                                     f"{curr_dict}/" + "cleanup_html", False)
        self.deactivateProcessing()

    def deactivateProcessing(self):
        """Deactivate some options when HTML mode is selected"""
        curr_display_mode = self.display_mode.currentText()
        if curr_display_mode == 'HTML':
            self.skip_top.setDisabled(True)
            self.collapse_newlines.setDisabled(True)
        else:
            self.skip_top.setEnabled(True)
            self.collapse_newlines.setEnabled(True)

    def openWordRulesEd(self):
        wordproc = WordRulesEditor(self)
        wordproc.exec()

    def setupAutosave(self):
        pass
