from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from operator import itemgetter
import time
from .tools import *
from .known_words import getKnownData, getKnownWords

prettydigits = lambda number: format(number, ',').replace(',', ' ')

class StatisticsWindow(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.settings = parent.settings
        self.rec = parent.rec
        self.setWindowTitle(f"Statistics")
        self.tabs = QTabWidget()
        self.mlw = QWidget()  # Most looked up words
        self.known = QWidget()  # Known words
        self.tabs.resize(400, 500)
        self.tabs.addTab(self.mlw, "Most looked up words")
        self.initMLW()
        self.tabs.addTab(self.known, "Known words")
        self.initKnown()
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tabs)

    def initMLW(self):
        langcode = self.settings.value('target_language', 'en')
        items = self.rec.countAllLemmaLookups(langcode)
        items = sorted(items, key=itemgetter(1), reverse=True) # Sort by counts, descending
        self.mlw.layout = QVBoxLayout(self.mlw)
        
        levels = [5, 8, 12, 20]
        level_prev = 1e9
        words_for_level = {}
        lws = {}
        for level in reversed(levels):
            count = 0
            #lws[level] = QListWidget()
            lws[level] = QLabel()
            lws[level].setWordWrap(True)
            #lws[level].setFlow(QListView.LeftToRight)
            #lws[level].setResizeMode(QListView.Adjust)
            #lws[level].setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
            #lws[level].setWrapping(True)
            content = ""
            for item in items:
                if level_prev > item[1] >= level and not item[0].startswith("http") and item[0]:
                    #lws[level].addItem(item[0])
                    content += item[0] + " "
                    count += 1
            lws[level].setText(content)
            self.mlw.layout.addWidget(QLabel(f"<h3>{level}+ lookups (<i>{count}</i>)</h3>"))
            self.mlw.layout.addWidget(lws[level])
            level_prev = level

    def initKnown(self):
        self.threshold = self.settings.value('tracking/known_threshold', 100, type=int) 
        self.threshold_cognate = self.settings.value('tracking/known_threshold_cognate', 25, type=int)
        self.known_langs = [l.strip() for l in self.settings.value('tracking/known_langs', 'en').split(",")]
        langcode = self.settings.value('target_language', 'en')
        start = time.time()
        self.known.layout = QVBoxLayout(self.known)
        
        known_words, known_cognates, total_score, count_seen_data, count_lookup_data, count_tgt_lemmas, count_ctx_lemmas = getKnownWords(self.settings, self.rec)
        print("Got known data in", time.time() - start, "seconds")

        if langcode in ['ru', 'uk']:
            known_words = [word for word in known_words if starts_with_cyrillic(word)]
        self.known.layout.addWidget(QLabel(f"<h3>Known words: {prettydigits(len(known_words))} ({prettydigits(len(known_cognates))} cognates)</h3>"))
        self.known.layout.addWidget(QLabel(f"<h4>Your total score: {prettydigits(int(total_score))}</h4>"))
        self.known.layout.addWidget(
            QLabel(
                f"Lemmas: {prettydigits(count_seen_data)} seen, {prettydigits(count_lookup_data)} looked up, "
                f"{prettydigits(count_tgt_lemmas)} as Anki targets, {prettydigits(count_ctx_lemmas)} in Anki context"))
        known_words_widget = QPlainTextEdit(" ".join(known_words))
        known_words_widget.setReadOnly(True)
        self.known.layout.addWidget(known_words_widget)

    def initLookupsStats(self):
        pass
            