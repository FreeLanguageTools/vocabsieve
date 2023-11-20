from dataclasses import dataclass
from typing import Optional
from enum import Enum
from bs4 import BeautifulSoup
import re
from markdownify import markdownify
from .format import markdown_nop

from .dictionary import lem_word

@dataclass(frozen=True, slots=True)
class Definition:
    '''Represents a result returned by a dictionary'''
    headword: str
    source: str
    definition: Optional[str] = None
    error: Optional[str] = None

@dataclass(frozen=True, slots=True)
class LookupResult:
    '''Represents the definition returned by a dictionary'''
    definition: Optional[str] = None
    error: Optional[str] = None

@dataclass(frozen=True, slots=True)
class SRSNote:
    '''Represents an Anki note or other flashcard program'''
    word: str
    sentence: Optional[str] = None
    definition1: Optional[str] = None
    definition2: Optional[str] = None
    audio_path: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[list[str]] = None

@dataclass(frozen=True, slots=True)
class AnkiSettings:
    '''Represents settings for Anki'''
    deck: str
    model: str
    word_field: str
    sentence_field: Optional[str] = None
    definition1_field: Optional[str] = None
    definition2_field: Optional[str] = None
    audio_field: Optional[str] = None
    image_field: Optional[str] = None
    tags: Optional[list[str]] = None



class LemmaPolicy(str, Enum):
    '''Represents how to handle lemmas'''
    no_lemma = "Don't lemmatize"
    only_lemma = "Only use lemma"
    try_original = "Try original first, otherwise lemma"
    try_lemma = "Try lemma first, otherwise original"
    first_lemma = "Lemma first, then original"
    first_original = "Original first, then lemma"

class DisplayMode(str, Enum):
    '''Represents how to display definitions'''
    raw = "Raw"
    plaintext = "Plaintext"
    markdown = "Markdown"
    markdown_html = "Markdown-HTML"
    html = "HTML"

@dataclass
class SourceOptions:
    '''Represents options for a Source'''
    lemma_policy: LemmaPolicy
    display_mode: DisplayMode
    skip_top: int
    collapse_newlines: int


class Source:
    '''Represents an abstract interface to a source of information in a language'''
    def __init__(self, name: str, langcode: str) -> None:
        self.name = name
        self.langcode = langcode

class FreqSource(Source):
    '''Represents an interface to a frequency list'''
    def __init__(self, name: str, langcode: str, lemmatized: bool) -> None:
        super().__init__(name, langcode)
        self.lemmatized = lemmatized
    
    def define(self, word: str) -> int:
        return self._lookup(word)
    
    def _lookup(self, word: str) -> int:
        raise NotImplementedError
    

class DictionarySource(Source):
    '''Represents a an interface to a dictionary'''
    def __init__(self, name: str, langcode: str, options: SourceOptions) -> None:
        super().__init__(name, langcode)
        self.lemma_policy = options.lemma_policy
        self.display_mode = options.display_mode
        self.skip_top = options.skip_top
        self.collapse_newlines = options.collapse_newlines

    def format(self, defi: str) -> str:
        '''Format a definition according to the SourceOptions'''
        print("Formatting", defi)
        result = defi
        result = convert_display_mode(result, self.display_mode)
        result = skip_lines(result, self.skip_top)
        result = collapse_newlines(result, self.collapse_newlines)
        print("Formatted", result)
        return result

        

    def define(self, word: str, no_lemma=False) -> list[Definition]:
        "Get definitions according to LemmaPolicy"
        items = []
        lemma = lem_word(word, self.langcode)
        if no_lemma:
            return [self._fmt_lookup(word)]
        
        if self.lemma_policy == LemmaPolicy.no_lemma:
            items.append(self._fmt_lookup(word))

        elif self.lemma_policy == LemmaPolicy.only_lemma:
            items.append(self._fmt_lookup(lemma))

        elif self.lemma_policy == LemmaPolicy.try_original:
            items.append(self._fmt_lookup(word))
            if items[0].error is not None:
                items.append(self._fmt_lookup(lemma))

        elif self.lemma_policy == LemmaPolicy.try_lemma:
            items.append(self._fmt_lookup(lemma))
            if items[0].error is not None:
                items.append(self._fmt_lookup(word))

        elif self.lemma_policy == LemmaPolicy.first_lemma:
            items.append(self._fmt_lookup(lemma))
            if word != lemma:
                items.append(self._fmt_lookup(word))
        
        elif self.lemma_policy == LemmaPolicy.first_original:
            items.append(self._fmt_lookup(word))
            if word != lemma:
                items.append(self._fmt_lookup(lemma))
        
        return items
    
    def _fmt_lookup(self, word: str) -> Definition:
        '''Format a LookupResult as a Definition'''
        result = self._lookup(word)
        if result.definition is not None:
            return Definition(headword=word, source=self.name, definition=self.format(result.definition))
        else:
            return Definition(headword=word, source=self.name, error=result.error)

    def _lookup(self, word: str) -> LookupResult:
        '''Lookup a word in the dictionary
        Subclass should override this method
        '''
        raise NotImplementedError

class DictionarySourceGroup:
    '''Wrapper for a group of Sources associated with a textbox on the main window'''
    def __init__(self, sources: list[DictionarySource]) -> None:
        self.sources = sources

    def getSource(self, name: str) -> Optional[DictionarySource]:
        '''Get a Source by name'''
        for source in self.sources:
            if source.name == name:
                return source
        return None

    def define(self, word: str) -> list[Definition]:
        '''Get definitions from all sources'''
        definitions = []
        for source in self.sources:
            definitions.extend(source.define(word))
        return definitions
    
def convert_display_mode(entry: str, mode: DisplayMode) -> str:
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
