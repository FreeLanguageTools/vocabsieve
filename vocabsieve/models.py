from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum
from bs4 import BeautifulSoup
import time
import re
from markdownify import markdownify
from .format import markdown_nop

from .lemmatizer import lem_word


@dataclass(frozen=True, slots=True)
class Definition:
    '''Represents a result returned by a dictionary'''
    headword: str
    lookup_term: str
    source: str
    definition: Optional[str] = None
    error: Optional[str] = None


@dataclass(frozen=True, slots=True)
class AudioDefinition:
    '''Represents a result returned by an audio dictionary'''
    headword: str
    lookup_term: str
    source: str
    audios: Optional[dict[str, str]] = None
    error: Optional[str] = None


@dataclass(frozen=True, slots=True)
class LookupResult:
    '''Represents the definition returned by a dictionary'''
    definition: Optional[str] = None
    error: Optional[str] = None


@dataclass(frozen=True, slots=True)
class AudioLookupResult:
    '''Represents the definition returned by an audio dictionary'''
    audios: Optional[dict[str, str]] = None
    error: Optional[str] = None


@dataclass(frozen=True, slots=True)
class LookupRecord:
    '''Represents a lookup record in the database'''
    word: str
    language: str
    source: str


@dataclass(frozen=True, slots=True)
class SRSNote:
    '''Represents an Anki note or other flashcard program, only word is required'''
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


@dataclass(slots=True)
class KnownMetadata:
    '''Represents metadata about calculated known data'''
    n_lookups: int = 0
    n_seen: int = 0
    n_mature_tgt: int = 0
    n_mature_ctx: int = 0
    n_young_tgt: int = 0
    n_young_ctx: int = 0


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


class LookupTrigger(Enum):
    '''Represents the trigger for a lookup'''
    double_clicked = 0
    shortcut_normal = 1
    shortcut_exact = 2
    hovered = 3


class FreqDisplayMode(str, Enum):
    '''Represents how to display the frequency of a word'''
    stars = "Stars"
    rank = "Rank"


@dataclass(frozen=True, slots=True)
class SourceOptions:
    '''Represents options for a Source'''
    lemma_policy: LemmaPolicy
    display_mode: DisplayMode
    skip_top: int
    collapse_newlines: int


class TrackingDataError(Enum):
    '''Represents an error that occurred during tracking'''
    no_errors = 0
    anki_enabled_but_not_running = 1
    anki_enabled_running_but_no_fieldmap = 2


class KeyAction(Enum):
    '''Represents the specific action of a key'''
    pressed = 0
    released = 1


@dataclass(slots=True)
class WordRecord:
    """Represents a user's knowledge of a word in the database
    Can be used to calculate score
    """
    lemma: str
    language: str
    n_seen: int = 0
    n_lookups: int = 0
    anki_young_ctx: int = 0
    anki_young_tgt: int = 0
    anki_mature_ctx: int = 0
    anki_mature_tgt: int = 0


@dataclass(frozen=True)
class WordActionWeights:
    """Represents the weights for each action in the score calculations"""
    seen: int
    lookup: int
    anki_young_ctx: int
    anki_young_tgt: int
    anki_mature_ctx: int
    anki_mature_tgt: int
    threshold: int
    threshold_cognate: int


class Source:
    '''Represents an abstract interface to a source of information in a language'''
    INTERNET = True

    def __init__(self, name: str, langcode: str) -> None:
        self.name = name
        self.langcode = langcode

    def define(self, word: str) -> Any:
        '''Get definitions for a word'''
        raise NotImplementedError


class FreqSource(Source):
    '''Represents an interface to a frequency list'''

    def __init__(self, name: str, langcode: str, lemmatized: bool) -> None:
        super().__init__(name, langcode)
        self.lemmatized = lemmatized

    def define(self, word: str) -> int:
        '''Get the frequency of a word'''
        if self.lemmatized:
            return self._lookup(lem_word(word, self.langcode))
        return self._lookup(word)

    def _lookup(self, word: str) -> int:
        raise NotImplementedError


class AudioSource(Source):
    def __init__(self, name: str, langcode: str, lemma_policy: LemmaPolicy) -> None:
        super().__init__(name, langcode)
        self.lemma_policy = lemma_policy

    def define(self, word: str, no_lemma=False) -> list[AudioDefinition]:
        "Get definitions according to LemmaPolicy"
        items = []
        lemma = lem_word(word, self.langcode)
        if no_lemma:
            return [self._fmt_lookup(word, word)]

        if self.lemma_policy == LemmaPolicy.no_lemma:
            items.append(self._fmt_lookup(word, word))

        elif self.lemma_policy == LemmaPolicy.only_lemma:
            items.append(self._fmt_lookup(lemma, word))

        elif self.lemma_policy == LemmaPolicy.try_original:
            items.append(self._fmt_lookup(word, word))
            if items[0].error is not None:
                items.append(self._fmt_lookup(lemma, word))

        elif self.lemma_policy == LemmaPolicy.try_lemma:
            items.append(self._fmt_lookup(lemma, word))
            if items[0].error is not None:
                items.append(self._fmt_lookup(word, word))

        elif self.lemma_policy == LemmaPolicy.first_lemma:
            items.append(self._fmt_lookup(lemma, word))
            if word != lemma:
                items.append(self._fmt_lookup(word, word))

        elif self.lemma_policy == LemmaPolicy.first_original:
            items.append(self._fmt_lookup(word, word))
            if word != lemma:
                items.append(self._fmt_lookup(lemma, word))

        return items

    def _fmt_lookup(self, word: str, lookup_term: str) -> AudioDefinition:
        '''Format a LookupResult as a Definition'''
        result = self._lookup(word)
        newdict = {}
        if result.audios is not None:
            for key in result.audios:
                newdict[self.name + "::" + key] = result.audios[key]
            return AudioDefinition(headword=word, source=self.name, audios=newdict, lookup_term=lookup_term)

        return AudioDefinition(headword=word, source=self.name, error=result.error, lookup_term=lookup_term)

    def _lookup(self, word: str) -> AudioLookupResult:
        raise NotImplementedError


class AudioSourceGroup:
    '''Wrapper for a group of Sources associated with a textbox on the main window'''

    def __init__(self, sources: list[AudioSource]) -> None:
        self.sources = sources

    def getSource(self, name: str) -> Optional[AudioSource]:
        '''Get a Source by name'''
        for source in self.sources:
            if source.name == name:
                return source
        return None

    def define(self, word: str, no_lemma: bool = False) -> list[AudioDefinition]:
        '''Get definitions from all sources'''
        definitions = []
        for source in self.sources:
            definitions.extend(source.define(word, no_lemma))
        return definitions


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
        result = defi
        result = convert_display_mode(result, self.display_mode)
        result = skip_lines(result, self.skip_top)
        result = collapse_newlines(result, self.collapse_newlines)
        return result

    def define(self, word: str, no_lemma=False) -> list[Definition]:
        "Get definitions according to LemmaPolicy"
        items = []
        lemma = lem_word(word, self.langcode)
        if no_lemma:
            return [self._fmt_lookup(word, word)]

        if self.lemma_policy == LemmaPolicy.no_lemma:
            items.append(self._fmt_lookup(word, word))

        elif self.lemma_policy == LemmaPolicy.only_lemma:
            items.append(self._fmt_lookup(lemma, word))

        elif self.lemma_policy == LemmaPolicy.try_original:
            items.append(self._fmt_lookup(word, word))
            if items[0].error is not None:
                items.append(self._fmt_lookup(lemma, word))

        elif self.lemma_policy == LemmaPolicy.try_lemma:
            items.append(self._fmt_lookup(lemma, word))
            if items[0].error is not None:
                items.append(self._fmt_lookup(word, word))

        elif self.lemma_policy == LemmaPolicy.first_lemma:
            items.append(self._fmt_lookup(lemma, word))
            if word != lemma:
                items.append(self._fmt_lookup(word, word))

        elif self.lemma_policy == LemmaPolicy.first_original:
            items.append(self._fmt_lookup(word, word))
            if word != lemma:
                items.append(self._fmt_lookup(lemma, word))

        return items

    def _fmt_lookup(self, word: str, lookup_term: str) -> Definition:
        '''Format a LookupResult as a Definition'''
        result = self._lookup(word)
        if result.definition is not None:
            return Definition(
                headword=word,
                source=self.name,
                definition=self.format(
                    result.definition),
                lookup_term=lookup_term)

        return Definition(headword=word, source=self.name, error=result.error, lookup_term=lookup_term)

    def _lookup(self, word: str) -> LookupResult:
        '''Lookup a word in the dictionary
        Subclass should override this method
        '''
        raise NotImplementedError


def convert_display_mode(entry: str, mode: DisplayMode) -> str:
    match mode:
        case DisplayMode.raw | DisplayMode.html:
            return entry
        case DisplayMode.markdown:
            return markdownify(entry)  # type: ignore
        case DisplayMode.markdown_html:
            return markdown_nop(markdownify(entry))
        case DisplayMode.plaintext:
            entry = entry.replace("<br>", "\n")\
                .replace("<br/>", "\n")\
                .replace("<BR>", "\n")
            entry = re.sub(r"<.*?>", "", entry)
            return entry
        case _:
            raise NotImplementedError(f"Mode {mode} not supported")


def is_html(s: str) -> bool:
    return bool(BeautifulSoup(s, "html.parser").find())


def skip_lines(entry: str, number: int) -> str:
    if is_html(entry):
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
