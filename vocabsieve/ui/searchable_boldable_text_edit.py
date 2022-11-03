from PyQt5.QtGui import *
from .searchable_text_edit import SearchableTextEdit
from ..text_manipulation import *
from ..settings import *

class SearchableBoldableTextEdit(SearchableTextEdit):
    def __init__(self):
        super(SearchableBoldableTextEdit, self).__init__()
        self.currentCharFormatChanged.connect(self.handleCurrentCharFormatChanged)

    @property
    def textBoldedByTags(self):
        """
        Current text content with bolded words defined by <b/>, irrespective of 
        `settings.value("bold_style")`.
        """
        if settings.value("bold_style", type=int) == BoldStyle.FONTWEIGHT.value:
            return markdown_boldings_to_bold_tag_boldings(
                # toMarkdown() includes erroneous newlines
                self.toMarkdown()[:-2])
        elif settings.value("bold_style", type=int) == BoldStyle.BOLDCHAR.value:
            return bold_char_boldings_to_bold_tag_boldings(self.toPlainText())[0]
        else: return self.toPlainText()

    def keyPressEvent(self, e):
        super().keyPressEvent(e)

        # Every time the user writes "_", check if we need to perform the 
        # substitution "__{word}__" -> "<b>{word}</b>"
        if settings.value("bold_style", type=int) == BoldStyle.FONTWEIGHT.value \
            and e.text() == settings.value("bold_char"):
            self.performBoldSubstitutions()

    def performBoldSubstitutions(self):
        bold_tags_substituted, subs_performed = \
            bold_char_boldings_to_bold_tag_boldings(self.toPlainText())

        if subs_performed:
            def rebold_previously_bolded_words(string: str):
                for should_bold in set(re.findall(r"\*\*(.+?)\*\*", self.toMarkdown())):
                    string = re.sub(
                        re.escape(should_bold), 
                        lambda match: apply_bold_tags(match.group(0)), 
                        string)
                return string

            bold_tags_substituted = rebold_previously_bolded_words(
                bold_tags_substituted)

            # Save cursor position
            old_cursor_pos = self.textCursor().position()
            # Set text
            self.setText(bold_tags_substituted)

            # Move back by the 4 characters removed when substituting 
            # "__{word}__" => "<b>{word}</b>" (note that `cursor` does not 
            # consider "<b/>" when calling `cursor.setPosition()`
            cursor = self.textCursor()
            cursor.setPosition(old_cursor_pos - 4 * subs_performed)
            self.setTextCursor(cursor)

    @pyqtSlot()
    def handleCurrentCharFormatChanged(self):
        """ 
        If `settings.value("bold_style") == BoldStyle.FONTWEIGHT.value`, bolded characters are
        added to the text editor. By default, the user cannot type in non-bold
        font adjacent to these characters, so we reset the font weight to 
        non-bold every time it changes.
        """

        def ensureNormalFontWeight():
            cursor = self.textCursor()
            fmt = cursor.charFormat()
            if fmt.fontWeight() != QFont.Weight.Normal:
                fmt.setFontWeight(QFont.Weight.Normal)
                cursor.setCharFormat(fmt)
                self.setTextCursor(cursor)
        ensureNormalFontWeight()

    @property
    def unboldedText(self):
        if settings.value("bold_style", type=int) == BoldStyle.FONTWEIGHT.value:
            # `.toPlainText()` strips <b/> for us
            return self.toPlainText()
        elif settings.value("bold_style", type=int) == BoldStyle.BOLDCHAR.value:
            # Remove bolds using bold_char
            return remove_bold_char_boldings(self.toPlainText())
        elif settings.value("bold_style", type=int) == "<disabled>":
            # Text was never bolded in the first place
            return self.toPlainText()