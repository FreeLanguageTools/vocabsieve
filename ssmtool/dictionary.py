import json
import urllib.request
import unicodedata
import simplemma
from googletrans import Translator
import requests
from bs4 import BeautifulSoup
from bidict import bidict
from .db import *
translator = Translator()
dictdb = LocalDictionary()
langdata = simplemma.load_data('en')

code = bidict({
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
    "Romanian": "ro",
    "Hindi": "hi",
    "Korean": "ko",
    "Arabic": "ar",
    "Turkish": "tr",
})

wikt_languages = code.keys()
gdict_languages = ['en', 'hi', 'es', 'fr', 'ja', 'ru', 'de', 'it', 'ko', 'ar', 'tr', 'pt']
simplemma_languages = ['bg', 'ca', 'cy', 'da', 'de', 'en', 'es', 'et', 'fa', 'fi', 'fr',
                       'ga', 'gd', 'gl', 'gv', 'hu', 'id', 'it', 'ka', 'la', 'lb', 'lt',
                       'lv', 'nl', 'pt', 'ro', 'ru', 'sk', 'sl', 'sv', 'tr', 'uk', 'ur']
dictionaries = {"Wiktionary (English)": "wikt-en",
                "Google dictionary (Monolingual)": "gdict",
                "Google translate": "gtrans"}


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
    #print("Remaining: ", word)
    return word

def fmt_result(definitions):
    "Format the result of dictionary lookup"
    lines = []
    for defn in definitions:
        if defn['pos'] != "":
            lines.append("<i>" + defn['pos'] + "</i>")
        lines.extend([str(item[0]+1) + ". " + item[1] for item in list(enumerate(definitions[0]['meaning']))])
    return "<br>".join(lines)

def lem_word(word, language):
    """Lemmatize a word. We will use simplemma, and if that
    isn't supported either, we give up."""
    if language in simplemma_languages:
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
            uninflected_forms_count = len(parsed_meaning.select("span.form-of-definition-link"))
            if uninflected_forms_count == 0 or not lemmatize:
                meaning = parsed_meaning.text
            else:
                next_target = parsed_meaning.select_one("span.form-of-definition-link")\
                    .select_one("a")['title']
                #print(next_target)
                return wiktionary(next_target, language, lemmatize=False)

            meanings.append(meaning)

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

def googletranslate(word, language, gtrans_lang):
    "Google translation, through the googletrans python library"
    return {"word": word, "definition": translator.translate(word, src=language, dest=gtrans_lang).text}


def lookupin(word, language, lemmatize=True, dictionary="Wiktionary (English)", gtrans_lang="English"):
    try:
        if lemmatize:
            word = lem_word(word, language)

        dictid = dictionaries.get(dictionary)
        if dictid == "wikt-en":
            item = wiktionary(word, language, lemmatize)
            item['definition'] = fmt_result(item['definition'])
            #print(item)
        elif dictid == "gdict":
            item = googledict(word, language, lemmatize)
            item['definition'] = fmt_result(item['definition'])
        elif dictid == "gtrans":
            return googletranslate(word, language, gtrans_lang)
        else:
            return {"word": word, "definition": dictdb.define(word, language, dictionary)}
        return item
    except Exception as e:
        print(e)
    #print(item)

def getDictsForLang(lang: str):
    "Get the list of dictionaries for a given language"
    results = ["Wiktionary (English)", "Google translate"]
    if lang in gdict_languages:
        results.append("Google dictionary (Monolingual)")
    results.extend(dictdb.getNamesForLang(lang))
    return results