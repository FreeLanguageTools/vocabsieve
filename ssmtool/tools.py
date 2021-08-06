import json
import urllib.request
import requests
import os
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
            "- Language setting (Current: " + setting.value("target_language", 'English') + ")<br>" +\
            "- Is the correct word being looked up?<br>" +\
            "- Are you connected to the Internet?<br>" +\
            "Otherwise, then " + setting.value("dict_source", "Wiktionary (English)") + " probably just does not have this word listed."

def is_oneword(s):
    return len(s.split()) == 1

def dictinfo(path):
    "Get information about dictionary from file path"
    basename, ext = os.path.splitext(path)
    basename = os.path.basename(basename)
    if ext not in [".json", ".ifo"]:
        return "Unsupported format"
    elif ext == ".json":
        with open(path) as f:
            try:
                d = json.load(f)
                if type(d) == list:
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
        dictdb.importdict(dict(stardict), lang, name)
    elif dicttype == "json":
        with open(path) as f:
            data = json.load(f)
            dictdb.importdict(data, lang, name)
    elif dicttype == "migaku":
        with open(path) as f:
            data = json.load(f)
            d = {}
            for item in data:
                d[item['term']] = item['definition']
            dictdb.importdict(d, lang, name)
    else:
        print("Error:", str(dicttype), "is not supported.")
        raise NotImplementedError

def dictrebuild(dicts):
    dictdb.purge()
    for item in dicts:
        dictimport(item['path'], item['type'], item['lang'], item['name'])