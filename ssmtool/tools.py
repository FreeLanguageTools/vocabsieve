import json
import urllib.request
import unicodedata
import pymorphy2
import requests
from bs4 import BeautifulSoup
morph = pymorphy2.MorphAnalyzer()

code = {
    "English": "en",
    "Chinese": "zh",
    "Italian": "it",
    "Finnish": "fi",
    "Japanese": "ja",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Latin": "la",
    "Polish": "pl",
    "Portuguese": "pt",
    "Russian": "ru",
    "Serbo-Croatian": "sh",
    "Dutch": "nl",
    "Romanian": "ro"
}


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

def fmt_result(definitions):
    "Format the result of dictionary lookup"
    lines = []
    for defn in definitions:
        lines.append("<i>" + defn['pos'] + "</i>")
        lines.extend([str(item[0]+1) + ". " + item[1] for item in list(enumerate(definitions[0]['meaning']))])
    return "<br>".join(lines)

def wiktionary(word, language, lemmatize=True):
    "Get definitions from Wiktionary"

    if lemmatize and language == 'ru':
        word = lem_word(word)
    res = requests.get('https://en.wiktionary.org/api/rest_v1/page/definition/' + word)
    if res.status_code != 200:
        raise Exception("Lookup error")
    definitions = []
    data = res.json()[language]
    for item in data:
        meanings = []
        for defn in item['definitions']:
            
            parsed_meaning = BeautifulSoup(defn['definition'], features="lxml")
 
            uninflected_forms_count = len(parsed_meaning.select("span.form-of-definition-link"))
            if uninflected_forms_count == 0 or not lemmatize:
                meaning = parsed_meaning.text
            else:
                next_target = parsed_meaning.select_one("span.form-of-definition-link")\
                    .select_one("a")['title']
                print(next_target)
                return wiktionary(next_target, language, lemmatize=False)
            
            meanings.append(meaning)
            
        meaning_item = {"pos": item['partOfSpeech'], "meaning": meanings}
        definitions.append(meaning_item)
    return {"word": word, "definition": definitions}

def lem_word(word):
    return morph.parse(word)[0].normal_form