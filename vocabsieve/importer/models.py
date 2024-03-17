from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReadingNote:
    """Represents a highlight/note/whatever in an ereader vocab builder"""
    lookup_term: str
    sentence: str
    date: str
    book_name: str
