import json
import urllib.request
import requests
import os
import re
import time
from bs4 import BeautifulSoup
from typing import List, Dict
from .db import *
from pystardict import Dictionary
from .dictionary import *
from .dictformats import *
from .xdxftransform import xdxf2html
from PyQt5.QtCore import QCoreApplication


def request(action, **params):
    return {'action': action, 'params': params, 'version': 6}


def invoke(action, server, **params):
    requestJson = json.dumps(request(action, **params)).encode('utf-8')
    response = json.load(
        urllib.request.urlopen(
            urllib.request.Request(
                server, requestJson)))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def getDeckList(server) -> list:
    result = invoke('deckNames', server)
    return list(result)


def getNoteTypes(server) -> list:
    result = invoke('modelNames', server)
    return list(result)


def getFields(server, name) -> list:
    result = invoke('modelFieldNames', server, modelName=name)
    return list(result)


def addNote(server, content) -> int:
    result = invoke('addNote', server, note=content)
    return int(result)


def addNotes(server, content) -> List[int]:
    result = invoke('addNotes', server, notes=content)
    return list(result)


def getVersion(server) -> str:
    result = invoke('version', server)
    return str(result)


def is_json(myjson) -> bool:
    if not myjson.startswith("{"):
        return False
    try:
        json_object = json.loads(myjson)
        json_object['word']
        json_object['sentence']
    except ValueError as e:
        return False
    except Exception as e:
        print(e)
        return False
    return True


def failed_lookup(word, settings) -> str:
    return str("<b>Definition for \"" + str(word) + "\" not found.</b><br>Check the following:<br>" +
               "- Language setting (Current: " + settings.value("target_language", 'en') + ")<br>" +
               "- Is the correct word being looked up?<br>" +
               "- Are you connected to the Internet?<br>" +
               "Otherwise, then " + settings.value("dict_source", "Wiktionary (English)") +
               " probably just does not have this word listed.")


def is_oneword(s) -> bool:
    return len(s.split()) == 1

def freq_to_stars(freq_num, lemmatize):
    if lemmatize:
        if freq_num <= 1000:
            return "★★★★★"
        elif freq_num <= 3000:
            return "★★★★☆"
        elif freq_num <= 8000:
            return "★★★☆☆"
        elif freq_num <= 20000:
            return "★★☆☆☆"
        elif freq_num <= 40000:
            return "★☆☆☆☆"
        else:
            return "☆☆☆☆☆"
    else:
        if freq_num <= 1500:
            return "★★★★★"
        elif freq_num <= 5000:
            return "★★★★☆"
        elif freq_num <= 15000:
            return "★★★☆☆"
        elif freq_num <= 30000:
            return "★★☆☆☆"
        elif freq_num <= 60000:
            return "★☆☆☆☆"
        else:
            return "☆☆☆☆☆"

def dictimport(path, dicttype, lang, name) -> None:
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
        dictdb.importdict(d, lang, name)
    elif dicttype == "json":
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
            dictdb.importdict(d, lang, name)
    elif dicttype == "migaku":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            d = {}
            for item in data:
                d[item['term']] = item['definition']
            dictdb.importdict(d, lang, name)
    elif dicttype == "freq":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            d = {}
            for i, word in enumerate(data):
                d[word] = str(i + 1)
            dictdb.importdict(d, lang, name)
    elif dicttype == "audiolib":
        # Audios will be stored as a serialized json list
        filelist = []
        d = {}
        for root, dirs, files in os.walk(path):
            for item in files:
                filelist.append(
                    os.path.relpath(
                        os.path.join(
                            root, item), path))
        for item in filelist:
            headword = os.path.basename(os.path.splitext(item)[0]).lower()
            if not d.get(headword):
                d[headword] = [item]
            else:
                d[headword].append(item)
        for word in d.keys():
            d[word] = json.dumps(d[word])
        dictdb.importdict(d, lang, name)
    elif dicttype == 'mdx':
        d = parseMDX(path)
        dictdb.importdict(d, lang, name)
    elif dicttype == "dsl":
        d = parseDSL(path)
        dictdb.importdict(d, lang, name)
    elif dicttype == "csv":
        d = parseCSV(path)
        dictdb.importdict(d, lang, name)
    elif dicttype == "tsv":
        d = parseTSV(path)
        dictdb.importdict(d, lang, name)


def dictdelete(name) -> None:
    dictdb.deletedict(name)
