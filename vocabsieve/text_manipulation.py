from .dictionary import lem_word
import re
from typing import Callable, Iterable
import string
import re
from itertools import chain, dropwhile
from .settings import settings

b = settings.value("bold_char")
apply_bold_tags = lambda word: f"<b>{word}</b>"
apply_bold_char = lambda word: f"{b}{b}{word}{b}{b}"
bolded_by_char_re = f"{b}{b}(.+?){b}{b}"
bolded_by_markdown_re = r"\*\*(.+?)\*\*"

def remove_bold_char_boldings(string: str):
    """ "__{word}__" => "{word}" """
    res = re.sub(
        bolded_by_char_re,
        lambda match: match.group(1),
        string
    )
    return res

def bold_char_boldings_to_bold_tag_boldings(string: str):
    """ "__{word}__" => "<b>{word}</b>" """
    return re.subn(
        bolded_by_char_re, 
        lambda match: apply_bold_tags(match.group(1)), 
        string)

def markdown_boldings_to_bold_tag_boldings(string: str):
    """ "**{word}**" => "<b>{word}</b>" """
    return re.sub(
        bolded_by_markdown_re, 
        lambda match: apply_bold_tags(match.group(1)), 
        string)

token_end = re.sub("'", "", string.punctuation + string.whitespace)
def tokenize(s: str) -> Iterable[str]:
    """ "Hello! I'm Jeff" => ["Hello", "! ", "I'm", " ", "Jeff"] """
    return chain.from_iterable(  # Flatten
        map(  # Find all tokens, obtaining shape [[until_split_on_chars, split_on_chars]]
            lambda m: [m.group(1), m.group(2)] if m.group(2) != "" else [m.group(1)], 
            re.finditer(f'([^{token_end}]+)([{token_end}]*)', s)))

def untokenize(xs: Iterable[str]):
    return "".join(xs)

def bold_word_in_text(
    word, 
    text, 
    apply_bold: Callable[[str], str],
    language,
    use_lemmatize=True, 
    greedy_lemmatize=False):
    if not use_lemmatize:
        return re.sub(word, lambda match: apply_bold(match.group(0)), text)
    else:
        lemmed_word = lem_word(word, language, greedy_lemmatize)

        return untokenize(map(
            lambda w: apply_bold(w) \
                      if lem_word(w, language, greedy_lemmatize) == lemmed_word \
                      else w, 
            tokenize(text)
        ))
