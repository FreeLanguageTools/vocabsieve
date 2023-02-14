from __future__ import annotations  # for Python 3.7-3.9

import os

from typing_extensions import (  # for Python <3.11 with (Not)Required
    NotRequired, TypedDict)
from typing import Literal
from bidict import bidict
import re

DEBUG_ENV = os.environ.get("VOCABSIEVE_DEBUG")


class LookUpResults(TypedDict):
    word: str
    definition: str
    definition2: NotRequired[str]


DefinitionDisplayModes = Literal["Raw", "Plaintext", "Markdown", "HTML"]

langcodes = bidict({'aa': 'Afar', 'ab': 'Abkhazian', 'af': 'Afrikaans', 'ak': 'Akan', 'am': 'Amharic', 'ar': 'Arabic', 'an': 'Aragonese', 'as': 'Assamese', 'av': 'Avaric', 'ae': 'Avestan', 'ay': 'Aymara', 'az': 'Azerbaijani', 'ba': 'Bashkir', 'bm': 'Bambara', 'be': 'Belarusian', 'bn': 'Bengali', 'bi': 'Bislama', 'bo': 'Tibetan', 'bs': 'Bosnian', 'br': 'Breton', 'bg': 'Bulgarian', 'ca': 'Catalan', 'cs': 'Czech', 'ch': 'Chamorro', 'ce': 'Chechen', 'cu': 'Church Slavic', 'cv': 'Chuvash', 'kw': 'Cornish', 'co': 'Corsican', 'cr': 'Cree', 'cy': 'Welsh', 'da': 'Danish', 'de': 'German', 'dv': 'Dhivehi', 'dz': 'Dzongkha', 'el': 'Modern Greek (1453-)', 'en': 'English', 'eo': 'Esperanto', 'et': 'Estonian', 'eu': 'Basque', 'ee': 'Ewe', 'fo': 'Faroese', 'fa': 'Persian', 'fj': 'Fijian', 'fi': 'Finnish', 'fr': 'French', 'fy': 'Western Frisian', 'ff': 'Fulah', 'gd': 'Scottish Gaelic', 'ga': 'Irish', 'gl': 'Galician', 'gv': 'Manx', 'gn': 'Guarani', 'gu': 'Gujarati', 'ht': 'Haitian', 'ha': 'Hausa', 'sh': 'Serbo-Croatian', 'he': 'Hebrew', 'hz': 'Herero', 'hi': 'Hindi', 'ho': 'Hiri Motu', 'hr': 'Croatian', 'hu': 'Hungarian', 'hy': 'Armenian', 'ig': 'Igbo', 'io': 'Ido', 'ii': 'Sichuan Yi', 'iu': 'Inuktitut', 'ie': 'Interlingue', 'ia': 'Interlingua (International Auxiliary Language Association)', 'id': 'Indonesian', 'ik': 'Inupiaq', 'is': 'Icelandic', 'it': 'Italian', 'jv': 'Javanese', 'ja': 'Japanese', 'kl': 'Kalaallisut', 'kn': 'Kannada', 'ks': 'Kashmiri', 'ka': 'Georgian', 'kr': 'Kanuri', 'kk': 'Kazakh', 'km': 'Central Khmer', 'ki': 'Kikuyu', 'rw': 'Kinyarwanda', 'ky': 'Kirghiz', 'kv': 'Komi', 'kg': 'Kongo', 'ko': 'Korean', 'kj': 'Kuanyama', 'ku': 'Kurdish', 'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian', 'li': 'Limburgan', 'ln': 'Lingala', 'lt': 'Lithuanian', 'lb': 'Luxembourgish', 'lu': 'Luba-Katanga', 'lg': 'Ganda', 'mh': 'Marshallese', 'ml': 'Malayalam', 'mr': 'Marathi', 'mk': 'Macedonian', 'mg': 'Malagasy', 'mt': 'Maltese', 'mn': 'Mongolian', 'mi': 'Maori', 'ms': 'Malay (macrolanguage)', 'my': 'Burmese', 'na': 'Nauru', 'nv': 'Navajo', 'nr': 'South Ndebele', 'nd': 'North Ndebele', 'ng': 'Ndonga', 'ne': 'Nepali (macrolanguage)', 'nl': 'Dutch', 'nn': 'Norwegian Nynorsk', 'nb': 'Norwegian Bokmål', 'no': 'Norwegian', 'ny': 'Nyanja', 'oc': 'Occitan (post 1500)', 'oj': 'Ojibwa', 'or': 'Oriya (macrolanguage)', 'om': 'Oromo', 'os': 'Ossetian', 'pa': 'Panjabi', 'pi': 'Pali', 'pl': 'Polish', 'pt': 'Portuguese', 'ps': 'Pushto', 'qu': 'Quechua', 'rm': 'Romansh', 'ro': 'Romanian', 'rn': 'Rundi', 'ru': 'Russian', 'sg': 'Sango', 'sa': 'Sanskrit', 'si': 'Sinhala', 'sk': 'Slovak', 'sl': 'Slovenian', 'se': 'Northern Sami', 'sm': 'Samoan', 'sn': 'Shona', 'sd': 'Sindhi', 'so': 'Somali', 'st': 'Southern Sotho', 'es': 'Spanish', 'sq': 'Albanian', 'sc': 'Sardinian', 'sr': 'Serbian', 'ss': 'Swati', 'su': 'Sundanese', 'sw': 'Swahili (macrolanguage)', 'sv': 'Swedish', 'ty': 'Tahitian', 'ta': 'Tamil', 'tt': 'Tatar', 'te': 'Telugu', 'tg': 'Tajik', 'tl': 'Tagalog', 'th': 'Thai', 'ti': 'Tigrinya', 'to': 'Tonga (Tonga Islands)', 'tn': 'Tswana', 'ts': 'Tsonga', 'tk': 'Turkmen', 'tr': 'Turkish', 'tw': 'Twi', 'ug': 'Uighur', 'uk': 'Ukrainian', 'ur': 'Urdu', 'uz': 'Uzbek', 've': 'Venda', 'vi': 'Vietnamese', 'vo': 'Volapük', 'wa': 'Walloon', 'wo': 'Wolof', 'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba', 'za': 'Zhuang', 'zh': 'Chinese', 'zu': 'Zulu'})
# Apply patches
langcodes['el'] = "Greek"
for item in langcodes:
    langcodes[item] = re.sub(r'\s?\([^)]*\)$', '', langcodes[item]) # Removes words in parens
langcodes['zh_HANT'] = "Chinese (Traditional)"
langcodes['haw'] = "Hawaiian"
langcodes['ceb'] = "Cebuano"
langcodes['hmn'] = "Hmong"
langcodes['<all>'] = "<all languages>"