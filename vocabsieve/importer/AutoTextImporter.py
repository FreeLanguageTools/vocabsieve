from .GenericImporter import GenericImporter
from .utils import *
from datetime import datetime as dt, timezone as tz
import sqlite3
import os
import re
from PyQt5.QtWidgets import QCheckBox, QLabel
from ..known_words import getKnownWords
from typing import Tuple, Dict, Set
from ..lemmatizer import lem_word, lem_pre
from ..dictformats import removeprefix
from ..tools import *

class AutoTextImporter(GenericImporter):
    def __init__(self, parent, path):
        self.path = path
        super().__init__(parent, "Auto vocab detection", path, "auto")

    def getNotes(self):
        chs = ebook2text(self.path)[0]
        bookname = os.path.splitext(os.path.basename(self.path))[0]
        sentences = list(sentence for sentence in 
            itertools.chain.from_iterable(
                map(lambda x: split_to_sentences(x, self.lang), (ch for ch in chs))
                ) 
            if sentence)

        known_words, *_ = getKnownWords(self.parent.settings, self.parent.rec)
        known_words = set(known_words)
        already_mined = set()
        target_words = []
        target_sentences = []
        norepeat = True
        only_1t = True
        print(len(sentences), "sentences found in text.")
        for sentence in sentences:
            unknowns = []
            for word, lemma in zip(sentence.split(), map(lambda x: lem_word(x, self.lang), sentence.split())):
                word = lem_pre(word, self.lang)
                if lemma not in known_words and lemma.isalpha() and lemma not in already_mined:
                    unknowns.append(word)
            if len(unknowns) == 1:
                if not (norepeat and lem_word(unknowns[0], self.lang) in already_mined):
                    target_sentences.append(sentence)
                    target_words.append(unknowns[0])
                    already_mined.update([lem_word(unknowns[0], self.lang)])
            if not only_1t:
                if len(unknowns) >= 2:
                    for lemma in unknowns:
                        target_words.append(lemma)
                        target_sentences.append(sentence)
        return target_words, target_sentences, [str(dt.now().astimezone())[:19]]*len(target_words), [bookname]*len(target_words)
        
