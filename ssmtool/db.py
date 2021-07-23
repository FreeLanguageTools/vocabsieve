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
        print(path.join(datapath, "records.db"))
        self.conn = sqlite3.connect(path.join(datapath, "records.db"))
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
        timestamp = time.time()
        sql = """INSERT INTO lookups(timestamp, word, definition, language, lemmatization, source, success)
                VALUES(?,?,?,?,?,?,?)"""
        self.c.execute(sql, (timestamp, word, definition, language, lemmatization, source, success))
        self.conn.commit()

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
        self.c.execute("""SELECT timestamp 
                          FROM lookups 
                          WHERE timestamp 
                          BETWEEN ? AND ?
                          AND success = 1 """, (start, end))
        return len(self.c.fetchall())

    def countNotesDay(self, day):
        start = day.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        end = day.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp()
        self.c.execute("""SELECT timestamp 
                          FROM notes 
                          WHERE timestamp 
                          BETWEEN ? AND ?
                          AND success = 1 """, (start, end))
        return len(self.c.fetchall())
        

        

if __name__ == "__main__":
    db = Record()
    #db.recordLookup("word", "sample-def", True, "wikt-en")
    print("\n".join([str(item) for item in db.getAll()]))
    print("Lookups today:", db.countLookupsToday())
    print("Lookups yesterday:", db.countLookupsDay(datetime.now() - timedelta(days=1)))