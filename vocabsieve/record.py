import sqlite3
import os
import time
import re
from bidict import bidict
from typing import Optional, cast
import json
from PyQt5.QtCore import QSettings
from datetime import datetime
from .constants import langcodes
from .lemmatizer import lem_word
from .models import LookupRecord, WordRecord, KnownMetadata, SRSNote
from .tools import findNotes, notesInfo
from .global_names import logger, settings


class Record():
    """Class to store user data"""

    def __init__(self, parent_settings: QSettings, datapath):
        self.conn = sqlite3.connect(
            os.path.join(
                datapath,
                "records.db"),
            check_same_thread=False)
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA foreign_keys = ON")
        self._createTables()
        if not parent_settings.value("internal/lookup_unique_index"):
            self._makeLookupUnique()
            parent_settings.setValue("internal/lookup_unique_index", True)
        self.conn.commit()

        self.last_known_data: Optional[tuple[dict[str, WordRecord], KnownMetadata]] = None
        self.last_known_data_date: float = 0.0  # 1970-01-01

    def _createTables(self):
        self.c.execute("""
        CREATE TABLE IF NOT EXISTS lookups (
            timestamp REAL,
            word TEXT,
            lemma TEXT,
            language TEXT,
            lemmatization INTEGER,
            source TEXT,
            success INTEGER,
            UNIQUE(timestamp, lemma)
        )
        """)
        self.c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            timestamp REAL,
            data TEXT,
            success INTEGER,
            sentence TEXT,
            word TEXT,
            definition TEXT,
            definition2 TEXT,
            pronunciation TEXT,
            image TEXT,
            tags TEXT
        )
        """)
        self.c.execute("""
        CREATE TABLE IF NOT EXISTS seen_new (
            language TEXT,
            lemma TEXT,
            count INTEGER DEFAULT 1,
            UNIQUE(language, lemma)
        )
        """)
        self.c.execute("""
        CREATE TABLE IF NOT EXISTS contents (
            id INTEGER NOT NULL PRIMARY KEY,
            language TEXT,
            name TEXT UNIQUE,
            jd INTEGER,
            content TEXT
        )
        """)
        self.c.execute("""
        CREATE TABLE IF NOT EXISTS modifiers (
                        language TEXT,
                        lemma TEXT,
                        value FLOAT,
                        UNIQUE(language, lemma)
        )
        """)
        self.c.execute("""
                       CREATE UNIQUE INDEX IF NOT EXISTS modifier_index ON modifiers (language, lemma)
        """)
        # Non-unique index for seen_new
        self.c.execute("""CREATE INDEX IF NOT EXISTS seen_index_lang ON seen_new (language)""")
        # Clean up old seen table
        self.c.execute("""DROP TABLE IF EXISTS seen""")
        self.c.execute("""VACUUM""")
        self.conn.commit()

    def _makeLookupUnique(self):
        """
        In the past, lookups were not unique, which made it very slow
        to avoid inserting duplicates"""
        self.c.execute("""
            CREATE TABLE temp_lookups AS SELECT * FROM lookups GROUP BY lemma, timestamp
        """)
        self.c.execute("""
            DROP TABLE lookups
        """)
        self.c.execute("""
            ALTER TABLE temp_lookups RENAME TO lookups
        """)
        self.c.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS lookup_index ON lookups (timestamp, lemma)
        """)
        self.conn.commit()

    def _seenContent(self, name, content, language):
        start = time.time()
        for word in content.replace("\\n", "\n").replace("\\N", "\n").split():
            lemma = lem_word(word, language)
            self.c.execute("""
                    INSERT INTO seen_new(language, lemma) VALUES(?,?)
                    ON CONFLICT(language, lemma) DO UPDATE SET count = count + 1
            """, (language, lemma))
        self.conn.commit()
        logger.info("Lemmatized", name, "in", time.time() - start, "seconds")

    def importContent(self, name: str, content: str, language: str, jd: int):
        start = time.time()
        self.c.execute('SELECT * FROM contents WHERE (name=?)', (name,))
        exists = self.c.fetchone()
        if not exists:
            sql = """INSERT INTO contents(name, content, language, jd)
                    VALUES(?,?,?,?)"""
            self.c.execute(
                sql,
                (name, content, language, jd))

            self.c.execute("SELECT last_insert_rowid()")
            source = self.c.fetchone()[0]
            logger.debug("ID for content", name, "is", source)
            self._seenContent(name, content, language)
            self.conn.commit()
            logger.debug("Recorded", name, "in", time.time() - start, "seconds")
            return True
        logger.info(name, "already exists")
        return False

    def getContents(self, language):
        return self.c.execute('''
            SELECT name, content, jd
            FROM contents
            WHERE language=?''', (language,))

    def getModifier(self, language, lemma) -> float:
        self.c.execute('''
            SELECT value
            FROM modifiers
            WHERE language=? AND lemma=?''', (language, lemma))
        value = self.c.fetchone()
        if value:
            return cast(float, value[0])
        else:
            return 1.0

    def setModifier(self, language, lemma, value):
        self.c.execute('''
            INSERT OR REPLACE INTO modifiers(language, lemma, value)
            VALUES(?,?,?)''', (language, lemma, value))
        self.conn.commit()

    def rebuildSeen(self):
        self.c.execute("DELETE FROM seen_new")
        self.c.execute('SELECT id, name, content, language, jd FROM contents')
        for _, name, content, language, _ in self.c.fetchall():
            self._seenContent(name, content, language)
        self.conn.commit()
        self.c.execute("VACUUM")

    def getSeen(self, language):
        cursor = self.conn.cursor()
        return cursor.execute('''
            SELECT lemma, count
            FROM seen_new
            WHERE language=?
            ''', (language,))

    def countSeen(self, language):
        self.c.execute('''
            SELECT SUM (count), COUNT (DISTINCT lemma)
            FROM seen_new
            WHERE language=?''', (language,))
        return self.c.fetchone()

    def deleteContent(self, name: str):
        self.c.execute("""
            DELETE FROM contents
            WHERE name=?
        """, (name,))
        self.conn.commit()
        self.c.execute("VACUUM")

    def deleteModifiers(self, langcode: str):
        "Drop all modifiers for given language"
        self.c.execute("""
            DELETE FROM modifiers
            WHERE language=?
        """, (langcode,))
        self.conn.commit()
        self.c.execute("VACUUM")

    def recordLookup(self, lr: LookupRecord, timestamp: Optional[float] = None, commit: bool = True):
        if timestamp is None:
            timestamp = time.time()
        sql = """INSERT OR IGNORE INTO lookups(timestamp, word, lemma, language, lemmatization, source, success)
                VALUES(?,?,?,?,?,?,?)"""
        self.c.execute(
            sql,
            (
                timestamp,
                lr.word,
                lem_word(lr.word, lr.language),
                lr.language,
                True,
                lr.source,
                True
            )
        )
        if commit:
            self.conn.commit()

    def recordNote(self, sn: SRSNote, content: str, commit: bool = True):
        timestamp = time.time()
        sql = """INSERT INTO notes(
            timestamp, data, sentence, word, definition, definition2, pronunciation, image, tags, success
            )
            VALUES(?,?,?,?,?,?,?,?,?,?)"""
        self.c.execute(sql,
                       (
                           timestamp,
                           content,
                           sn.sentence or "",
                           sn.word or "",
                           sn.definition1 or "",
                           sn.definition2 or "",
                           sn.audio_path or "",
                           sn.image or "",
                           " ".join(sn.tags) if sn.tags else "",
                           1
                       )
                       )
        if commit:
            self.conn.commit()

    def getAllLookups(self):
        return self.c.execute("SELECT timestamp, word, lemma, language, lemmatization, source, success FROM lookups")

    def getAllNotes(self):
        return self.c.execute("SELECT * FROM notes")

    def countLemmaLookups(self, word, language):
        self.c.execute(
            '''SELECT COUNT (DISTINCT date(timestamp, "unixepoch")) FROM lookups WHERE lemma=?''',
            (lem_word(
                word,
                language),
             ))
        return self.c.fetchone()[0]

    def countLookups(self, language):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT COUNT (*) FROM lookups WHERE language=?''', (language,))
        return cursor.fetchone()[0]

    def countAllLemmaLookups(self, language):
        cursor = self.conn.cursor()
        return cursor.execute(
            '''SELECT lemma, COUNT (DISTINCT date(timestamp, "unixepoch"))
               FROM lookups
               WHERE language=?
               GROUP BY lemma
            ''', (language,))

    def countLookupsToday(self):
        day = datetime.now()
        return self.countLookupsDay(day)

    def countNotesToday(self):
        day = datetime.now()
        return self.countNotesDay(day)

    def countLookupsDay(self, day):
        start = day.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0).timestamp()
        end = day.replace(hour=23, minute=59, second=59,
                          microsecond=999999).timestamp()
        try:
            self.c.execute("""SELECT COUNT (DISTINCT word)
                            FROM lookups
                            WHERE timestamp
                            BETWEEN ? AND ?
                            AND success = 1 """, (start, end))
            return self.c.fetchone()[0]
        except sqlite3.ProgrammingError:
            return -1

    def countNotesDay(self, day):
        start = day.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0).timestamp()
        end = day.replace(hour=23, minute=59, second=59,
                          microsecond=999999).timestamp()
        try:
            self.c.execute("""SELECT COUNT (timestamp)
                            FROM notes
                            WHERE timestamp
                            BETWEEN ? AND ?
                            AND success = 1 """, (start, end))
            return self.c.fetchone()[0]
        except sqlite3.ProgrammingError:
            return -1

    def purge(self):
        self.c.execute("""
        DROP TABLE IF EXISTS lookups,notes,contents,seen_new,seen
        """)
        self._createTables()
        self.c.execute("VACUUM")

    def getKnownData(self) -> tuple[dict[str, WordRecord], KnownMetadata]:
        lifetime = settings.value('tracking/known_data_lifetime', 1800, type=int)  # Seconds
        if self.last_known_data is None:
            logger.debug("No known data in this session. Creating known data from database..")
            self.last_known_data = self._refreshKnownData()
            self.last_known_data_date = time.time()
            return self.last_known_data
        else:
            known_data_age = time.time() - self.last_known_data_date
            if known_data_age > lifetime:
                logger.debug(f"Known data is {known_data_age:.2f} s old, "
                             f"which is older than the specified lifetime of {lifetime} s. Refreshing..")
                self.last_known_data = self._refreshKnownData()
                self.last_known_data_date = time.time()
                return self.last_known_data
            else:
                logger.debug(f"Known data is {known_data_age:.2f} s old, "
                             f"which is newer than the specified lifetime of {lifetime} s. Not refreshing now.")
                return self.last_known_data

    @staticmethod
    def process_notes_info(notes_info: dict,
                           result: dict[str, WordRecord],
                           tgt_key: str,
                           ctx_key: str,
                           fieldmap: dict[str, list[str]],
                           langcode: str) -> tuple[list[str], list[str]]:
        tgt_lemmas = []
        ctx_lemmas = []
        for info in notes_info:
            model = info['modelName']
            word_field, ctx_field = fieldmap.get(model) or ("<Ignore>", "<Ignore>")
            word = ""
            ctx = ""
            lemma = ""
            if word_field != "<Ignore>":
                word = info['fields'][word_field]['value']
            if ctx_field != "<Ignore>":
                ctx = info['fields'][ctx_field]['value']
            if word:
                lemma = word  # word field is assumed to be already lemmatized
                tgt_lemmas.append(lemma)
                try:
                    setattr(result[lemma], tgt_key, getattr(result[lemma], tgt_key) + 1)
                except KeyError:
                    result[lemma] = WordRecord(lemma=lemma, language=langcode, **{tgt_key: 1})
            if ctx:
                this_ctx_lemmas = set(map(lambda w: lem_word(w, langcode), re.sub(r"<.*?>", " ", ctx).split()))
                if lemma:  # Don't count if already counted as word
                    this_ctx_lemmas.discard(lemma)
                for ctx_lemma in this_ctx_lemmas:
                    ctx_lemmas.append(ctx_lemma)
                    try:
                        setattr(result[ctx_lemma], ctx_key, getattr(result[ctx_lemma], ctx_key) + 1)
                    except KeyError:
                        result[ctx_lemma] = WordRecord(lemma=ctx_lemma, language=langcode, **{ctx_key: 1})
        return tgt_lemmas, ctx_lemmas

    def _refreshKnownData(self) -> tuple[dict[str, WordRecord], KnownMetadata]:

        langcode = settings.value('target_language', 'en')

        result: dict[str, WordRecord] = {}

        start = time.time()

        metadata = KnownMetadata()

        for lemma, count in self.countAllLemmaLookups(langcode):
            metadata.n_lookups += 1
            result[lemma] = WordRecord(lemma=lemma, language=langcode, n_lookups=count)

        logger.debug(f"Processed lookup data in {time.time() - start:.2f} seconds")

        start = time.time()
        for lemma, count in self.getSeen(langcode):
            metadata.n_seen += 1
            try:
                result[lemma].n_seen = count
            except KeyError:
                result[lemma] = WordRecord(lemma=lemma, language=langcode, n_seen=count)

        logger.debug(f"Processed seen data in {time.time() - start:.2f} seconds")

        start = time.time()

        if not settings.value('enable_anki', True, type=bool):
            logger.debug("Anki disabled, skipping")
            result = {k: v for k, v in result.items() if k.isalpha() and not k.startswith('http') and " " not in k}
            return result, metadata
        fieldmap = json.loads(settings.value("tracking/fieldmap", "{}"))

        anki_api = settings.value("anki_api", "http://127.0.0.1:8765")

        mature_notes = findNotes(
            anki_api,
            settings.value("tracking/anki_query_mature")
        )
        young_notes = findNotes(
            anki_api,
            settings.value("tracking/anki_query_young")
        )
        young_notes = [note for note in young_notes if note not in mature_notes]

        logger.debug(f"Received anki data from AnkiConnect in {time.time() - start:.2f} seconds")
        start = time.time()
        mature_notes_info = notesInfo(anki_api, mature_notes)
        young_notes_info = notesInfo(anki_api, young_notes)

        mature_tgt_lemmas, mature_ctx_lemmas = self.process_notes_info(
            mature_notes_info,
            result,
            "anki_mature_tgt",
            "anki_mature_ctx",
            fieldmap,
            langcode
        )
        young_tgt_lemmas, young_ctx_lemmas = self.process_notes_info(
            young_notes_info,
            result,
            "anki_young_tgt",
            "anki_young_ctx",
            fieldmap,
            langcode
        )
        metadata.n_mature_ctx = len(mature_ctx_lemmas)
        metadata.n_mature_tgt = len(mature_tgt_lemmas)
        metadata.n_young_ctx = len(young_ctx_lemmas)
        metadata.n_young_tgt = len(young_tgt_lemmas)

        logger.debug(f"Processed anki data in {time.time() - start:.2f} seconds")

        result = {k: v for k, v in result.items() if k.isalpha() and not k.startswith('http') and " " not in k}
        return result, metadata
