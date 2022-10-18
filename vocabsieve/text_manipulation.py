from .dictionary import lem_word
import re
from typing import Callable, Iterable
from .settings import settings
import string
import re
from itertools import chain

re_bolded = r"__([ \w]+)__"
apply_bold = lambda word: f"__{word}__"

def remove_bold(text):
    return re.sub(re_bolded, lambda match: match.group(1), text)

def filter_empty_string(ss):
    return filter(lambda s: s != "", ss)

split_on = string.punctuation + string.whitespace
def split(s: str) -> Iterable[str]:
    return chain.from_iterable(
        map(lambda m: filter_empty_string(m.groups()), 
            re.finditer(f'([^{split_on}]+)([{split_on}]*)', s)))

def unsplit(xs: Iterable[str]):
    return "".join(xs)

def bold_word_in_text(
    word, 
    text, 
    language,
    use_lemmatize=True, 
    greedy_lemmatize=False):
    if not use_lemmatize:
        return re.sub(word, lambda match: apply_bold(match.group()), text)
    else:
        lemmed_word = lem_word(word, language, greedy_lemmatize)
        res = list(split(text))

        return unsplit(list(map(
            lambda w: apply_bold(w) if lem_word(w, language, greedy_lemmatize) == lemmed_word else w, 
            split(text)
        )))
