
from ast import parse
import sqlite3
import os

from .dictformats import parseMDX, parseDSL, parseCSV, parseTSV, xdxf2text, zopen, parseKaikki
from .lemmatizer import removeAccents
from pystardict import Dictionary
import json
from .global_names import lock, datapath as datapath_


class LocalDictionary():
    def __init__(self, datapath) -> None:
        path = os.path.join(datapath, "dict.db")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.c = self.conn.cursor()
        self.createTables()
        self.makeIndex()

    def makeIndex(self) -> None:
        try:
            self.c.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS dictionary_index ON dictionary(language, dictname, word)
            """)  # Faster lookups
            self.c.execute("""
            CREATE INDEX IF NOT EXISTS dictname_index ON dictionary(dictname)
            """)  # Faster counting of entries
            print("Either successfully made unique index, or there is already one")
        except sqlite3.IntegrityError:
            print("Unable to make unique index")

    def createTables(self) -> None:
        self.c.execute("""
        CREATE TABLE IF NOT EXISTS dictionary (
            word TEXT,
            definition TEXT,
            language TEXT,
            dictname TEXT
        )
        """)
        self.conn.commit()

    def importdict(self, data: dict[str, str], lang: str, name: str) -> None:
        for item in data.items():
            # Handle escape sequences
            self.c.execute("""
                INSERT INTO dictionary(word, definition, language, dictname)
                VALUES(?, ?, ?, ?)
                """,
                           (
                               item[0],
                               item[1].replace("\\n", "\n"),
                               lang,
                               name
                           )
                           )
        self.conn.commit()

    def deletedict(self, name: str) -> None:
        self.c.execute("""
            DELETE FROM dictionary
            WHERE dictname=?
        """, (name,))
        self.conn.commit()
        self.c.execute("VACUUM")

    def getCognates(self, lang: str) -> sqlite3.Cursor:
        return self.c.execute("""
            SELECT word, definition FROM dictionary
            WHERE language=?
            AND dictname='cognates'
            """, (lang,))

    def hasCognatesData(self) -> bool:
        self.c.execute("""
            SELECT COUNT(*) FROM dictionary
            WHERE dictname='cognates'
            """)
        return bool(self.c.fetchone()[0] > 0)

    def define(self, word: str, lang: str, name: str) -> str:
        """
        Get definition from database
        Should raise KeyError if word not found
        """
        self.c.execute("""
            SELECT definition FROM dictionary
            WHERE word=?
            AND language=?
            AND dictname=?
            """, (word, lang, name))
        if results := self.c.fetchone():
            return str(results[0])
        else:
            raise KeyError(f"Word {word} not found in {name}")

    def getAllWords(self, lang: str, name: str) -> list[tuple[str, str]]:
        """
        Get all words from database
        Should raise KeyError if word not found
        """
        self.c.execute("""
        SELECT word, definition FROM dictionary
        WHERE language=?
        AND dictname=?
        """, (lang, name))
        return self.c.fetchall()

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

    def getNamesForLang(self, lang: str) -> list[str]:
        self.c.row_factory = lambda cursor, row: row[0]
        self.c.execute("""
        SELECT DISTINCT dictname FROM dictionary
        WHERE language=?
        """, (lang,))
        res = self.c.fetchall()
        self.c.row_factory = None
        return res

    def purge(self) -> None:
        self.c.execute("""
        DROP TABLE IF EXISTS dictionary
        """)
        self.createTables()
        self.c.execute("VACUUM")

    @staticmethod
    def regularize_headword(word: str) -> str:
        "If headword is all caps, convert it to all lowercase"
        return removeAccents(word.lower() if word.isupper() else word)

    def dictimport(self, path, dicttype, lang, name) -> None:
        "Import dictionary from file to database"
        d: dict[str, str] = {}
        if dicttype == "stardict":
            stardict = Dictionary(os.path.splitext(path)[0], in_memory=True)
            if stardict.ifo.sametypesequence == 'x':
                for key in stardict.idx.keys():

                    d[self.regularize_headword(key)] = xdxf2text(stardict.dict[key])
            else:
                for key in stardict.idx.keys():
                    d[self.regularize_headword(key)] = stardict.dict[key]
            self.importdict(d, lang, name)
        elif dicttype == "json":
            with zopen(path) as f:
                d = json.load(f)
                self.importdict(d, lang, name)
        elif dicttype == "migaku":
            with zopen(path) as f:
                data = json.load(f)
                for item in data:
                    key = self.regularize_headword(item['term'])
                    if not d.get(key):  # fix for duplicate entries
                        d[key] = item['definition']
                    else:
                        d[key] += "\n" + item['definition']
                self.importdict(d, lang, name)
        elif dicttype == "wiktdump":
            self.importdict(parseKaikki(path, lang), lang, name)
        elif dicttype == "freq":
            with zopen(path) as f:
                data = json.load(f)
                i = 0
                for word in data:
                    if word and not word[0].isupper():  # Ignore proper nouns
                        d[self.regularize_headword(word)] = str(i + 1)
                        i += 1
                self.importdict(d, lang, name)
        elif dicttype == "audiolib":
            # Audios will be stored as a serialized json list
            filelist = []
            list_d: dict[str, list[str]] = {}
            for root, _, files in os.walk(path):
                for item in files:
                    filelist.append(
                        os.path.relpath(
                            os.path.join(
                                root, item), path))
            for item in filelist:
                headword = os.path.basename(os.path.splitext(item)[0]).lower()
                if not list_d.get(headword):
                    list_d[self.regularize_headword(headword)] = [item]
                else:
                    list_d[self.regularize_headword(headword)].append(item)
            for word, audios in list_d.items():
                d[word] = json.dumps(audios)
            self.importdict(d, lang, name)
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
            for lang_ in cognates_d:
                data = {k: json.dumps(v) for k, v in cognates_d[lang_].items()}
                self.importdict(data, lang_, name)
        else:
            raise ValueError(f"Unknown dictionary type {dicttype}")

    def dictdelete(self, name) -> None:
        self.deletedict(name)

    def getCognatesData(self, language: str, known_langs: list[str]) -> set[str]:
        "Get all cognates from the local database in a given language"
        data = self.getCognates(language)
        known_langs = [lang.strip() for lang in known_langs]
        if not known_langs:
            return set()
        if not known_langs[0]:
            return set()
        cognates = []
        for word, cognates_in in data:
            for lang in known_langs:
                if lang in cognates_in:
                    cognates.append(word)
                    break
        return set(cognates)


dictdb = LocalDictionary(datapath_)
