from typing import TYPE_CHECKING
from sentence_splitter import SentenceSplitter
from .GenericImporter import GenericImporter
from .utils import *
from datetime import datetime as dt
import os
import re
from ..lemmatizer import lem_word, lem_pre
from ..tools import *

if TYPE_CHECKING:
    from ..main import MainWindow

from .models import ReadingNote
import itertools

class AutoTextImporter(GenericImporter):
    def __init__(self, parent: "MainWindow", path):
        self.path: str = path
        self.splitter: SentenceSplitter= parent.splitter
        self.known_words, _ = parent.getKnownWords()
        super().__init__(parent, "Auto vocab detection", path, "auto", show_selector_src=False, show_selector_date=False)

    def getNotes(self):
        chs = ebook2text(self.path)[0]
        bookname = os.path.splitext(os.path.basename(self.path))[0]
        sentences = list(sentence for sentence in 
            itertools.chain.from_iterable(
                map(lambda x: self.splitter.split(x), (ch for ch in chs))
                ) 
            if sentence)

        known_words = set(self.known_words)
        already_mined = set()
        reading_notes = []
        norepeat = True
        #only_1t = True
        for sentence in sentences:
            unknowns = []
            for word, lemma in zip(sentence.split(), map(lambda x: lem_word(x, self.lang), sentence.split())):
                word = lem_pre(word, self.lang)
                if lemma not in known_words and lemma.isalpha() and lemma not in already_mined:
                    unknowns.append(word)
            if len(unknowns) == 1:
                if not (norepeat and lem_word(unknowns[0], self.lang) in already_mined):
                    #target_sentences.append(sentence)
                    #target_words.append(unknowns[0])
                    already_mined.update([lem_word(unknowns[0], self.lang)])
                    reading_notes.append(ReadingNote(
                        lookup_term=unknowns[0],
                        sentence=sentence,
                        book_name=bookname,
                        date=str(dt.now().astimezone())[:19]
                        ))
        return reading_notes
        
