import sqlite3
import os
import time
from bidict import bidict
from datetime import datetime
from .constants import langcodes
from .lemmatizer import lem_word

dictionaries = bidict({"Wiktionary (English)": "wikt-en",
                       "Google Translate": "gtrans"})


class Record():
    def __init__(self, parent, datapath):
        self.conn = sqlite3.connect(
            os.path.join(
                datapath,
                "records.db"),
            check_same_thread=False)
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA foreign_keys = ON")
        self.createTables()
        self.fixOld()
        if not parent.settings.value("internal/db_has_lemma"):
            self.lemmatizeLookups()
            parent.settings.setValue("internal/db_has_lemma", True)
        if not parent.settings.value("internal/db_no_definitions"):
            self.dropDefinitions()
            parent.settings.setValue("internal/db_no_definitions", True)
        if not parent.settings.value("internal/db_new_source"):
            self.fixSource()
            parent.settings.setValue("internal/db_new_source", True)
        self.conn.commit()
        if not parent.settings.value("internal/seen_has_no_word"):
            self.fixSeen()
            parent.settings.setValue("internal/seen_has_no_word", True)
        if not parent.settings.value("internal/timestamps_are_seconds", True):
            self.fixBadTimestamps()
            parent.settings.setValue("internal/timestamps_are_seconds", True)
        if not parent.settings.value("internal/lookup_unique_index"):
            self.makeLookupUnique()
            parent.settings.setValue("internal/lookup_unique_index", True)
        self.conn.commit()

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
            word_to_lemma = {}
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


    def recordLookup(
            self,
            word: str,
            language: str,
            lemmatization: bool,
            source: str,
            success: bool,
            timestamp: float,
            commit: bool = True):
        lemma = lem_word(word, language) # For statistics, so it is used even if lemmatization is off
        sql = """INSERT OR IGNORE INTO lookups(timestamp, word, lemma, language, lemmatization, source, success)
                VALUES(?,?,?,?,?,?,?)"""
        self.c.execute(
            sql,
            (timestamp,
            word,
            lemma,
            language,
            lemmatization,
            source,
            success))
        if commit:
            self.conn.commit()



    def recordNote(self, data, sentence, word, definition, definition2, pronunciation, image, tags, success):
        timestamp = time.time()
        sql = """INSERT INTO notes(
            timestamp, data, sentence, word, definition, definition2, pronunciation, image, tags, success
            ) 
            VALUES(?,?,?,?,?,?,?,?,?,?)"""
        self.c.execute(sql, 
            (
                timestamp, 
                data, 
                sentence or "", 
                word or "", 
                definition or "", 
                definition2 or "", 
                pronunciation or "", 
                image or "", 
                tags or "",
                success
            )
        )
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


