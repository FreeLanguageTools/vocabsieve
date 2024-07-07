import itertools
from datetime import datetime as dt
from typing import TYPE_CHECKING
from sentence_splitter import SentenceSplitter
from .GenericImporter import GenericImporter
import os
from ..lemmatizer import lem_word, lem_pre
from .models import ReadingNote
from ..tools import ebook2text
from .AutoTextVisualizer import AutoTextVisualizer

if TYPE_CHECKING:
    from ..main import MainWindow


class AutoTextImporter(GenericImporter):
    def __init__(self, parent: "MainWindow", path):
        self.path: str = path
        self.splitter: SentenceSplitter = parent.splitter
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
        treat_capital_words_as_known = self.lang not in ('de', 'lb')
        visualizer_data: list[str] = []
        for sentence in sentences:
            unknowns = []
            start = False
            visualizer_sentence = sentence
            # Detect the unknown words in sentence
            for word, lemma in zip(sentence.split(), map(lambda x: lem_word(x, self.lang), sentence.split())):
                word = lem_pre(word, self.lang)
                is_capital_but_not_initial = word and word[0].isupper() and not start
                if lemma not in known_words \
                        and lemma.isalpha() \
                        and lemma not in already_mined \
                        and not (is_capital_but_not_initial and treat_capital_words_as_known):

                    unknowns.append(word)
                    visualizer_sentence = visualizer_sentence.replace(word, f"[{word}]")

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

            visualizer_data.append(visualizer_sentence)

        AutoTextVisualizer(self, visualizer_data).show()

        return reading_notes
