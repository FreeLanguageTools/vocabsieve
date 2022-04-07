import json
import urllib.request
import requests
import os
import re
from bs4 import BeautifulSoup
from .db import *
from pystardict import Dictionary
from .dictionary import *

def request(action, **params):
    return {'action': action, 'params': params, 'version': 6}

def invoke(action, server, **params):
    requestJson = json.dumps(request(action, **params)).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request(server, requestJson)))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']

def getDeckList(server):
    result = invoke('deckNames', server)
    return result

def getNoteTypes(server):
    result = invoke('modelNames', server)
    return result

def getFields(server, name):
    result = invoke('modelFieldNames', server, modelName=name)
    return result

def addNote(server, content):
    result = invoke('addNote', server, note=content)
    return result

def addNotes(server, content):
    result = invoke('addNotes', server, notes=content)
    return result

def getVersion(server):
    result = invoke('version', server)
    return result

def is_json(myjson):
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

def failed_lookup(word, setting):
    return "<b>Definition for \"" + str(word) + "\" not found.</b><br>Check the following:<br>" +\
            "- Language setting (Current: " + setting.value("target_language", 'en') + ")<br>" +\
            "- Is the correct word being looked up?<br>" +\
            "- Are you connected to the Internet?<br>" +\
            "Otherwise, then " + setting.value("dict_source", "Wiktionary (English)") + " probably just does not have this word listed."

def is_oneword(s):
    return len(s.split()) == 1

def dictinfo(path):
    "Get information about dictionary from file path"
    basename, ext = os.path.splitext(path)
    basename = os.path.basename(basename)
    if os.path.isdir(path):
        return {"type": "audiolib", "basename": basename, "path": path}
    if ext not in [".json", ".ifo"]:
        return "Unsupported format"
    elif ext == ".json":
        with open(path, encoding="utf-8") as f:
            try:
                d = json.load(f)
                if type(d) == list:
                    if type(d[0]) == str:
                        return {"type": "freq", "basename": basename, "path": path}
                    return {"type": "migaku", "basename": basename, "path": path}
                elif type(d) == dict:
                    return {"type": "json", "basename": basename, "path": path}
            except Exception:
                return "Unsupported format"
    elif ext == ".ifo":
        return {"type": "stardict", "basename": basename, "path": path}

def dictimport(path, dicttype, lang, name):
    "Import dictionary from file to database"
    if dicttype == "stardict":
        stardict = Dictionary(os.path.splitext(path)[0])
        newdict = {}
        for key in stardict.idx.keys():
            newdict[key] = re.sub('<[^>]*>', '', stardict.dict[key])
        dictdb.importdict(newdict, lang, name)
    elif dicttype == "json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            dictdb.importdict(data, lang, name)
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
                d[word] = i+1
            dictdb.importdict(d, lang, name)
    elif dicttype == "audiolib":
        # Audios will be stored as a serialized json list
        filelist = []
        d = {}
        for root, dirs, files in os.walk(path):
            for item in files:
                filelist.append(os.path.relpath(os.path.join(root, item), path))
        print(len(filelist), "audios selected.")
        for item in filelist:
            headword = os.path.basename(os.path.splitext(item)[0]).lower()
            if not d.get(headword):
                d[headword] = [item]
            else:
                d[headword].append(item)
        for word in d.keys():
            d[word] = json.dumps(d[word])
        dictdb.importdict(d, lang, name)

    else:
        print("Error:", str(dicttype), "is not supported.")
        raise NotImplementedError

def dictrebuild(dicts):
    dictdb.purge()
    for item in dicts:
        try:
            dictimport(item['path'], item['type'], item['lang'], item['name'])
        except Exception as e:
            print(e)