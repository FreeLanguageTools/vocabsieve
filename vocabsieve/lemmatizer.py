import simplemma
import pymorphy2
import re

# On Windows frozen build, there is no pymorphy2 support for Russian due
# to an issue with cxfreeze
PYMORPHY_SUPPORT = []
morph = {}
try:
    import pymorphy2_dicts_ru
    morph['ru'] = pymorphy2.MorphAnalyzer(path=pymorphy2_dicts_ru.get_path(), lang="ru")
    PYMORPHY_SUPPORT.append("ru")
    print("PyMorphy2 is available for RU")
except ValueError as e:
    print("PyMorphy2 is not available for RU, performance may be bad:", e)

try:
    import pymorphy2_dicts_uk
    morph['uk'] = pymorphy2.MorphAnalyzer(path=pymorphy2_dicts_uk.get_path(), lang="uk")
    print("PyMorphy2 is available for UK")
    PYMORPHY_SUPPORT.append("uk")
except ValueError as e:
    print("PyMorphy2 is not available for UK, performance may be bad:", e)

simplemma_languages = [
    'bg', 'ca', 'cy', 'da', 'de', 'en', 'es', 'et', 'fa', 'fi', 'fr', 'ga',
    'gd', 'gl', 'gv', 'hu', 'id', 'it', 'ka', 'la', 'lb', 'lt', 'lv', 'nl',
    'pl', 'pt', 'ro', 'ru', 'sk', 'sl', 'sv', 'tr', 'uk', 'ur'
]


def lem_word(word, language, greedy=False):
    """Lemmatize a word. We will use PyMorphy for RU, simplemma for others,
    and if that isn't supported , we give up. Should not fail under any circumstances"""
    try:
        if not word:
            return word
        word = re.sub('[\\?\\.!«»…,()\\[\\]]*', "", word)
        if language in PYMORPHY_SUPPORT:
            if morph and morph.get(language):
                return morph[language].parse(word)[0].normal_form
        elif language in simplemma_languages:
            return simplemma.lemmatize(word, lang=language, greedy=greedy)
        else:
            return word
    except ValueError:
        print("encountered ValueError")
        return word
    except Exception:
        return word
    