import json
import urllib.request

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