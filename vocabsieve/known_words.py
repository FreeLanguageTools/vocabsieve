import time
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from .tools import *

def getKnownData(settings, rec):
    w_lookup = settings.value('tracking/w_lookup', 15, type=int) # Weight for each lookup, max 1 per day
    w_seen = settings.value('tracking/w_seen', 8, type=int) # W for seeing
    w_anki_ctx = settings.value('tracking/w_anki_ctx', 30, type=int) # W for being on context field of a mature card
    w_anki_word = settings.value('tracking/w_anki_word', 70, type=int) # W for being on the word field of a mature card
    w_anki_ctx_y = settings.value('tracking/w_anki_ctx_y', 20, type=int) # W for being on context field of a young card
    w_anki_word_y = settings.value('tracking/w_anki_word_y', 40, type=int) # W for being on the word field of a young card
    langcode = settings.value('target_language', 'en')

    score = {}

    start = time.time()

    lookup_data = rec.countAllLemmaLookups(langcode)
    count_lookup_data = 0
    for word, count in lookup_data:
        count_lookup_data += 1
        score[word] = score.get(word, 0) + count * w_lookup
    print("Prepared lookup data in", time.time() - start, "seconds")

    start = time.time()
    seen_data = rec.getSeen(langcode)
    count_seen_data = 0
    for word, count in seen_data:
        count_seen_data += 1
        score[word] = score.get(word, 0) + count * w_seen
    print("Prepared seen data in", time.time() - start, "seconds")

    start = time.time()
    
    fieldmap = json.loads(settings.value("tracking/fieldmap",  "{}"))
    if not fieldmap:
        QMessageBox.warning(None, "No Anki notes field matching data",
            "Use 'Match fields' in settings.")

    anki_api = settings.value("anki_api", "127.0.0.1:8765")

    tgt_lemmas = []
    ctx_lemmas = []
    if settings.value('enable_anki', True, type=bool):
        try:
            _ = getVersion(anki_api)
            mature_notes = findNotes(
                anki_api,
                settings.value("tracking/anki_query_mature")
                )
            young_notes = findNotes(
                anki_api,
                settings.value("tracking/anki_query_young")
                )
            young_notes = [note for note in young_notes if note not in mature_notes]
            n_mature = len(mature_notes)
            progress = QProgressDialog("Computing Anki data...", None, 0, n_mature+len(young_notes), None)
            progress.setWindowModality(Qt.WindowModal)  
            print("Got anki data from AnkiConnect in", time.time() - start, "seconds")
            start = time.time()
            mature_notes_info = notesInfo(anki_api, mature_notes)
            young_notes_info = notesInfo(anki_api, young_notes)

            for n, info in enumerate(mature_notes_info):
                progress.setValue(n)
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
                    try:
                        score[lemma] += w_anki_word
                    except KeyError:
                        score[lemma] = w_anki_word
                if ctx:
                    for ctx_word in re.sub(r"<.*?>", " ", ctx).split():
                        ctx_lemma = lem_word(ctx_word, langcode).lower()
                        if ctx_lemma != lemma: # No double counting
                            ctx_lemmas.append(ctx_lemma)
                            try:
                                score[ctx_lemma] += w_anki_ctx
                            except KeyError:
                                score[ctx_lemma] = w_anki_ctx

            for n, info in enumerate(young_notes_info):
                progress.setValue(n_mature+n)
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
                    try:
                        score[lemma] += w_anki_word_y
                    except KeyError:
                        score[lemma] = w_anki_word_y
                if ctx:
                    for ctx_word in re.sub(r"<.*?>", " ", ctx).split():
                        ctx_lemma = lem_word(ctx_word, langcode).lower()
                        if ctx_lemma != lemma: # No double counting
                            ctx_lemmas.append(ctx_lemma)
                            try:
                                score[ctx_lemma] += w_anki_ctx_y
                            except KeyError:
                                score[ctx_lemma] = w_anki_ctx_y
            progress.setValue(n_mature+n+1)
        except Exception as e:
            print(e)
            if settings.value("enable_anki"):
                QMessageBox.warning(None, "Cannot access AnkiConnect", 
                    "Check if AnkiConnect is installed and Anki is running. <br>Re-open statistics to view the whole data.")
        return score, count_seen_data, count_lookup_data, len(set(tgt_lemmas)), len(set(ctx_lemmas))