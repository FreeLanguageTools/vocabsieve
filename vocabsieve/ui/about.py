from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QT_VERSION_STR, PYQT_VERSION_STR
import sys
from .. import __version__



class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("About VocabSieve")

        QBtn = QDialogButtonBox.Ok

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        self._layout = QVBoxLayout() # type: ignore
        message = QLabel(
            f'''
VocabSieve version: {__version__}<br>
Python version: {sys.version}<br>
PyQt5 (Qt bindings) version: {QT_VERSION_STR}, Qt {PYQT_VERSION_STR}<br><br>
© 2022 FreeLanguageTools<br><br>
Visit <a href="https://wiki.freelanguagetools.org">FreeLanguageTools Wiki</a> for more info on how to use this tool.<br>
You can also talk to us on <a href="https://webchat.kde.org/#/room/#flt:midov.pl">Matrix</a>
or <a href="https://t.me/fltchat">Telegram</a> for support.<br><br>

Consult <a href="https://wiki.freelanguagetools.org/vocabsieve_dicts">this wiki page</a>
to find compatible dictionaries. <br><br>

VocabSieve (formerly SSM, ssmtool) is free software available to you under the terms of
<a href="https://www.gnu.org/licenses/gpl-3.0.en.html">GNU GPLv3</a>.
If you found a bug, or have enhancement ideas, please open an issue on the
Github <a href=https://github.com/FreeLanguageTools/vocabsieve>repository</a>.<br><br>

This program is yours to keep. There is no EULA you need to agree to.
No usage data is sent to any server other than the configured dictionary APIs.
Statistics data are stored locally.
<br><br>
If you find this tool useful, you can give it a star on Github and tell others about it. Any suggestions will also be appreciated.
            '''
        )
        message.setTextFormat(Qt.RichText)
        message.setOpenExternalLinks(True)
        message.setWordWrap(True)
        message.adjustSize()
        self._layout.addWidget(message)
        self._layout.addWidget(self.buttonBox)
        self.setLayout(self._layout)