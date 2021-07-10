import json
import urllib.request
import unicodedata

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

def removeAccents(word):
    print("Removing accent marks from query ", word)
    ACCENT_MAPPING = {
        '́': '',
        '̀': '',
        'а́': 'а',
        'а̀': 'а',
        'е́': 'е',
        'ѐ': 'е',
        'и́': 'и',
        'ѝ': 'и',
        'о́': 'о',
        'о̀': 'о',
        'у́': 'у',
        'у̀': 'у',
        'ы́': 'ы',
        'ы̀': 'ы',
        'э́': 'э',
        'э̀': 'э',
        'ю́': 'ю',
        '̀ю': 'ю',
        'я́́': 'я',
        'я̀': 'я',
    }
    word = unicodedata.normalize('NFKC', word)
    for old, new in ACCENT_MAPPING.items():
        word = word.replace(old, new)
    print("Remaining: ", word)
    return word
