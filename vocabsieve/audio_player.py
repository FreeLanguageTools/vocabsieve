import os
from threading import Thread
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
from typing import Dict
import requests
from .forvo import *
from .dictionary import *

class AudioPlayer:
  def __init__(self) -> None:
    self.player = QMediaPlayer()

  def crossplatform_play_sound(self, path):
    self.player.setMedia(QMediaContent(path))
    Thread(target=lambda: self.player.play()).start()

  def play_audio(self, name: str, data: Dict[str, str], lang: str) -> str:
    audiopath: str = data.get(name, "")
    if not audiopath:
        return ""

    if not audiopath.startswith("https://"):
        content = QUrl(audiopath)
        self.crossplatform_play_sound(content)
        return audiopath

    fpath = os.path.join(forvopath, lang, name)
    if not os.path.exists(fpath):
        res = requests.get(audiopath, headers=HEADERS)

        if res.status_code != 200:
            # /TODO: Maybe display error to the user?
            return ""

        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, 'bw') as file:
            file.write(res.content)

    url = QUrl.fromLocalFile(fpath)
    self.crossplatform_play_sound(url)
    return fpath