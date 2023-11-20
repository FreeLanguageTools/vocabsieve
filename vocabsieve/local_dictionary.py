
import sqlite3
import os
import time
from .dictformats import parseMDX, parseDSL, parseCSV, parseTSV, zopen
from .xdxftransform import xdxf2html
from .lemmatizer import removeAccents
from pystardict import Dictionary
import json
from typing import Optional

class LocalDictionary():
    def __init__(self, datapath):
        path = os.path.join(datapath, "dict.db")
        print("Initializing local dictionary object at ", path)
        self.conn = sqlite3.connect(path, check_same_thread=False)
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
            # Handle escape sequences
            self.c.execute("""
                INSERT INTO dictionary(word, definition, language, dictname)
                VALUES(?, ?, ?, ?)
                """,
                           (
                               removeAccents(item[0].lower() if item[0].isupper() else item[0]),  # no caps
                               item[1].replace("\\n", "\n"),
                               lang,
                               name
                           )
                           )
        self.conn.commit()

    def deletedict(self, name: str):
        self.c.execute("""
            DELETE FROM dictionary
            WHERE dictname=?
        """, (name,))
        self.conn.commit()
        self.c.execute("VACUUM")

    def getCognates(self, lang: str):
        return self.c.execute("""
            SELECT word, definition FROM dictionary
            WHERE language=?
            AND dictname='cognates'
            """, (lang,))

    def hasCognatesData(self):
        self.c.execute("""
            SELECT COUNT(*) FROM dictionary
            WHERE dictname='cognates'
            """)
        return self.c.fetchone()[0] > 0

    def define(self, word: str, lang: str, name: str) -> str:
        self.c.execute("""
        SELECT definition FROM dictionary
        WHERE word=?
        AND language=?
        AND dictname=?
        """, (word, lang, name))
        return str(self.c.fetchone()[0])

    def countEntries(self) -> int:
        self.c.execute("""
        SELECT COUNT(*) FROM dictionary
        """)
        return int(self.c.fetchone()[0])

    def countEntriesDict(self, name) -> int:
        self.c.execute("""
        SELECT COUNT(*) FROM dictionary
        WHERE dictname=?
        """, (name,))
        return int(self.c.fetchone()[0])

    def countDicts(self) -> int:
        self.c.execute("""
        SELECT COUNT(DISTINCT dictname) FROM dictionary
        """)
        return int(self.c.fetchone()[0])

    def getNamesForLang(self, lang: str):
        self.c.row_factory = lambda cursor, row: row[0]
        self.c.execute("""
        SELECT DISTINCT dictname FROM dictionary
        WHERE language=?
        """, (lang,))
        res = self.c.fetchall()
        self.c.row_factory = None
        return res

    def purge(self):
        self.c.execute("""
        DROP TABLE IF EXISTS dictionary
        """)
        self.createTables()
        self.c.execute("VACUUM")

    def dictimport(self, path, dicttype, lang, name) -> None:
        "Import dictionary from file to database"
        if dicttype == "stardict":
            stardict = Dictionary(os.path.splitext(path)[0], in_memory=True)
            d = {}
            if stardict.ifo.sametypesequence == 'x':
                for key in stardict.idx.keys():
                    d[key] = xdxf2html(stardict.dict[key])
            else:
                for key in stardict.idx.keys():
                    d[key] = stardict.dict[key]
            self.importdict(d, lang, name)
        elif dicttype == "json":
            with zopen(path) as f:
                d = json.load(f)
                self.importdict(d, lang, name)
        elif dicttype == "migaku":
            with zopen(path) as f:
                data = json.load(f)
                d = {}
                for item in data:
                    d[item['term']] = item['definition']
                self.importdict(d, lang, name)
        elif dicttype == "freq":
            with zopen(path) as f:
                data = json.load(f)
                d = {}
                for i, word in enumerate(data):
                    d[word] = str(i + 1)
                self.importdict(d, lang, name)
        elif dicttype == "audiolib":
            # Audios will be stored as a serialized json list
            filelist = []
            list_d: dict[str, list[str]] = {}
            d = {}
            for root, dirs, files in os.walk(path):
                for item in files:
                    filelist.append(
                        os.path.relpath(
                            os.path.join(
                                root, item), path))
            for item in filelist:
                headword = os.path.basename(os.path.splitext(item)[0]).lower()
                if not list_d.get(headword):
                    list_d[headword] = [item]
                else:
                    list_d[headword].append(item)
            for word in list_d.keys():
                d[word] = json.dumps(list_d[word])
            self.importdict(list_d, lang, name)
        elif dicttype == 'mdx':
            d = parseMDX(path)
            self.importdict(d, lang, name)
        elif dicttype == "dsl":
            d = parseDSL(path)
            self.importdict(d, lang, name)
        elif dicttype == "csv":
            d = parseCSV(path)
            self.importdict(d, lang, name)
        elif dicttype == "tsv":
            d = parseTSV(path)
            self.importdict(d, lang, name)
        elif dicttype == "cognates":
            with zopen(path) as f:
                cognates_d: dict[str, dict[str, list[str]]] = json.load(f)
            for lang in cognates_d:
                data = {k: json.dumps(v) for k, v in cognates_d[lang].items()}
                self.importdict(data, lang, name)


    def dictdelete(self, name) -> None:
        self.deletedict(name)

    def getCognatesData(self, language: str, known_langs: list) -> Optional[list[str]]:
        "Get all cognates from the local database in a given language"
        start = time.time()
        data = self.getCognates(language)
        if not known_langs:
            return []
        if not known_langs[0]:
            return []
        cognates = []
        for word, cognates_in in data:
            for lang in known_langs:
                if lang in cognates_in:
                    cognates.append(word)
                    break
        print("Got all cognates in", time.time() - start, "seconds")
        return cognates