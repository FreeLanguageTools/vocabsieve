import json
import re
import unicodedata
from threading import Thread
from urllib.parse import quote
from typing import Optional, Dict, Tuple
import time
import requests
import itertools
from bidict import bidict
from bs4 import BeautifulSoup
from markdown import markdown
from markdownify import markdownify
from .playsound import playsound
from .constants import DefinitionDisplayModes, LookUpResults
from .db import *
from .dictformats import removeprefix
from .forvo import *
from .lemmatizer import lem_word, removeAccents

dictdb = LocalDictionary()

gtrans_languages = ['af', 'sq', 'am', 'ar', 'hy', 'az', 'eu', 'be', 'bn',
                    'bs', 'bg', 'ca', 'ceb', 'ny', 'zh', 'zh_HANT', 'co', 'hr', 'cs',
                    'da', 'nl', 'en', 'eo', 'et', 'tl', 'fi', 'fr', 'fy', 'gl', 'ka',
                    'de', 'el', 'gu', 'he', 'ht', 'ha', 'haw', 'hi', 'hmn', 'hu', 'is', 'ig',
                    'id', 'ga', 'it', 'ja', 'kn', 'kk', 'km', 'rw', 'ko', 'ku', 'ky',
                    'lo', 'la', 'lv', 'lt', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'mi',
                    'mr', 'mn', 'my', 'ne', 'no', 'or', 'ps', 'fa', 'pl', 'pt', 'pa',
                    'ro', 'ru', 'sm', 'gd', 'sr', 'st', 'sn', 'sd', 'si', 'sk', 'sl',
                    'so', 'es', 'su', 'sw', 'sv', 'tg', 'ta', 'tt', 'te', 'th', 'tr',
                    'tk', 'uk', 'ur', 'ug', 'uz', 'vi', 'cy', 'xh', 'yi', 'yo', 'zu'
                    ]

langs_supported = bidict(
    dict(zip(gtrans_languages, [langcodes[item] for item in gtrans_languages])))

gdict_languages = [
    'en', 'hi', 'es', 'fr', 'ja', 'ru', 'de', 'it', 'ko', 'ar', 'tr', 'pt'
]

pronunciation_sources = ["Forvo (all)", "Forvo (best)"]



def preprocess_clipboard(s: str, lang: str, should_convert_to_uppercase: bool = False) -> str:
    """
    Pre-process string from clipboard before showing it
    NOTE: originally intended for parsing JA and ZH, but
    that feature has been removed for the time being due
    to maintainence and dependency concerns.
    """
    # Convert the first letter to uppercase if should_convert_to_uppercase is True
    if should_convert_to_uppercase:
        return s[0].upper() + s[1:]
    else:
        return s


def fmt_result(definitions):
    "Format the result of dictionary lookup"
    lines = []
    for defn in definitions:
        if defn['pos'] != "":
            lines.append("<i>" + defn['pos'] + "</i>")
        lines.extend([str(item[0] + 1) + ". " + item[1]
                     for item in list(enumerate(defn['meaning']))])
    return "<br>".join(lines)


def wiktionary(word, language: str) -> Optional[dict]:
    "Get definitions from Wiktionary"
    try:
        res = requests.get(
            'https://en.wiktionary.org/api/rest_v1/page/definition/' +
            word,
            timeout=4)
    except Exception as e:
        print(e)
        return None

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


def googletranslate(word, language, gtrans_lang, gtrans_api) -> Optional[LookUpResults]:
    "Google translation, through the googletrans python library"
    if language == "he":
        language = "iw" # fix for hebrew language code
    url = f"{gtrans_api}/api/v1/{language}/{gtrans_lang}/{quote(word)}"
    print(url)
    res = requests.get(url)
    if res.status_code == 200:
        return {"word": word, "definition": res.json()['translation']}
    return None

def getCognatesData(language: str, known_langs: list) -> Optional[List[str]]:
    "Get all cognates from the local database in a given language"
    start = time.time()
    data = dictdb.getCognates(language)
    if not known_langs:
        return []
    if not known_langs[0]:
        return []
    cognates = []
    for word, cognates_in in data:
        for lang in known_langs:
            if lang in cognates_in:
                cognates.append(word)
                break
    print("Got all cognates in", time.time() - start, "seconds")
    return cognates

def getAudio(word: str, 
             language: str, 
             dictionary: str="Forvo (all)", 
             custom_dicts:Optional[list]=None) -> Dict[str, str]:
    if custom_dicts is None:
        custom_dicts = []
    
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
                    data = lookupin(
                        word.lower(),
                        language,
                        lemmatize=False,
                        dictionary=d['name'])
                    if data['definition']:
                        data['definition'] = json.loads(data['definition'])
                        rootpath = d['path']
                        for item in data['definition']:
                            qualified_name = d['name'] + \
                                ":" + os.path.splitext(item)[0]
                            result[qualified_name] = os.path.join(
                                rootpath, item)
                except Exception:
                    pass
        return result

    # We are using a local dictionary here.
    data = lookupin(
        word.lower(),
        language,
        lemmatize=False,
        dictionary=dictionary)
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


def lookupin(
        word: str,
        language: str,
        lemmatize: bool=True,
        greedy_lemmatize: bool=False,
        dictionary: str="Wiktionary (English)",
        gtrans_lang: str="en",
        gtrans_api: str="https://lingva.lunar.icu") -> Optional[LookUpResults]:
    # Remove any punctuation other than a hyphen
    # @language is code
    if not word:
        return word
    IS_UPPER = word[0].isupper()
    if lemmatize and not " " in word:
        word = lem_word(word, language, greedy_lemmatize)
    # The lemmatizer would always turn words lowercase, which can cause
    # lookups to fail if not recovered.
    candidates = [word, word.capitalize()] if IS_UPPER else [word]
    if " " in word:
        words = word.split(" ")
        # Try all unlemmatized first, then brute force to test each lemmatized vs unlemmatized combos
        combinations = list(itertools.product(*[[word, lem_word(word, language, greedy_lemmatize)] for word in words]))
        for combo in combinations:
            if IS_UPPER:
                candidates.append(" ".join(combo))
                if IS_UPPER:
                    candidates.append(" ".join(combo).capitalize())
    candidates = set(candidates)
    for word in candidates:
        try:
            if dictionary == "Wiktionary (English)":
                item = wiktionary(word, language)
                item['definition'] = fmt_result(item['definition'])
                item['word'] = word
                return item
            elif dictionary == "Google Translate":
                return googletranslate(word, language, gtrans_lang, gtrans_api)
            else:
                try:
                    item = {
                        "word": word,
                        "definition": dictdb.define(
                            word,
                            language,
                            dictionary)}
                except Exception:
                    pass
                finally:
                    return item
        except BaseException:
            pass
    raise Exception("Word not found")


def getFreq(word, language, lemfreq, dictionary) -> Tuple[int, int]:
    if lemfreq:
        word = lem_word(word, language)
    freq = dictdb.define(word.lower(), language, dictionary)
    max_freq = dictdb.countEntriesDict(dictionary)
    return int(freq), int(max_freq)


def getDictsForLang(lang: str, dicts: list):
    "Get the list of dictionaries for a given language"
    # These are for all the languages
    results = ["Wiktionary (English)", "Google Translate"]
    results.extend([item['name'] for item in dicts if item['lang'] ==
                   lang and item['type'] != "freq" and item['type'] != 'audiolib'])
    return results


def getAudioDictsForLang(lang: str, dicts: list):
    "Get the list of audio dictionaries for a given language"
    results = ["<disabled>"]
    results.extend(pronunciation_sources)
    audiolibs = [item['name'] for item in dicts if item['lang']
                 == lang and item['type'] == "audiolib"]
    results.extend(audiolibs)
    if len(audiolibs) > 1:
        results.append("<all>")
    return results


def getFreqlistsForLang(lang: str, dicts: list):
    return [item['name']
            for item in dicts if item['lang'] == lang and item['type'] == "freq"]


forvopath = os.path.join(QStandardPaths.writableLocation(QStandardPaths.DataLocation), "forvo")


def play_audio(name: str, data: Dict[str, str], lang: str) -> str:
    def crossplatform_playsound(relative_audio_path: str):
        Thread(target=lambda: playsound(relative_audio_path)).start()

    audiopath: str = data.get(name, "")
    if not audiopath:
        return ""

    if not audiopath.startswith("https://"):
        crossplatform_playsound(audiopath)
        return audiopath

    fpath = os.path.join(forvopath, lang, name) + audiopath[-4:]
    if not os.path.exists(fpath):
        res = requests.get(audiopath, headers=HEADERS)

        if res.status_code != 200:
            # /TODO: Maybe display error to the user?
            return ""
        
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, 'bw') as file:
            file.write(res.content)
    
    crossplatform_playsound(fpath)
    return fpath


def process_definition(entry: str, mode: DefinitionDisplayModes, skip: int, newlines: int) -> str:
    result = entry
    result = convert_display_mode(result, mode)
    result = skip_lines(result, skip)
    result = collapse_newlines(result, newlines)
    return result


def convert_display_mode(entry: str, mode: DefinitionDisplayModes) -> str:
    if mode in ['Raw', 'HTML']:
        return entry
    elif mode == 'Markdown':
        return markdownify(entry)  # type: ignore
    elif mode == "Markdown-HTML":
        return markdown_nop(markdownify(entry))
    elif mode == 'Plaintext':
        entry = entry.replace("<br>", "\n")\
                     .replace("<br/>", "\n")\
                     .replace("<BR>", "\n")
        entry = re.sub(r"<.*?>", "", entry)
        return entry
    else:
        raise NotImplementedError("Mode not supported")


def is_html(s: str) -> bool:
    return bool(BeautifulSoup(s, "html.parser").find())


def skip_lines(entry: str, number: int) -> str:
    if is_html(entry):
        print("this is html")
        # Try to replace all the weird <br> tags with the standard one
        entry = entry.replace("<BR>", "<br>")\
                     .replace("<br/>", "<br>")\
                     .replace("<br />", "<br>")
        return "<br>".join(entry.split("<br>")[number:])
    else:
        return "\n".join(entry.splitlines()[number:])


def collapse_newlines(entry: str, number: int) -> str:
    if number == 0:  # no-op
        return entry
    if is_html(entry):
        # Try to replace all the weird <br> tags with the standard one
        entry = entry.replace("<BR>", "<br>")\
                     .replace("<br/>", "<br>")\
                     .replace("<br />", "<br>")
        return re.sub(r'(\<br\>)+', r'<br>' * number, entry)
    else:
        return re.sub(r'(\n)+', r'\n' * number, entry)


def markdown_nop(s: str) -> str:
    print(removeprefix(
        markdown(s.replace("\n", "\n\n").replace(".", "\.")).\
                   replace("<p>", "<br>").\
                   replace("</p>", ""),
        "<br>"))
    return removeprefix(
        markdown(s.replace("\n", "\n\n").replace(".", "\.")).\
                   replace("<p>", "<br>").\
                   replace("</p>", ""),
        "<br>"
    )
