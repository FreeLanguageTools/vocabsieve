from .GenericImporter import GenericImporter
from .models import ReadingNote
from datetime import datetime as dt


class WordListImporter(GenericImporter):
    def __init__(self, parent, words: list[str]):
        self.words = words
        super().__init__(parent, "Word list", "", "wordlist", show_selector_date=False, show_selector_src=False)

    def getNotes(self):
        notes = []
        for word in self.words:
            notes.append(ReadingNote(
                lookup_term=word,
                sentence="",
                book_name="",
                date=str(dt.now().astimezone())[:19]
            ))
        return notes
