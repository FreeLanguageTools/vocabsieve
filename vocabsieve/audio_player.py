import os
from threading import Thread
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
from typing import Dict
import requests
from .constants import FORVO_HEADERS
from .global_names import forvopath


class AudioPlayer:
    def __init__(self) -> None:
        self.player = QMediaPlayer()

    def crossplatform_play_sound(self, path):
        content = QUrl.fromLocalFile(path)
        self.player.setMedia(QMediaContent(content))
        Thread(target=self.player.play).start()

    def play_audio(self, name: str, data: Dict[str, str], lang: str) -> str:
        audiopath: str = data.get(name, "")
        if not audiopath:
            return ""

        if audiopath.startswith("https://"):
            name = name.replace("::", "__")  # Windows doesn't like colons in filenames
            fpath = os.path.join(forvopath, lang, name)
            if not os.path.exists(fpath):
                res = requests.get(audiopath, headers=FORVO_HEADERS, timeout=5)
                res.raise_for_status()

                os.makedirs(os.path.dirname(fpath), exist_ok=True)
                with open(fpath, 'bw') as file:
                    file.write(res.content)
            audiopath = fpath

        self.crossplatform_play_sound(audiopath)
        return audiopath
