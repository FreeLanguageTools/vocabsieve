import sqlite3
from PyQt5.QtCore import QStandardPaths, QCoreApplication
from os import path
from pathlib import Path
import time
from datetime import datetime, timedelta

QCoreApplication.setApplicationName("ssmtool")
QCoreApplication.setOrganizationName("FreeLanguageTools")
datapath = QStandardPaths.writableLocation(QStandardPaths.DataLocation)
Path(datapath).mkdir(parents=True, exist_ok=True)

class Record():
    def __init__(self):
        #print(path.join(datapath, "records.db"))
        self.conn = sqlite3.connect(path.join(datapath, "records.db"), check_same_thread=False)
        self.c = self.conn.cursor()
        self.createTables()

    def createTables(self):
        self.c.execute("""
        CREATE TABLE IF NOT EXISTS lookups (
            timestamp FLOAT,
            word TEXT,
            definition TEXT,
            language TEXT,
            lemmatization INTEGER,
            source TEXT,
            success INTEGER
        )
        """)
        self.c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            timestamp FLOAT,
            data TEXT,
            success INTEGER
        )
        """)
        self.conn.commit()

    def recordLookup(self, word, definition, language, lemmatization, source, success):
        try:
            timestamp = time.time()
            sql = """INSERT INTO lookups(timestamp, word, definition, language, lemmatization, source, success)
                    VALUES(?,?,?,?,?,?,?)"""
            self.c.execute(sql, (timestamp, word, definition, language, lemmatization, source, success))
            self.conn.commit()
        except sqlite3.ProgrammingError:
            return

    def recordNote(self, data, success):
        timestamp = time.time()
        sql = "INSERT INTO notes(timestamp, data, success) VALUES(?,?,?)"
        self.c.execute(sql, (timestamp, data, success))
        self.conn.commit()

    def getAll(self):
        self.c.execute("SELECT * FROM lookups")
        return self.c.fetchall()

    def countLookupsToday(self):
        day = datetime.now()
        return self.countLookupsDay(day)

    def countNotesToday(self):
        day = datetime.now()
        return self.countNotesDay(day)

    def countLookupsDay(self, day):
        start = day.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        end = day.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp()
        try:
            self.c.execute("""SELECT timestamp 
                            FROM lookups 
                            WHERE timestamp 
                            BETWEEN ? AND ?
                            AND success = 1 """, (start, end))
            return len(self.c.fetchall())
        except sqlite3.ProgrammingError:
            return
    def countNotesDay(self, day):
        start = day.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        end = day.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp()
        try:
            self.c.execute("""SELECT timestamp 
                            FROM notes 
                            WHERE timestamp 
                            BETWEEN ? AND ?
                            AND success = 1 """, (start, end))
            return len(self.c.fetchall())
        except sqlite3.ProgrammingError:
            return

    def purge(self):
        self.c.execute("""
        DROP TABLE IF EXISTS lookups,notes
        """)
        self.createTables()

class LocalDictionary():
    def __init__(self):
        #print(path.join(datapath, "dict.db"))
        self.conn = sqlite3.connect(path.join(datapath, "dict.db"), check_same_thread=False)
        self.c = self.conn.cursor()
        self.createTables()

    def createTables(self):
        self.c.execute("""
        CREATE TABLE IF NOT EXISTS dictionary (
            word TEXT,
            definition TEXT,
            language TEXT,
            dictname TEXT
        )
        """)
        self.conn.commit()
    
    def importdict(self, data: dict, lang: str, name: str):
        for item in data.items():
            self.c.execute("""
            INSERT INTO dictionary(word, definition, language, dictname)
            VALUES(?, ?, ?, ?)
            """, (item[0], item[1], lang, name))
        self.conn.commit()

    def define(self, word: str, lang: str, name: str) -> str:
        self.c.execute("""
        SELECT definition FROM dictionary
        WHERE word=?
        AND language=?
        AND dictname=?
        """,(word, lang, name))
        return self.c.fetchone()[0]

    def countEntries(self) -> int:
        self.c.execute("""
        SELECT COUNT(*) FROM dictionary
        """)
        return self.c.fetchone()[0]

    def countDicts(self) -> int:
        self.c.execute("""
        SELECT COUNT(DISTINCT dictname) FROM dictionary
        """)
        return self.c.fetchone()[0]

    def getNamesForLang(self, lang: str):
        self.c.row_factory = lambda cursor, row: row[0]
        self.c.execute("""
        SELECT DISTINCT dictname FROM dictionary
        WHERE language=?
        """,(lang,))
        res = self.c.fetchall()
        self.c.row_factory = None
        return res

    def purge(self):
        self.c.execute("""
        DROP TABLE IF EXISTS dictionary
        """)
        self.createTables()
        
if __name__ == "__main__":
    db = Record()
    #db.recordLookup("word", "sample-def", True, "wikt-en")
    print("\n".join([str(item) for item in db.getAll()]))
    print("Lookups today:", db.countLookupsToday())
    print("Lookups yesterday:", db.countLookupsDay(datetime.now() - timedelta(days=1)))
    di = LocalDictionary()
    #print(di.define("test", "en", "testdict"))
    print("Names", di.getNamesForLang("ru"))
    print(di.define("test", "en", "Oxford Dictionary of English - No Examples"))
    print(di.countEntries())