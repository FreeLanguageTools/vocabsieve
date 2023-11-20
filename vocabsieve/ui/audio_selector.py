from PyQt5.QtWidgets import QListWidget, QListView
from PyQt5.QtCore import QCoreApplication
from typing import Optional
from ..audio_player import AudioPlayer
from ..models import AudioDefinition, AudioSourceGroup, Definition

class AudioSelector(QListWidget):
    def __init__(self, settings):
        super().__init__()
        self.setMinimumHeight(50)
        self.settings = settings
        self.setFlow(QListView.TopToBottom)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)
        self.audio_player = AudioPlayer()
        self.audios = {}
        self.sg: Optional[AudioSourceGroup] = None
        self.connect_signals()

    def setSourceGroup(self, sg: AudioSourceGroup):
        self.sg = sg

    def getDefinitions(self, word: str) -> list[AudioDefinition]:
        if self.sg is None:
            return []
        return self.sg.define(word)
    
    def lookup(self, word: str):
        self.clear()
        self.audios = {}
        for definition in self.getDefinitions(word):
            self.appendDefinition(definition)
        self.updateAudioUI()

    def appendDefinition(self, defi: AudioDefinition):
        if defi.audios is None:
            return
        self.audios.update(defi.audios)
    



    def play_audio_if_exists(self, x):
        if x is not None:
            self.play_audio(x.text()[2:])

    def updateAudioUI(self):
        for item in self.audios:
            self.addItem("🔊 " + item)
        self.setCurrentItem(self.item(0))

    def play_audio(self, name: Optional[str]) -> None:
        QCoreApplication.processEvents()
        if name is None:
            return

        self.audio_path = self.audio_player.play_audio(name, self.audios, self.settings.value("target_language", "en"))

    def connect_signals(self):
        self.currentItemChanged.connect(self.play_audio_if_exists)
        self.itemDoubleClicked.connect(self.play_audio_if_exists)