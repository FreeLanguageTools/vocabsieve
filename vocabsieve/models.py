from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Definition:
    '''Represents a definition returned by a dictionary'''
    headword: str
    definition: str
    source: str

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



class Source:
    '''Represents a an interface to a dictionary'''
    def lookup(self, word: str) -> Definition:
        '''Returns a definition for a given word'''
        raise NotImplementedError()

