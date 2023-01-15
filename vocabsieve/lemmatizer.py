import simplemma
import pymorphy2
import re

# On Windows frozen build, there is no pymorphy2 support for Russian due
# to an issue with cxfreeze
PYMORPHY_SUPPORT = False
try:
    morph = pymorphy2.MorphAnalyzer(lang="ru")
    PYMORPHY_SUPPORT = True
except ValueError:
    morph = None
    pass
simplemma_languages = [
    'bg', 'ca', 'cy', 'da', 'de', 'en', 'es', 'et', 'fa', 'fi', 'fr', 'ga',
    'gd', 'gl', 'gv', 'hu', 'id', 'it', 'ka', 'la', 'lb', 'lt', 'lv', 'nl',
    'pl', 'pt', 'ro', 'ru', 'sk', 'sl', 'sv', 'tr', 'uk', 'ur'
]

def lem_word(word, language, greedy=False):
    """Lemmatize a word. We will use PyMorphy for RU, simplemma for others,
    and if that isn't supported , we give up."""
    if not word:
        return word
    word = re.sub('[\\?\\.!«»…,()\\[\\]]*', "", word)
    if language == 'ru' and PYMORPHY_SUPPORT:
        return morph.parse(word)[0].normal_form
    elif language in simplemma_languages:
        return simplemma.lemmatize(word, lang=language, greedy=greedy)
    else:
        return word
