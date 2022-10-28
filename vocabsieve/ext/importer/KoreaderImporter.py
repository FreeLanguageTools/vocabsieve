from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from io import BytesIO
import os
import re
import glob
import json
from pathlib import Path
from difflib import SequenceMatcher
from sentence_splitter import split_text_into_sentences
from vocabsieve.tools import addNotes
from vocabsieve.dictionary import getAudio
from datetime import datetime
from itertools import compress
from slpp import slpp
from lxml import etree
from ebooklib import epub, ITEM_DOCUMENT

from .utils import *


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

def removesuffix(self: str, suffix: str, /) -> str:
    # suffix='' should not call self[:-0].
    if suffix and self.endswith(suffix):
        return self[:-len(suffix)]
    else:
        return self[:]

def koreader_parse_fb2(file, lang):
    result = []
    notepath = os.path.join(
        os.path.dirname(file), removesuffix(file, "fb2") + "sdr", "metadata.fb2.lua"
    )
    with open(notepath) as f:
        notes = slpp.decode(" ".join("\n".join(f.readlines()[1:]).split(" ")[1:]))['bookmarks'].items()
    print(notepath)
    root = etree.parse(file).getroot()
    ns = {'f': "http://www.gribuser.ru/xml/fictionbook/2.0"}
    for _, item in notes:
        try:
            xpath = fb2_xpathconvert(item['page'])
            word_start = int(item['pos0'].split(".")[-1])
            word_end = int(item['pos1'].split(".")[-1])
            if root.xpath(xpath, namespaces=ns):
                ctx = root.xpath(xpath, namespaces=ns)[0].text
                for sentence in split_text_into_sentences(ctx, language=lang):
                    if item['notes'] in sentence:
                        if ctx.find(sentence) < word_start \
                            and ctx.find(sentence) + len(sentence) > word_end: 
                            result.append((item['notes'], sentence, item['datetime']))
        except KeyError:
            continue
    return result



def koreader_parse_epub(file, lang):
    result = []
    notepath = os.path.join(
        os.path.dirname(file), removesuffix(file, "epub") + "sdr", "metadata.epub.lua"
    )
    with open(notepath) as f:
        notes = slpp.decode(" ".join("\n".join(f.readlines()[1:]).split(" ")[1:]))['bookmarks'].items()
    docs = []
    for doc in epub.read_epub(file).get_items_of_type(ITEM_DOCUMENT):
        docs.append(
            etree.parse(BytesIO(doc.get_content())).getroot()
        )
    ns = {'f': 'http://www.w3.org/1999/xhtml'}
    for _, item in notes:
        try:
            index, xpath = epub_xpathconvert(item['page'])
            word_start = int(item['pos0'].split(".")[-1])
            word_end = int(item['pos1'].split(".")[-1])
            if docs[index].xpath(xpath, namespaces=ns):
                ctx = docs[index].xpath(xpath, namespaces=ns)[0].text
                for sentence in split_text_into_sentences(ctx, language=lang):
                    if item['notes'] in sentence:
                        if ctx.find(sentence) < word_start \
                            and ctx.find(sentence) + len(sentence) > word_end: 
                            result.append((item['notes'], sentence, item['datetime']))
                            break
        except KeyError:
            continue
    return result

def koreader_scandir(path):
    filelist = []
    epubs = glob.glob(os.path.join(path, "**/*.epub"), recursive=True)
    for filename in epubs:
        if os.path.exists(os.path.join(os.path.dirname(filename), 
                            removesuffix(filename, "epub") + "sdr", 
                            "metadata.epub.lua")):
            filelist.append(filename)
    fb2s = glob.glob(os.path.join(path, "**/*.fb2"), recursive=True)
    for filename in fb2s:
        if os.path.exists(os.path.join(os.path.dirname(filename), 
                          removesuffix(filename, "fb2") + "sdr", 
                          "metadata.fb2.lua")):
            filelist.append(filename)
    return filelist


class KoreaderImporter(QDialog):
    def __init__(self, parent, path):
        super().__init__(parent)
        self.settings = parent.settings
        self.lang = parent.settings.value('target_language')
        self.setWindowTitle("Import KOReader notes")
        self.parent = parent
        self.resize(700, 500)
        self.datewidget = QComboBox()
        self.layout = QFormLayout(self)
        self.layout.addRow(QLabel(
            "<h2>Import KOReader notes</h2>"
        ))
        self.layout.addRow(QLabel(
            "<strong>Only Epub and FB2 formats are supported. PDF books will not work.</strong>"
        ))
        self.layout.addRow(QLabel(
            "<hr><h3>Select which books to retrieve notes from:</h3>"
        ))
        self.bookfiles = koreader_scandir(path)

        self.book_selector = []
        for item in self.bookfiles:
            self.book_selector.append(
                QCheckBox(truncate_middle(os.path.basename(item),90))
            )
            self.layout.addRow(self.book_selector[-1])
        start_import_button = QPushButton("Finished selecting")
        self.layout.addRow(start_import_button)
        start_import_button.clicked.connect(self.getNotes)
        self.lookup_button = QPushButton("Look up words")
        self.lookup_button.setEnabled(False)

    def getNotes(self):
        book_selected = list(
            map(lambda w: w.isChecked(), self.book_selector)
        )
        # This applies book_selected as mask
        books = compress(self.bookfiles, book_selected)
        items = []
        for bookfile in books:
            if bookfile.endswith("fb2"):
                items.extend(
                    koreader_parse_fb2(bookfile, self.lang)
                )
            elif bookfile.endswith("epub"):
                items.extend(
                    koreader_parse_epub(bookfile, self.lang)
                )
        self.lookup_terms, self.sents, self.dates = zip(*items)
        self.datewidget.addItems(uniq_preserve_order(
            [date[:10] for date in self.dates]))
        self.layout.addRow(QLabel("Start from date"), self.datewidget)
        extract_sentences_button = QPushButton("Extract sentences from chosen date")
        self.layout.addRow(QLabel("Get sentences"), extract_sentences_button)
        extract_sentences_button.clicked.connect(self.extractSentences)

    def extractSentences(self):
        start_date = self.datewidget.currentText()
        self.lookup_terms, self.sents = zip(*compress(
            zip(self.lookup_terms, self.sents), 
            map(lambda d: d>start_date, self.dates)
            ))
        self.layout.addRow(QLabel(f"{len(list(zip(self.lookup_terms, self.sents)))} notes extracted."), self.lookup_button)
        self.lookup_button.setEnabled(True)
        self.lookup_button.clicked.connect(self.define_words)


    def define_words(self):
        self.lookup_button.setEnabled(False)
        self.sentences = []
        self.words = []
        self.definitions = []
        self.definition2s = []
        self.audio_paths = []
        
        self.definition_count_label = QLabel("0 definitions found")
        self.anki_button = QPushButton("Add notes to Anki")
        self.anki_button.setEnabled(False)
        self.anki_button.clicked.connect(self.to_anki)
        self.layout.addRow(self.definition_count_label, self.anki_button)

        count = 0
        for i in range(len(self.lookup_terms)):
            # Remove punctuations
            word = re.sub('[\\?\\.!«»…,()\\[\\]]*', "", self.lookup_terms[i])

            if self.sents[i]:
                if self.settings.value("bold_word", True, type=bool):
                    self.sentences.append(self.sents[i].replace("_", "").replace(word, f"__{word}__"))
                    
                else:
                    self.sentences.append(self.sents[i])
                item = self.parent.lookup(word, record=False)
                if not item['definition'].startswith("<b>Definition for"):
                    count += 1
                    self.words.append(item['word'])
                    self.definitions.append(item['definition'])
                    self.definition_count_label.setText(
                        str(count) + " definitions found")
                    QApplication.processEvents()
                else:
                    self.words.append(word)
                    self.definitions.append("")
                self.definition2s.append(item.get('definition2', ""))

                audio_path = ""
                if self.settings.value("audio_dict", "Forvo (all)") != "<disabled>":
                    try:
                        audios = getAudio(
                                word,
                                self.settings.value("target_language", 'en'),
                                dictionary=self.settings.value("audio_dict", "Forvo (all)"),
                                custom_dicts=json.loads(
                                    self.settings.value("custom_dicts", '[]')))
                    except Exception:
                        audios = {}
                    if audios:
                        # First item
                        audio_path = audios[next(iter(audios))]
                self.audio_paths.append(audio_path)
        
            else:
                print("no sentence")
                #self.sentences.append("")
                #self.definitions.append("")
                #self.words.append("")
                #self.definition2s.append("")
                #self.audio_paths.append("")

        self.anki_button.setEnabled(True)

    def to_anki(self):
        notes = []
        for word, sentence, definition, definition2, audio_path in zip(
                self.words, self.sentences, self.definitions, self.definition2s, self.audio_paths):
            if word and sentence and definition:
                if self.settings.value("bold_word", True, type=bool):
                    sentence = re.sub(
                        r"__([ \w]+)__",
                        r"<strong>\1</strong>",
                        sentence
                        )
                tags = self.parent.settings.value(
                    "tags", "vocabsieve").strip() + " koreader"
                content = {
                    "deckName": self.parent.settings.value("deck_name"),
                    "modelName": self.parent.settings.value("note_type"),
                    "fields": {
                        self.parent.settings.value("sentence_field"): sentence,
                        self.parent.settings.value("word_field"): word,
                    },
                    "tags": tags.split(" ")
                }
                definition = definition.replace("\n", "<br>")
                content['fields'][self.parent.settings.value(
                    'definition_field')] = definition
                if self.settings.value("dict_source2", "<disabled>") != '<disabled>':
                    definition2 = definition2.replace("\n", "<br>")
                    content['fields'][self.parent.settings.value('definition2_field')] = definition2
                if self.settings.value("audio_dict", "<disabled>") != '<disabled>' and audio_path:
                    content['audio'] = {}
                    if audio_path.startswith("https://") or audio_path.startswith("http://"):
                        content['audio']['url'] = audio_path
                    else:
                        content['audio']['path'] = audio_path
                    content['audio']['filename'] = audio_path.replace("\\", "/").split("/")[-1]
                    content['audio']['fields'] = [self.settings.value('pronunciation_field')]

                print(content)
                notes.append(content)
        res = addNotes(self.parent.settings.value("anki_api"), notes)
        self.layout.addRow(QLabel(str(len(notes)) +
                                  " notes have been exported, of which " +
                                  str(len([i for i in res if i])) +
                                  " were successfully added to your collection."))
        self.anki_button.setEnabled(False)