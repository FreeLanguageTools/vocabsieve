from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from operator import itemgetter
from pyqtgraph import PlotWidget, BarGraphItem, PlotItem, AxisItem, mkPen
from datetime import timedelta, datetime
import time
import math
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
        self.known = QWidget()  # Known words
        self.lookupStats = QWidget()  # Lookup stats
        self.mlw = QWidget()  # Most looked up words
        self.tabs.resize(400, 500)
        self.langcode = self.settings.value('target_language', 'en')
        self.initKnown()
        self.initMLW()
        self.initLookupsStats()
        self.tabs.addTab(self.known, "Known words")
        self.tabs.addTab(self.mlw, "Most looked up words")
        self.tabs.addTab(self.lookupStats, "Lookup stats")
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tabs)

    def initMLW(self):
        items = self.rec.countAllLemmaLookups(self.langcode)
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
        hasCognates = dictdb.hasCognatesData()
        if not hasCognates:
            self.known.layout.addWidget(label:=QLabel('No cognates data installed. Please download <a href="https://raw.githubusercontent.com/FreeLanguageTools/CogNet-processing/master/cognates.json.xz">this file</a> and import it in the configuration tool.'))
            label.setOpenExternalLinks(True)
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
        self.lookupStats.layout = QVBoxLayout(self.lookupStats)
        self.lookupStats.layout.addWidget(QLabel(f"<h3>Lookup statistics</h3>"))
        data = self.rec.getAllLookups()
        today_midnight = datetime.combine(datetime.today(), datetime.min.time()).timestamp()
        timestamp_30d_ago = today_midnight - 30 * 24 * 60 * 60
        #timestamp_90d_ago = today_midnight - 90 * 24 * 60 * 60
        #timestamp_180d_ago = today_midnight - 180 * 24 * 60 * 60

        # 30 days
        words_looked_up = {} # List of sets of lemmas looked up, 0 is today, 1 is yesterday, etc.
        for i in range(31):
            words_looked_up[i] = set()
        for timestamp, word, lemma, language, lemmatization, source, success in data:
            if language == self.langcode and timestamp > timestamp_30d_ago:
                n_days_ago = math.ceil((today_midnight - timestamp) / (24 * 60 * 60))
                words_looked_up[n_days_ago].add(lemma)
        n_words_looked_up = [len(words_looked_up[i]) for i in range(31)]
        n_cumul_words_looked_up = [sum(n_words_looked_up[i:]) for i in range(31)]
        #self.lookupStats.layout.addWidget(QLabel(f"Count of words looked up in the last 30 days: {n_words_looked_up}"))
        # Draw bar chart with pyqtgraph
        self.lookups_plotwidget = PlotWidget()
        bgcolor = self.palette().color(QPalette.Background)
        self.lookups_plotwidget.setBackground(bgcolor)
        self.lookupStats.layout.addWidget(self.lookups_plotwidget)
        bar = BarGraphItem(x=[-i for i in range(31)], height=n_words_looked_up, width=1, brush='#4e79a7')
        self.lookups_plotwidget.addItem(bar)

        ratio = (max(n_cumul_words_looked_up) / max(n_words_looked_up)) if max(n_words_looked_up) else 1
        n_cumul_words_looked_up = [int(n / ratio) for n in n_cumul_words_looked_up]

        self.lookups_plotwidget.plot(x=[-i for i in range(31)], y=n_cumul_words_looked_up, pen=mkPen('#f28e2b', width=3))
        self.lookups_plotwidget.setLabel('left', "Distinct words looked up")
        self.lookups_plotwidget.setLabel('right', "Cumulative words looked up")
        axisItem = AxisItem('right')
        pretty_number_max = int(round(max(n_cumul_words_looked_up)*ratio, -len(str(int(max(n_cumul_words_looked_up)*ratio))) + 1))
        pretty_number_step = max(int(round(pretty_number_max // 6, -len(str(pretty_number_max // 6)) + 1)), 1)
        axisItem.setTicks([[(n/ratio, str(int(n))) for n in range(0, pretty_number_max, pretty_number_step)],[]])
        self.lookups_plotwidget.setAxisItems({'right': axisItem})
        self.lookups_plotwidget.setLabel('bottom', "Day")
        self.lookupStats.layout.addWidget(QLabel(f"Total lookups: {prettydigits(sum(n_words_looked_up))} ({round(sum(n_words_looked_up)/30, 1)} per day, {round(sum(n_words_looked_up)/4.3, 1)} per week)"))
