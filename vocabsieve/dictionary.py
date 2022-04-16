import json
import unicodedata
import simplemma
import re
import requests
import pycountry
from urllib.parse import quote
from bs4 import BeautifulSoup
from bidict import bidict
import pymorphy2
from .db import *
from playsound import playsound
from .forvo import *
dictdb = LocalDictionary()
langdata = simplemma.load_data('en')


# Currently, all languages with two letter codes can be set
langcodes = bidict(dict(zip([l.alpha_2 for l in list(pycountry.languages) if getattr(l, 'alpha_2', None)],
                     [l.name for l in list(pycountry.languages) if getattr(l, 'alpha_2', None)])))
# Apply patches
langcodes['el'] = "Greek"
for item in langcodes:
    langcodes[item] = re.sub(r'\s?\([^)]*\)$', '', langcodes[item])
langcodes['zh_HANT'] = "Chinese (Traditional)"
langcodes['haw'] = "Hawaiian"
langcodes['ceb'] = "Cebuano"
langcodes['hmn'] = "Hmong"


gtrans_languages = ['af', 'sq', 'am', 'ar', 'hy', 'az', 'eu', 'be', 'bn',
    'bs', 'bg', 'ca', 'ceb', 'ny', 'zh', 'zh_HANT', 'co', 'hr', 'cs', 'da', 'nl',
    'en', 'eo', 'et', 'tl', 'fi', 'fr', 'fy', 'gl', 'ka', 'de', 'el', 'gu', 'ht',
    'ha', 'haw', 'hi', 'hmn', 'hu', 'is', 'ig', 'id', 'ga', 'it', 'ja', 'kn', 'kk', 
    'km', 'rw', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'lt', 'lb',
    'mk', 'mg', 'ms', 'ml', 'mt', 'mi', 'mr', 'mn', 'my', 'ne', 'no', 'or', 'ps',
    'fa', 'pl', 'pt', 'pa', 'ro', 'ru', 'sm', 'gd', 'sr', 'st', 'sn', 'sd', 'si',
    'sk', 'sl', 'so', 'es', 'su', 'sw', 'sv', 'tg', 'ta', 'tt', 'te', 'th', 'tr',
    'tk', 'uk', 'ur', 'ug', 'uz', 'vi', 'cy', 'xh', 'yi', 'yo', 'zu']

langs_supported = bidict(dict(zip(gtrans_languages, [langcodes[item] for item in gtrans_languages])))

gdict_languages = ['en', 'hi', 'es', 'fr', 'ja', 'ru', 'de', 'it', 'ko', 'ar', 'tr', 'pt']
simplemma_languages = ['bg', 'ca', 'cy', 'da', 'de', 'en', 'es', 'et', 'fa', 'fi', 'fr',
                       'ga', 'gd', 'gl', 'gv', 'hu', 'id', 'it', 'ka', 'la', 'lb', 'lt',
                       'lv', 'nl', 'pt', 'ro', 'ru', 'sk', 'sl', 'sv', 'tr', 'uk', 'ur']
dictionaries = bidict({"Wiktionary (English)": "wikt-en",
                "Google dictionary (Monolingual)": "gdict",
                "Google Translate": "gtrans"})
pronunciation_sources = ["Forvo (all)", "Forvo (best)"]

# On Windows frozen build, there is no pymorphy2 support for Russian due to an issue with cxfreeze
PYMORPHY_SUPPORT = False
try:
    morph = pymorphy2.MorphAnalyzer(lang="ru")
    PYMORPHY_SUPPORT = True
except ValueError:
    morph = None
    pass



def preprocess_clipboard(s: str, lang: str) -> str:
    """
    Pre-process string from clipboard before showing it
    NOTE: originally intended for parsing JA and ZH, but 
    that feature has been removed for the time being due
    to maintainence and dependency concerns.
    """
    return s

    
def removeAccents(word):
    #print("Removing accent marks from query ", word)
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
    return word

def fmt_result(definitions):
    "Format the result of dictionary lookup"
    lines = []
    for defn in definitions:
        if defn['pos'] != "":
            lines.append("<i>" + defn['pos'] + "</i>")
        lines.extend([str(item[0]+1) + ". " + item[1] for item in list(enumerate(defn['meaning']))])
    return "<br>".join(lines)

def lem_word(word, language):
    """Lemmatize a word. We will use PyMorphy for RU, simplemma for others, 
    and if that isn't supported , we give up."""
    if language == 'ru' and PYMORPHY_SUPPORT:
        return morph.parse(word)[0].normal_form
    elif language in simplemma_languages:
        global langdata
        if langdata[0][0] != language:
            langdata = simplemma.load_data(language)
            return lem_word(word, language)
        else:
            return simplemma.lemmatize(word, langdata)
    else:
        return word

def wiktionary(word, language, lemmatize=True):
    "Get definitions from Wiktionary"
    try:
        res = requests.get('https://en.wiktionary.org/api/rest_v1/page/definition/' + word, timeout=4)
    except Exception as e:
        print(e)

    if res.status_code != 200:
        raise Exception("Lookup error")
    definitions = []
    data = res.json()[language]
    for item in data:
        meanings = []
        for defn in item['definitions']:
            parsed_meaning = BeautifulSoup(defn['definition'], features="lxml")
            meanings.append(parsed_meaning.text)

        meaning_item = {"pos": item['partOfSpeech'], "meaning": meanings}
        definitions.append(meaning_item)
    return {"word": word, "definition": definitions}

def googledict(word, language, lemmatize=True):
    """Google dictionary lookup. Note Google dictionary cannot provide
    lemmatization, so only Russian is supported through PyMorphy2."""
    if language not in gdict_languages:
        return {"word": word, "definition": "Error: Unsupported language"}
    if language == "pt":
        # Patching this because it seems that Google dictionary only
        # offers the brasillian one.
        language = "pt-BR"

    try:
        res = requests.get('https://api.dictionaryapi.dev/api/v2/entries/' + language + "/" + word, timeout=4)
    except Exception as e:
        print(e)
    if res.status_code != 200:
        raise Exception("Lookup error")
    definitions = []
    data = res.json()[0]
    for item in data['meanings']:
        meanings = []
        for d in item['definitions']:
            meanings.append(d['definition'])
        meaning_item = {"pos": item.get('partOfSpeech', ""), "meaning": meanings}
        definitions.append(meaning_item)
    return {"word": word, "definition": definitions}

def googletranslate(word, language, gtrans_lang, gtrans_api):
    "Google translation, through the googletrans python library"
    url = f"{gtrans_api}/api/v1/{language}/{gtrans_lang}/{quote(word)}"
    res = requests.get(url)
    if res.status_code == 200:
        return {"word": word, "definition": res.json()['translation']}
    else:
        return

def getAudio(word, language, dictionary="Forvo (all)", custom_dicts=[]):
    # should return a dict of audio names and paths to audio
    if dictionary == "Forvo (all)":
        return fetch_audio_all(word, language)
    elif dictionary == "Forvo (best)":
        return fetch_audio_best(word, language)
    elif dictionary == "<all>":
        # We are using all the local dictionaries here.
        result = {}
        for d in custom_dicts:
            if d['lang'] == language and d['type'] == 'audiolib':
                try:
                    data = lookupin(word.lower(), language, lemmatize=False, dictionary=d['name'])
                    if data['definition']:
                        data['definition'] = json.loads(data['definition'])
                        rootpath = d['path']
                        for item in data['definition']:
                            qualified_name = d['name'] + ":" + os.path.splitext(item)[0]
                            result[qualified_name] = os.path.join(rootpath, item)
                except Exception:
                    pass
        return result
    else:
        # We are using a local dictionary here.
        data = lookupin(word.lower(), language, lemmatize=False, dictionary=dictionary)
        data['definition'] = json.loads(data['definition'])
        for d in custom_dicts:
            if d['name'] == dictionary and d['lang'] == language and d['type'] == 'audiolib':
                rootpath = d['path']
                break
        result = {}
        for item in data['definition']:
            qualified_name = dictionary + ":" + os.path.splitext(item)[0]
            result[qualified_name] = os.path.join(rootpath, item)
        return result
    return

def lookupin(word, language, lemmatize=True, dictionary="Wiktionary (English)", gtrans_lang="en", gtrans_api="https://lingva.ml"):
    # Remove any punctuation other than a hyphen
    # @language is code
    if language == 'ru':
        word = removeAccents(word)
    if lemmatize:
        word = lem_word(word, language)
    dictid = dictionaries.get(dictionary)
    if dictid == "wikt-en":
        item = wiktionary(word, language, lemmatize)
        item['definition'] = fmt_result(item['definition'])
    elif dictid == "gdict":
        item = googledict(word, language, lemmatize)
        item['definition'] = fmt_result(item['definition'])
    elif dictid == "gtrans":
        return googletranslate(word, language, gtrans_lang, gtrans_api)
    else:
        return {"word": word, "definition": dictdb.define(word, language, dictionary)}
    return item

def getFreq(word, language, lemfreq, dictionary):
    if lemfreq:
        word = lem_word(word, language)
    return int(dictdb.define(word.lower(), language, dictionary))


def getDictsForLang(lang: str, dicts: list):
    "Get the list of dictionaries for a given language"
    results = ["Wiktionary (English)", "Google Translate"] # These are for all the languages
    #if lang in gdict_languages:
    #    results.append("Google dictionary (Monolingual)")
    results.extend([item['name'] for item in dicts if item['lang'] == lang and item['type'] != "freq" and item['type'] != 'audiolib'])
    return results

def getAudioDictsForLang(lang: str, dicts: list):
    "Get the list of audio dictionaries for a given language"
    results = ["<disabled>"]
    results.extend(pronunciation_sources)
    audiolibs = [item['name'] for item in dicts if item['lang'] == lang and item['type'] == "audiolib"]
    results.extend(audiolibs)
    if len(audiolibs) > 1:
        results.append("<all>")
    return results

def getFreqlistsForLang(lang: str, dicts: list):
    return [item['name'] for item in dicts if item['lang'] == lang and item['type'] == "freq"]

forvopath = os.path.join(QStandardPaths.writableLocation(QStandardPaths.DataLocation), "forvo")
def play_audio(name: str, data: dict, lang: str):
    audiopath = data.get(name)
    if audiopath == None:
        return
    if audiopath.startswith("https://"):
        fpath = os.path.join(forvopath, lang, name) + audiopath[-4:]
        if not os.path.exists(fpath):
            res = requests.get(audiopath, headers=HEADERS)
            if res.status_code == 200:
                os.makedirs(os.path.dirname(fpath), exist_ok=True)
                with open(fpath, 'bw') as file:
                    file.write(res.content)
            else:
                return
        playsound(fpath)
        return fpath
    else:
        playsound(audiopath)
        return audiopath