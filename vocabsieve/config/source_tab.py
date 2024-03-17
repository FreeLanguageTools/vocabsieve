import json
from bidict import bidict
from PyQt5.QtWidgets import QLabel, QComboBox, QLineEdit, QPushButton, QCheckBox, QGridLayout
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from .base_tab import BaseTab
from ..constants import langcodes
from .dictmanager import DictManager
from ..dictionary import getFreqlistsForLang, getDictsForLang, getAudioDictsForLang, langs_supported
from ..global_names import settings
from ..ui import SourceGroupWidget, AllSourcesWidget
from ..models import LemmaPolicy

BOLD_STYLES = ["<disabled>", "Font weight", "Underscores"]


class SourceTab(BaseTab):
    sg2_visibility_changed = pyqtSignal(bool)

    def initWidgets(self):
        self.sg1_widget = SourceGroupWidget()
        self.sg2_widget = SourceGroupWidget()
        self.all_sources_widget = AllSourcesWidget()
        self.sg2_enabled = QCheckBox("Enable Dictionary Group 2")
        self.audio_sg_widget = SourceGroupWidget()
        self.all_audio_sources_widget = AllSourcesWidget()
        self.audio_lemma_policy = QComboBox()

    def setupWidgets(self):
        self.sg2_enabled.clicked.connect(self.sg2_visibility_changed.emit)

    def setupLayout(self):
        layout = QGridLayout(self)
        layout.addWidget(QLabel("<h3>Dictionary sources</h3>"), 0, 0, 1, 2)
        layout.addWidget(QLabel("Dictionary Group 1"), 1, 0, 1, 1)
        layout.addWidget(QLabel("Available dictionaries"), 1, 1, 1, 1)
        layout.addWidget(self.sg1_widget, 2, 0, 1, 1)
        layout.addWidget(self.sg2_enabled, 3, 0, 1, 2)
        layout.addWidget(self.sg2_widget, 4, 0, 1, 1)
        layout.addWidget(self.all_sources_widget, 2, 1, 3, 1)

        layout.addWidget(QLabel("<h3>Pronunciation sources</h3>"), 5, 0, 1, 2)
        layout.addWidget(QLabel("Lemmatization policy for pronunciation"), 6, 0, 1, 1)
        layout.addWidget(self.audio_lemma_policy, 6, 1, 1, 1)
        layout.addWidget(QLabel("Enabled pronunciation sources"), 7, 0, 1, 1)
        layout.addWidget(QLabel("Available pronunciation sources"), 7, 1, 1, 1)
        layout.addWidget(self.audio_sg_widget, 8, 0, 1, 1)
        layout.addWidget(self.all_audio_sources_widget, 8, 1, 1, 1)

    def setupAutosave(self):
        self.sg2_enabled.stateChanged.connect(lambda value: self.sg2_widget.setEnabled(value))
        self.sg2_widget.setEnabled(self.sg2_enabled.isChecked())
        for policy in LemmaPolicy:
            self.audio_lemma_policy.addItem(policy.value, policy)
        self.register_config_handler(self.sg2_enabled, 'sg2_enabled', False)
        self.register_config_handler(self.sg1_widget, 'sg1', [])
        self.register_config_handler(self.sg2_widget, 'sg2', [])

        self.register_config_handler(self.audio_sg_widget, 'audio_sg', [])
        self.register_config_handler(self.audio_lemma_policy, 'audio_lemma_policy', LemmaPolicy.first_lemma)

    @pyqtSlot(list, list)
    def reloadSources(self, dicts: list, audio_dicts: list):
        self.all_audio_sources_widget.clear()
        self.all_audio_sources_widget.addItems(audio_dicts)
        self.all_sources_widget.clear()
        self.all_sources_widget.addItems(dicts)
