from typing import Optional
from bidict import bidict

from .constants import langcodes


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


def getDictsForLang(lang: str, dicts: list):
    "Get the list of dictionaries for a given language"
    # These are for all the languages
    results = ["Wiktionary (English)", "Google Translate"]
    results.extend([item['name'] for item in dicts if item['lang'] ==
                   lang and item['type'] != "freq" and item['type'] != 'audiolib'])
    return results


def getAudioDictsForLang(lang: str, dicts: list):
    "Get the list of audio dictionaries for a given language"
    results = ["Forvo"]
    audiolibs = [item['name'] for item in dicts if item['lang']
                 == lang and item['type'] == "audiolib"]
    results.extend(audiolibs)
    return results


def getFreqlistsForLang(lang: str, dicts: list):
    return [item['name']
            for item in dicts if item['lang'] == lang and item['type'] == "freq"]
