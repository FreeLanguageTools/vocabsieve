from typing import Optional, Dict, Tuple
import time
from bidict import bidict

from .db import *
from .forvo import *


dictdb = LocalDictionary(datapath)

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
    if should_convert_to_uppercase and s:
        return s[0].upper() + s[1:]
    else:
        return s






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
    else:
        pass


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

