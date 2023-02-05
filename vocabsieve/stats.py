from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from operator import itemgetter
from .tools import *
from .lemmatizer import lem_word
import json

prettydigits = lambda number: format(number, ',').replace(',', ' ')

class StatisticsWindow(QDialog):
    def __init__(self, parent, src_name="Generic", path=None, methodname="generic"):
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
        threshold = self.settings.value('tracking/known_threshold', 100, type=int) # Score needed to be considered known
        w_lookup = self.settings.value('tracking/w_lookup', 15, type=int) # Weight for each lookup, max 1 per day
        w_seen = self.settings.value('tracking/w_seen', 8, type=int) # W for seeing
        w_anki_ctx = self.settings.value('tracking/w_anki_ctx', 30, type=int) # W for being on context field of a mature card
        w_anki_word = self.settings.value('tracking/w_anki_word', 70, type=int) # W for being on the word field of a mature card
        w_anki_ctx_y = self.settings.value('tracking/w_anki_ctx_y', 20, type=int) # W for being on context field of a young card
        w_anki_word_y = self.settings.value('tracking/w_anki_word_y', 40, type=int) # W for being on the word field of a young card
        langcode = self.settings.value('target_language', 'en')

        self.known.layout = QVBoxLayout(self.known)
        score = {}

        lookup_data = self.rec.countAllLemmaLookups(langcode)
        count_lookup_data = 0
        for word, count in lookup_data:
            count_lookup_data += 1
            score[word] = score.get(word, 0) + count * w_lookup

        seen_data = self.rec.getSeen(langcode)
        count_seen_data = 0
        for word, count in seen_data:
            count_seen_data += 1
            score[word] = score.get(word, 0) + count * w_seen
        
        fieldmap = json.loads(self.settings.value("tracking/fieldmap",  "{}"))
        if not fieldmap:
            QMessageBox.warning(self, "No Anki notes field matching data",
                "Use 'Match fields' in settings.")

        anki_api = self.settings.value("anki_api", "127.0.0.1:8765")

        tgt_lemmas = []
        ctx_lemmas = []
        if self.settings.value('enable_anki', True, type=bool):
            try:
                _ = getVersion(anki_api)
                mature_notes = findNotes(
                    anki_api,
                    self.settings.value("tracking/anki_query_mature")
                    )
                young_notes = findNotes(
                    anki_api,
                    self.settings.value("tracking/anki_query_young")
                    )
                young_notes = [note for note in young_notes if note not in mature_notes]


                mature_notes_info = notesInfo(anki_api, mature_notes)
                young_notes_info = notesInfo(anki_api, young_notes)

                for info in mature_notes_info:
                    model = info['modelName']
                    word_field, ctx_field = fieldmap.get(model) or ("<Ignore>", "<Ignore>")
                    word = ""
                    ctx = ""
                    if word_field != "<Ignore>":
                        word = info['fields'][word_field]['value']
                    if ctx_field != "<Ignore>":
                        ctx = info['fields'][ctx_field]['value']
                    if word:
                        lemma = lem_word(word, langcode).lower()
                        tgt_lemmas.append(lemma)
                        score[lemma] = score.get(lemma, 0) + w_anki_word
                    if ctx:
                        for ctx_word in re.sub(r"<.*?>", " ", ctx).split():
                            ctx_lemma = lem_word(ctx_word, langcode).lower()
                            if ctx_lemma != lemma: # No double counting
                                ctx_lemmas.append(ctx_lemma)
                                score[ctx_lemma] = score.get(ctx_lemma, 0) + w_anki_ctx

                for info in young_notes_info:
                    model = info['modelName']
                    word_field, ctx_field = fieldmap.get(model) or ("<Ignore>", "<Ignore>")
                    word = ""
                    ctx = ""
                    if word_field != "<Ignore>":
                        word = info['fields'][word_field]['value']
                    if ctx_field != "<Ignore>":
                        ctx = info['fields'][ctx_field]['value']
                    if word:
                        lemma = lem_word(word, langcode).lower()
                        tgt_lemmas.append(lemma)
                        score[lemma] = score.get(lemma, 0) + w_anki_word_y
                    if ctx:
                        for ctx_word in re.sub(r"<.*?>", " ", ctx).split():
                            ctx_lemma = lem_word(ctx_word, langcode).lower()
                            if ctx_lemma != lemma: # No double counting
                                ctx_lemmas.append(ctx_lemma)
                                score[ctx_lemma] = score.get(ctx_lemma, 0) + w_anki_ctx_y
            except Exception as e:
                if self.settings.value("enable_anki"):
                    QMessageBox.warning(self, "Cannot access AnkiConnect", 
                        "Check if AnkiConnect is installed and Anki is running. <br>Re-open statistics to view the whole data.")
        print(len(set(ctx_lemmas)), len(ctx_lemmas))
        known_words = [word for word, points in score.items() if points >= threshold and word.isalpha()]
        if langcode in ['ru', 'uk']:
            known_words = [word for word in known_words if starts_with_cyrillic(word)]
        total_score = int(sum(min(threshold, points) for points in score.values()) / threshold)
        self.known.layout.addWidget(QLabel(f"<h3>Known words (<i>{prettydigits(len(known_words))}</i>)</h3>"))
        self.known.layout.addWidget(QLabel(f"<h4>Your total score: {prettydigits(total_score)}</h4>"))
        self.known.layout.addWidget(
            QLabel(
                f"Lemmas: {prettydigits(count_seen_data)} seen, {prettydigits(count_lookup_data)} looked up, "
                f"{prettydigits(len(set(tgt_lemmas)))} as Anki targets, {prettydigits(len(set(ctx_lemmas)))} in Anki context"))
        known_words_widget = QPlainTextEdit(" ".join(known_words))
        known_words_widget.setReadOnly(True)
        self.known.layout.addWidget(known_words_widget)