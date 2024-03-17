from ..models import AudioSource, LemmaPolicy, AudioLookupResult
from ..local_dictionary import LocalDictionary
import json
from loguru import logger
import os

class LocalAudioSource(AudioSource):
    def __init__(self, langcode: str, lemma_policy: LemmaPolicy, dictdb: LocalDictionary, dictname: str, path: str) -> None:
        super().__init__(dictname, langcode, lemma_policy)
        self.dictdb = dictdb
        self.base_path = path

    def _lookup(self, word: str) -> AudioLookupResult:
        try:
            audios = {}
            audio_files = json.loads(self.dictdb.define(word, self.langcode, self.name) or "[]")
            for file in audio_files:
                audios[file] = os.path.join(self.base_path, file)
            return AudioLookupResult(audios=audios)
        except KeyError as e:
            logger.debug(repr(e))
            return AudioLookupResult(error=repr(e))