from PyQt5.QtWidgets import QListWidget, QListView, QToolButton, QVBoxLayout
from PyQt5.QtCore import QCoreApplication, pyqtSignal, QSize
from PyQt5.QtWidgets import QStyle
from typing import Optional

from ..audio_player import AudioPlayer
from ..global_names import MOD, settings
from ..models import AudioDefinition, AudioSourceGroup, Definition
import threading


class AudioSelector(QListWidget):
    audio_fetched = pyqtSignal(AudioDefinition)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(50)
        self.setFlow(QListView.TopToBottom)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)
        self.audio_player = AudioPlayer()
        self.discard_audio_button = QToolButton(self)

        self.discard_audio_button.clicked.connect(self.clear)
        self.discard_audio_button.setToolTip(f"Discard audio [{MOD}+Shift+X]")

        icon = self.style().standardIcon(QStyle.SP_TrashIcon)
        self.discard_audio_button.setIcon(icon)

        self.current_audio_path = ""
        self.audios: dict[str, str] = {}
        self.sg: Optional[AudioSourceGroup] = None
        self.audio_fetched.connect(self.appendDefinition)
        self.connect_signals()

    def setSourceGroup(self, sg: AudioSourceGroup) -> None:
        self.sg = sg

    def getDefinitions(self, word: str) -> list[AudioDefinition]:
        if self.sg is None:
            return []
        return self.sg.define(word)

    def lookup_on_thread(self, word: str):
        self.clear()
        for definition in self.getDefinitions(word):
            self.audio_fetched.emit(definition)

    def appendDefinition(self, defi: AudioDefinition):
        if defi.audios is None:
            return
        self.audios.update(defi.audios)
        self.updateAudioUI()

    def clear(self):
        super().clear()
        self.audios = {}
        self.current_audio_path = ""

    def lookup(self, word: str):
        # check if all sources are online
        if self.sg is not None:
            all_online = all(not source.INTERNET for source in self.sg.sources)
            if all_online:
                # Use threads only if all online because sqlite cursor
                # can't be accessed from multiple threads
                threading.Thread(
                    target=self.lookup_on_thread,
                    args=(word,)).start()
            else:
                self.lookup_on_thread(word)

    def play_audio_if_exists(self, x):
        if x is not None:
            audio_name = x.text()[2:]
            self.current_audio_path = self.audios.get(audio_name, "")
            self.play_audio(audio_name)
        else:
            self.current_audio_path = ""

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.alignDiscardButton()

    def alignDiscardButton(self):
        padding = QSize(5, 5)  # optional
        newSize = self.size() - self.discard_audio_button.size() - padding
        self.discard_audio_button.move(newSize.width(), 0)

    def updateAudioUI(self):
        for item in self.audios:
            self.addItem("🔊 " + item)
        self.setCurrentItem(self.item(0))

    def play_audio(self, name: Optional[str]) -> None:
        QCoreApplication.processEvents()
        if name is None:
            return

        self.audio_path = self.audio_player.play_audio(name, self.audios, settings.value("target_language", "en"))

    def connect_signals(self):
        self.currentItemChanged.connect(self.play_audio_if_exists)
        self.itemDoubleClicked.connect(self.play_audio_if_exists)
