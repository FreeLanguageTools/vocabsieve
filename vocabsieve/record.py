from calendar import c
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
from .tools import getVersion, findNotes, notesInfo
from loguru import logger

dictionaries = bidict({"Wiktionary (English)": "wikt-en",
                       "Google Translate": "gtrans"})


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
        self.settings = parent_settings
        self.createTables()
        self.fixOld()
        if not parent_settings.value("internal/db_has_lemma"):
            self.lemmatizeLookups()
            parent_settings.setValue("internal/db_has_lemma", True)
        if not parent_settings.value("internal/db_no_definitions"):
            self.dropDefinitions()
            parent_settings.setValue("internal/db_no_definitions", True)
        if not parent_settings.value("internal/db_new_source"):
            self.fixSource()
            parent_settings.setValue("internal/db_new_source", True)
        self.conn.commit()
        if not parent_settings.value("internal/seen_has_no_word"):
            self.fixSeen()
            parent_settings.setValue("internal/seen_has_no_word", True)
        if not parent_settings.value("internal/timestamps_are_seconds", True):
            self.fixBadTimestamps()
            parent_settings.setValue("internal/timestamps_are_seconds", True)
        if not parent_settings.value("internal/lookup_unique_index"):
            self.makeLookupUnique()
            parent_settings.setValue("internal/lookup_unique_index", True)

        self.last_known_data: Optional[tuple[dict[str, WordRecord], KnownMetadata]] = None
        self.last_known_data_date: float = 0.0 # 1970-01-01

    def fixSeen(self):
        try:
            self.c.execute("""
                ALTER TABLE seen DROP COLUMN word
                """)
            self.conn.commit()
            self.c.execute("VACUUM")
        except Exception as e:
            print(e)

    def fixSource(self):
        self.c.execute("""
            UPDATE lookups SET source='vocabsieve'
            """)
        self.conn.commit()

    def fixBadTimestamps(self):
        "In the past some lookups were imported with millisecond timestamps"
        self.c.execute("""
            UPDATE lookups SET timestamp=timestamp/1000 WHERE timestamp > 1000000000000
            """)

    def createTables(self):
        self.c.execute("""
        CREATE TABLE IF NOT EXISTS lookups (
            timestamp FLOAT,
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
            timestamp FLOAT,
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
        CREATE TABLE IF NOT EXISTS seen (
            language TEXT,
            lemma TEXT,
            jd INTEGER,
            source INTEGER,
            FOREIGN KEY(source) REFERENCES contents(id) ON DELETE CASCADE
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
        self.conn.commit()

    def fixOld(self):
        """
        1. In the past language name rather than code was recorded
        2. In the past some dictonaries had special names.
        3. Add proper columns in the notes table rather than just a json dump
        """
        self.c.execute("""
        SELECT DISTINCT language FROM lookups
        """)
        for languagename, in self.c.fetchall():  # comma unpacks a single value tuple
            if not langcodes.get(languagename) and langcodes.inverse.get(languagename):
                print(f"Replacing {languagename} with {langcodes.inverse[languagename]}")
                self.c.execute("""
                UPDATE lookups SET language=? WHERE language=?
                """, (langcodes.inverse[languagename], languagename))
                self.conn.commit()
        self.c.execute("""
        SELECT DISTINCT source FROM lookups
        """)
        for source, in self.c.fetchall():  # comma unpacks a single value tuple
            if source in dictionaries.inverse:
                print(f"Replacing {source} with {dictionaries.inverse[source]}")
                self.c.execute("""
                UPDATE lookups SET source=? WHERE source=?
                """, (dictionaries.inverse[source], source))
                self.conn.commit()
        try:
            self.c.executescript("""
                ALTER TABLE notes ADD COLUMN sentence TEXT;
                ALTER TABLE notes ADD COLUMN word TEXT;
                ALTER TABLE notes ADD COLUMN definition TEXT;
                ALTER TABLE notes ADD COLUMN definition2 TEXT;
                ALTER TABLE notes ADD COLUMN pronunciation TEXT;
                ALTER TABLE notes ADD COLUMN image TEXT;
                ALTER TABLE notes ADD COLUMN tags TEXT;
            """)
        except sqlite3.OperationalError:
            pass
        self.c.execute("VACUUM")

    def makeLookupUnique(self):
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


    def dropDefinitions(self):
        print('dropping definition')
        try:
            self.c.execute("""ALTER TABLE lookups DROP COLUMN definition""")
            self.c.execute("VACUUM")
        except Exception as e:
            print(e)
        return

    def lemmatizeLookups(self):
        "In the past, lemmas were not recorded during lookups. This applies it to older rows"
        try:
            print("Trying to add lemma column to lookups table..")
            self.c.execute("""
                ALTER TABLE lookups ADD COLUMN lemma TEXT;
            """)
            langiter = self.c.execute("""
                SELECT DISTINCT language FROM lookups
            """)
            word_to_lemma: dict[str, dict[str, str]] = {}
            for lang in langiter:
                print("Found lang:", lang[0])
                word_to_lemma[lang[0]] = {} #Make 2d dict

            wordlangiter = self.c.execute("""
                SELECT DISTINCT word, language FROM lookups
            """)
            for word, lang in wordlangiter:
                print("lemma of", word, "in", lang, "is", lem_word(word, lang))
                word_to_lemma[lang][word] = lem_word(word, lang)

            for lang in word_to_lemma:
                for word in word_to_lemma[lang]:
                    self.c.execute('''UPDATE lookups SET lemma=? WHERE word=? AND language=?''',
                        (word_to_lemma[lang][word], word, lang))
            self.conn.commit()
        except sqlite3.OperationalError:
            print("encountered error, likely because column already exists")

    def seenContent(self, cid, name, content, language, jd):
        start = time.time()
        for word in content.replace("\\n", "\n").replace("\\N", "\n").split():
            lemma = lem_word(word, language)
            self.c.execute('INSERT INTO seen(source, language, lemma, jd) VALUES(?,?,?,?)', (cid, language, lemma, jd))
        print("Lemmatized", name, "in", time.time() - start, "seconds")

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
            print("ID for content", name, "is", source)
            self.seenContent(source, name, content, language, jd)
            self.conn.commit()
            print("Recorded", name, "in", time.time() - start, "seconds")
            return True
        print(name, "already exists")
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
        self.c.execute("DELETE FROM seen")
        self.c.execute('SELECT id, name, content, language, jd FROM contents')
        for cid, name, content, language, jd in self.c.fetchall():
            print("Lemmatizing", name)
            self.seenContent(cid, name, content, language, jd)
        self.conn.commit()
        self.c.execute("VACUUM")

    def getSeen(self, language):
        return self.c.execute('''
            SELECT lemma, COUNT (lemma)
            FROM seen
            WHERE language=?
            GROUP BY lemma''', (language,))

    def countSeen(self, language):
        self.c.execute('''
            SELECT COUNT(lemma), COUNT (DISTINCT lemma)
            FROM seen
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
        self.c.execute('''SELECT COUNT (DISTINCT date(timestamp, "unixepoch")) FROM lookups WHERE lemma=?''', (lem_word(word, language),))
        return self.c.fetchone()[0]

    def countLookups(self, language):
        self.c.execute('''SELECT COUNT (*) FROM lookups WHERE language=?''', (language,))
        return self.c.fetchone()[0]

    def countAllLemmaLookups(self, language):
        return self.c.execute(
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
            return self.c.fetchall()[0][0]
        except sqlite3.ProgrammingError:
            return

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
            return self.c.fetchall()[0][0]
        except sqlite3.ProgrammingError:
            return

    def purge(self):
        self.c.execute("""
        DROP TABLE IF EXISTS lookups,notes,contents,seen
        """)
        self.createTables()
        self.c.execute("VACUUM")

    def getKnownData(self) -> tuple[dict[str, WordRecord], KnownMetadata]:
        lifetime = self.settings.value('tracking/known_data_lifetime', 1800, type=int) # Seconds
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

        langcode = self.settings.value('target_language', 'en')

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
        
        if not self.settings.value('enable_anki', True, type=bool):
            logger.debug("Anki disabled, skipping")
            result = {k: v for k, v in result.items() if k.isalpha() and not k.startswith('http') and " " not in k}
            return result, metadata
        fieldmap = json.loads(self.settings.value("tracking/fieldmap",  "{}"))

        anki_api = self.settings.value("anki_api", "127.0.0.1:8765")
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


