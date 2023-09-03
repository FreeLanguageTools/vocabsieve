from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from io import BytesIO
import os
import re
from zipfile import ZipFile
from slpp import slpp
from lxml import etree
from ebooklib import epub, ITEM_DOCUMENT

from .GenericImporter import GenericImporter
from .utils import *
from ..tools import *


def fb2_xpathconvert(s):
    s = "/".join(s.split("/")[2:-1])
    s = ("/" + s).replace("/", "/f:")
    return "." + s

def epub_xpathconvert(s):
    index = int(re.findall('DocFragment\[(\d+)\]', s)[0])
    s = "/body" + s.split("body")[-1]
    s = "/".join(s.split("/")[:-1])
    s = s.replace("/", "/f:")
    return (index, "." + s)

def koreader_parse_fb2(file, lang):
    result = []
    notepath = os.path.join(
        os.path.dirname(file), removesuffix(os.path.basename(file), "fb2") + "sdr", "metadata.fb2.lua"
    )
    with open(notepath, encoding='utf-8') as f:
        data = slpp.decode(" ".join("\n".join(f.readlines()[1:]).split(" ")[1:]))
        notes = data['bookmarks'].items()
        booklang = data['doc_props']['language']
        if '-' in booklang:
            booklang = booklang[:2]
    root = etree.parse(file).getroot()
    ns = {'f': "http://www.gribuser.ru/xml/fictionbook/2.0"}
    try:
        booktitle = root.xpath("f:description/f:title-info/f:book-title", namespaces=ns)[0].text
    except Exception:
        booktitle = removesuffix(os.path.basename(file), ".fb2")
    result.append(("", "", "1970-01-01 00:00:00", booktitle, booklang))

    for _, item in notes:
        try:
            xpath = fb2_xpathconvert(item['page'])
            word_start = int(item['pos0'].split(".")[-1])
            word_end = int(item['pos1'].split(".")[-1])
            if root.xpath(xpath, namespaces=ns):
                ctx = root.xpath(xpath, namespaces=ns)[0].text
                for sentence in split_to_sentences(ctx, language=lang):
                    if item['notes'] in sentence:
                        if ctx.find(sentence) < word_start \
                            and ctx.find(sentence) + len(sentence) > word_end: 
                            result.append((item['notes'], sentence, item['datetime'], booktitle, booklang))
        except KeyError:
            continue
    return result


def koreader_parse_fb2zip(file, lang):
    result = []
    notepath = os.path.join(
        os.path.dirname(file), removesuffix(os.path.basename(file), "zip") + "sdr", "metadata.zip.lua"
    )
    with open(notepath, encoding='utf8') as f:
        data = slpp.decode(" ".join("\n".join(f.readlines()[1:]).split(" ")[1:]))
        notes = data['bookmarks'].items()
        booklang = data['doc_props']['language']
    print(notepath)
    with ZipFile(file, 'r') as f:
        for file_in_zip in f.namelist():
            if file_in_zip.endswith(".fb2"):
                content = f.read(file_in_zip)
    root = etree.ElementTree(etree.fromstring(content)).getroot()
    ns = {'f': "http://www.gribuser.ru/xml/fictionbook/2.0"}
    try:
        booktitle = root.xpath("f:description/f:title-info/f:book-title", namespaces=ns)[0].text
    except Exception:
        booktitle = removesuffix(os.path.basename(file), ".fb2.zip")
    result.append(("", "", "1970-01-01 00:00:00", booktitle, booklang))
    for _, item in notes:
        try:
            xpath = fb2_xpathconvert(item['page'])
            word_start = int(item['pos0'].split(".")[-1])
            word_end = int(item['pos1'].split(".")[-1])
            if root.xpath(xpath, namespaces=ns):
                ctx = root.xpath(xpath, namespaces=ns)[0].text
                for sentence in split_to_sentences(ctx, language=lang):
                    if item['notes'] in sentence:
                        if ctx.find(sentence) < word_start \
                            and ctx.find(sentence) + len(sentence) > word_end: 
                            result.append((item['notes'], sentence, item['datetime'], booktitle, booklang))
        except KeyError:
            continue
    return result



def find_sentence_for_word(item, doc, lang):
    ns = {'f': 'http://www.w3.org/1999/xhtml'}
    index, xpath = epub_xpathconvert(item['page'])
    word_start = int(item['pos0'].split(".")[-1])
    word_end = int(item['pos1'].split(".")[-1])
    if doc.xpath(xpath, namespaces=ns):
        ctx = doc.xpath(xpath, namespaces=ns)[0].text
        for sentence in split_to_sentences(ctx, language=lang):
            if item['notes'] in sentence:
                if ctx.find(sentence) < word_start \
                    and ctx.find(sentence) + len(sentence) > word_end: 
                    return sentence
    

def koreader_parse_epub(file, lang):
    result = []
    notepath = os.path.join(
        os.path.dirname(file), removesuffix(os.path.basename(file), "epub") + "sdr", "metadata.epub.lua"
    )
    with open(notepath, encoding='utf8') as f:
        data = slpp.decode(" ".join("\n".join(f.readlines()[1:]).split(" ")[1:]))
        notes = data['bookmarks'].items()
        booklang = data['doc_props']['language']
    print(notepath)
    docs = []
    booktitle = epub.read_epub(file).get_metadata('DC', 'title')[0][0].strip() or removesuffix(os.path.basename(file), "epub")
    result.append(("", "", "1970-01-01 00:00:00", booktitle, booklang))
    for doc in epub.read_epub(file).get_items_of_type(ITEM_DOCUMENT):
        docs.append(
            etree.parse(BytesIO(doc.get_content())).getroot()
        )
    ns = {'f': 'http://www.w3.org/1999/xhtml'}
    for _, item in notes:
        found = False
        try:
            index, _ = epub_xpathconvert(item['page'])
            print(len(docs), "docs in", booktitle)
            if index < len(docs):
                if sentence:=find_sentence_for_word(item, docs[index], lang):
                    result.append((
                        item['notes'],
                        sentence,
                        item['datetime'],
                        booktitle,
                        booklang
                    ))
                    found = True
            if not found: #Ordering is weird, loop through all docs
                for doc in docs:
                    if sentence:=find_sentence_for_word(item, doc, lang):
                        result.append((
                            item['notes'],
                            sentence,
                            item['datetime'],
                            booktitle,
                            booklang
                        ))
                        found = True
                
        except KeyError:
            continue
    return result

class KoreaderImporter(GenericImporter):
    def __init__(self, parent, path):
        super().__init__(parent, "KOReader highlights", path, "koreader")

    def getNotes(self):
        self.bookfiles = koreader_scandir(self.path)
        print(self.bookfiles)
        langcode = self.parent.settings.value("target_language", "en")
        items = []
        for bookfile in self.bookfiles:
            if bookfile.endswith("fb2"):
                items.extend(
                    koreader_parse_fb2(bookfile, self.lang)
                )
            elif bookfile.endswith("epub"):
                items.extend(
                    koreader_parse_epub(bookfile, self.lang)
                )
            elif bookfile.endswith("fb2.zip"):
                items.extend(
                    koreader_parse_fb2zip(bookfile, self.lang)
                )
        print(len(items))
        notitems = [item[:4] for item in items if item[4] != langcode]
        items = [item[:4] for item in items if item[4] == langcode]
        print(len(items))
        print(notitems)
        books_in_lang = set(item[3] for item in items)
        print("Books in", langcode, ":", books_in_lang)
        try:
            self.histpath = findHistoryPath(self.path)
            d = []
            with open(self.histpath) as f:
                with open(self.histpath) as f:
                    content = f.read().split("LookupHistoryEntry")[1:]
                    for item in content:
                        d.append(slpp.decode(item))
            entries = [entry['data'].get(next(iter(entry['data']))) for entry in d]
            entries = [(entry['word'], entry['book_title'], entry['time']) for entry in entries]
            count = 0
            success_count = 0
            for word, booktitle, timestamp in entries:
                if booktitle in books_in_lang:
                    count += 1
                    success_count += self.parent.rec.recordLookup(word, langcode, True, "koreader", True, timestamp, commit=False)
            self.parent.rec.conn.commit()

            self.layout.addRow(QLabel("Lookup history: " + self.histpath))
            self.layout.addRow(QLabel(f"Found {count} lookups in {langcode}, added {success_count} to lookup database."))
        except Exception as e:
            print(e)
            self.layout.addRow(QLabel("Failed to find/read lookup_history.lua. Lookups will not be tracked this time."))

        items = [item for item in items if item[2] > "1970-01-01 00:00:00"]
        return zip(*items)


    