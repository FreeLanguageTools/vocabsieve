import time
import json
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import Qt
import re
from .tools import getVersion, findNotes, notesInfo
from .lemmatizer import lem_word

last_known_data = None
last_known_data_date = 0.0 # 1970-01-01

def getKnownWords(settings, rec, dictdb):
    langcode = settings.value('target_language', 'en')
    known_langs = [l.strip() for l in settings.value('tracking/known_langs', 'en').split(",")]
    score, count_seen_data, count_lookup_data, count_tgt_lemmas, count_ctx_lemmas = getKnownData(settings, rec)
    cognates = set(dictdb.getCognatesData(langcode, known_langs))
    threshold = settings.value('tracking/known_threshold', 100, type=int)
    threshold_cognate = settings.value('tracking/known_threshold_cognate', 25, type=int)
    start = time.time()
    total_score = 0
    total_score += sum([min(points, threshold) for word, points in score.items() if word not in cognates]) / threshold
    total_score += sum([min(points, threshold_cognate) for word, points in score.items() if word in cognates]) / threshold_cognate
    known_words = [word for word, points in score.items() if points >= threshold and word not in cognates]
    known_cognates = [word for word, points in score.items() if points >= threshold_cognate and word in cognates]
    known_words += known_cognates
    known_words = sorted(list(set(known_words)))
    return set(known_words), known_cognates, total_score, count_seen_data, count_lookup_data, count_tgt_lemmas, count_ctx_lemmas

