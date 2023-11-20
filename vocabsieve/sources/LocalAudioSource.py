from ..models import AudioSource, LemmaPolicy, AudioLookupResult
from ..local_dictionary import LocalDictionary
import json
import os

class LocalAudioSource(AudioSource):
    def __init__(self, langcode: str, lemma_policy: LemmaPolicy, dictdb: LocalDictionary, dictname: str, path: str) -> None:
        super().__init__(dictname, langcode, lemma_policy)
        self.dictdb = dictdb
        self.base_path = path

    def _lookup(self, word: str) -> AudioLookupResult:
        try:
            audios = {}
            audio_files = json.loads(self.dictdb.define(word, self.langcode, self.name))
            print("audio_files", audio_files)
            for file in audio_files:
                audios[file] = os.path.join(self.base_path, file)
            return AudioLookupResult(audios=audios)
        except Exception as e:
            print(f"Word not found in {self.name}", e)
            return AudioLookupResult(error=repr(e))