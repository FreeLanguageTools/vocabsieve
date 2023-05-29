import simplemma
import pymorphy3
import re
from functools import lru_cache
import unicodedata

PYMORPHY_SUPPORT = []
morph = {}
try:
    import pymorphy3_dicts_ru
    morph['ru'] = pymorphy3.MorphAnalyzer(path=pymorphy3_dicts_ru.get_path(), lang="ru")
    PYMORPHY_SUPPORT.append("ru")
    print("pymorphy3 is available for RU")
except Exception as e:
    print("pymorphy3 is not available for RU, performance may be bad:", e)

try:
    import pymorphy3_dicts_uk
    morph['uk'] = pymorphy3.MorphAnalyzer(path=pymorphy3_dicts_uk.get_path(), lang="uk")
    print("pymorphy3 is available for UK")
    PYMORPHY_SUPPORT.append("uk")
except Exception as e:
    print("pymorphy3 is not available for UK, performance may be bad:", e)

simplemma_languages = ["ast", "bg", "ca", "cs", "cy", "da", "de", "el", "en",
                       "enm", "es", "et", "fa", "fi", "fr", "ga", "gd", "gl",
                       "gv", "hbs", "hi", "hu", "hy", "id", "is", "it", "ka",
                       "la", "lb", "lt", "lv", "mk", "ms", "nb", "nl", "nn",
                       "pl", "pt", "ro", "ru", "se", "sk", "sl", "sq", "sv",
                       "sw", "tl", "tr", "uk"]


def lem_pre(word, language):
    word = re.sub(r'[\?\.!«»”“"…,()\[\]]*', "", word).strip()
    word = re.sub(r"<.*?>", "", word)
    word = re.sub(r"\{.*?\}", "", word)
    return word

def lem_word(word, language, greedy=False):
    return lemmatize(lem_pre(word, language), language, greedy)


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

@lru_cache(maxsize=500000)
def lemmatize(word, language, greedy=False):
    """Lemmatize a word. We will use PyMorphy for RU, UK, simplemma for others,
    and if that isn't supported , we give up. Should not fail under any circumstances"""
    try:
        if language == 'ru':
            word = removeAccents(word)
        if not word:
            return word
        if language in PYMORPHY_SUPPORT:
            if morph and morph.get(language):
                return morph[language].parse(word)[0].normal_form
        elif language in simplemma_languages:
            return simplemma.lemmatize(word, lang=language, greedy=greedy)
        else:
            return word
    except ValueError as e:
        print("encountered ValueError", repr(e))
        return word
    except Exception as e:
        print(repr(e))
        return word
    
