from dataclasses import dataclass
from typing import Optional
from enum import Enum
from .dictionary import lem_word

@dataclass(frozen=True, slots=True)
class Definition:
    '''Represents a definition returned by a dictionary'''
    headword: str
    source: str
    definition: Optional[str] = None
    error: Optional[str] = None

@dataclass(frozen=True, slots=True)
class Note:
    '''Represents an Anki note or other flashcard program'''
    sentence: str
    word: str
    definition1: str
    definition2: str
    pronunciation: str
    image: str
    tags: str

class LemmaPolicy(Enum):
    '''Represents how to handle lemmas'''
    no_lemma = 0
    only_lemma = 1
    try_original = 2
    try_lemma = 3
    first_lemma = 4
    first_original = 5

class Source:
    '''Represents a an interface to a dictionary'''
    def __init__(self, name: str, langcode: str, lemma_policy: LemmaPolicy) -> None:
        self.name = name
        self.langcode = langcode
        self.lemma_policy = lemma_policy
        

    def lookup(self, word: str, no_lemma=False) -> list[Definition]:
        "Get definitions according to LemmaPolicy"
        items = []
        if no_lemma:
            return [self._lookup(word)]
        
        if self.lemma_policy == LemmaPolicy.no_lemma:
            items.append(self._lookup(word))

        elif self.lemma_policy == LemmaPolicy.only_lemma:
            items.append(self._lookup(lem_word(word, self.langcode)))

        elif self.lemma_policy == LemmaPolicy.try_original:
            items.append(self._lookup(word))
            if items[0].error is not None:
                items.append(self._lookup(lem_word(word, self.langcode)))

        elif self.lemma_policy == LemmaPolicy.try_lemma:
            items.append(self._lookup(lem_word(word, self.langcode)))
            if items[0].error is not None:
                items.append(self._lookup(word))

        elif self.lemma_policy == LemmaPolicy.first_lemma:
            items.append(self._lookup(lem_word(word, self.langcode)))
            items.append(self._lookup(word))
        
        elif self.lemma_policy == LemmaPolicy.first_original:
            items.append(self._lookup(word))
            items.append(self._lookup(lem_word(word, self.langcode)))
        
        return items

    def _lookup(self, word: str) -> Definition:
        '''Lookup a word in the dictionary'''
        raise NotImplementedError

class SourceGroup:
    '''Wrapper for a group of Sources associated with a textbox on the main window'''
    def __init__(self, sources: list[Source]) -> None:
        self.sources = sources

    def getDefinitions(self, word: str) -> list[Definition]:
        '''Get definitions from all sources'''
        definitions = []
        for source in self.sources:
            definitions.extend(source.lookup(word))
        return definitions