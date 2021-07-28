import json
import urllib.request
import requests
from bs4 import BeautifulSoup



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

