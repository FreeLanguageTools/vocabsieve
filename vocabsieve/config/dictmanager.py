from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QDialog, QTreeWidget, QPushButton, QStatusBar, QVBoxLayout, QLabel, QFileDialog, QMessageBox, QTreeWidgetItem, QLineEdit, QComboBox, QFormLayout
from PyQt5.QtCore import QDateTime, QCoreApplication, QStandardPaths, QUrl
from PyQt5.QtGui import QDesktopServices
import time
from ..constants import langcodes
from ..dictionary import getDictsForLang, getFreqlistsForLang, getAudioDictsForLang
from ..dictformats import supported_dict_formats, dictinfo
import json
from ..tools import profile
from ..global_names import settings
from ..local_dictionary import dictdb
if TYPE_CHECKING:
    from .general_tab import GeneralTab


class DictManager(QDialog):
    def __init__(self, parent: "GeneralTab") -> None:
        super().__init__(parent)
        self.setWindowTitle("Manage Local Dictionaries")
        self.parent = parent  # type: ignore
        self.resize(500, 400)
        self.initWidgets()
        self.setupWidgets()
        self.refresh()
        self.showStats()

    def initWidgets(self):
        self.tview = QTreeWidget()
        self.tview.setColumnCount(4)
        self.tview.setHeaderLabels(["Name", "Type", "Language", "Headwords"])
        self.open_resources_manual_page = QPushButton("Open Resources page in browser")
        self.open_resources_manual_page.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://docs.freelanguagetools.org/resources.html")))
        self.add_dict = QPushButton("Import dictionary, frequency list, or cognate data...")
        self.add_dict.clicked.connect(self.onAdd)
        self.add_audio = QPushButton(
            "Import GoldenDict/LinguaLibre audio library...")
        self.add_audio.clicked.connect(self.onAddAudio)
        self.remove = QPushButton("Remove")
        self.remove.clicked.connect(self.onRemove)
        self.rebuild = QPushButton("Rebuild dictionary database")
        self.rebuild.setToolTip("""\
This will regenerate the database containing dictionary entries.
This program stores all dictionary entries in a single database to
improve performance during lookups. The files must be in their original location
to be reimported, otherwise this operation will fail.\
        """)
        self.rebuild.clicked.connect(self.rebuildDB)
        self.status_bar = QStatusBar()

    def setupWidgets(self):
        self._layout = QVBoxLayout(self)
        self._layout.addWidget(
            QLabel(
                "<strong>Note</strong>: "
                "<strong>Do not</strong> delete any files after importing them!<br>"
                "VocabSieve does not store a copy of these files; it only indexes and caches them.<br>"
                "If you delete the files, your dictionaries will disappear when the database is rebuilt."))
        self._layout.addWidget(self.open_resources_manual_page)
        self._layout.addWidget(self.tview)
        self._layout.addWidget(self.add_dict)
        self._layout.addWidget(self.add_audio)
        self._layout.addWidget(self.remove)
        self._layout.addWidget(self.rebuild)
        self._layout.addWidget(self.status_bar)

    def rebuildDB(self):
        start = time.time()
        dicts = json.loads(settings.value("custom_dicts", '[]'))
        dictdb.purge()
        n_dicts = len(dicts)
        failed_reads = []
        failed_errors = []
        for (i, item) in enumerate(dicts):
            try:
                self.status(f"Rebuilding database: dictionary ({i+1}/{n_dicts})"
                            ".. this can take a while.")
                QCoreApplication.processEvents()
                dictdb.dictimport(item['path'], item['type'], item['lang'], item['name'])
            except Exception as e:
                # Delete dictionary if read fails
                failed_reads.append(item['name'])
                failed_errors.append("\tError:" + repr(e))
                del dicts[i]
                settings.setValue("custom_dicts", json.dumps(dicts))
        dictdb.makeIndex()
        failures = [name + ": Error: " + error for name, error in zip(failed_reads, failed_errors)]
        failed_msg = ("\nThe following dictionaries could not be imported, and have been removed: \n"
                      + "\n\t".join(failures) if failures else "")

        QMessageBox.information(self, "Database rebuilt",
                                f"Database rebuilt in {format(time.time()-start, '.3f')} seconds.{failed_msg}")
        self.refresh()
        self.showStats()

    def onAdd(self):
        fdialog = QFileDialog()
        fdialog.setFileMode(QFileDialog.ExistingFile)
        fdialog.setNameFilter(
            "Dictionary files (*.jsonl *.jsonl.xz *.jsonl.gz *.jsonl.bz2 *.json *.json.xz *.json.bz2 *.json.gz *.ifo *.mdx *.dsl *.dsl.dz *.csv *.tsv)")
        fdialog.exec()
        if fdialog.selectedFiles() == []:
            return
        else:
            fname = fdialog.selectedFiles()[0]
        dialog = AddDictDialog(self, fname)
        dialog.exec()
        self.showStats()

    def onAddAudio(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select sound library", QStandardPaths.writableLocation(
                QStandardPaths.HomeLocation), QFileDialog.ShowDirsOnly)
        if not folder:
            return
        dialog = AddDictDialog(self, folder, True)
        dialog.exec()
        self.showStats()

    def onRemove(self):
        index = self.tview.indexFromItem(self.tview.currentItem())
        dicts = json.loads(settings.value("custom_dicts", '[]'))
        if dicts == []:
            return
        dictdb.dictdelete(dicts[index.row()]['name'])
        del dicts[index.row()]
        settings.setValue("custom_dicts", json.dumps(dicts))
        self.refresh()
        self.showStats()

    @profile
    def refresh(self):
        dicts = json.loads(settings.value("custom_dicts", '[]'))
        self.tview.clear()
        for item in dicts:
            treeitem = QTreeWidgetItem(
                [
                    item['name'],
                    supported_dict_formats[item['type']],
                    langcodes[item['lang']],
                    str(dictdb.countEntriesDict(item['name']))
                ]
            )
            self.tview.addTopLevelItem(treeitem)
        for i in range(4):
            self.tview.resizeColumnToContents(i)

    def status(self, msg, t=4000):
        self.status_bar.showMessage(self.time() + " " + msg, t)

    def time(self):
        return QDateTime.currentDateTime().toString('[hh:mm:ss]')

    def closeEvent(self, event):
        self.parent.load_dictionaries()
        self.parent.load_freq_sources()
        event.accept()

    def showStats(self):
        n_dicts = dictdb.countDicts()
        n_entries = dictdb.countEntries()
        self.status(f"Total: {n_dicts} dictionaries, {n_entries} entries.", t=0)
        # t=0 means it will not disappear


class AddDictDialog(QDialog):
    def __init__(self, parent, fname, audiolib=False):
        super().__init__(parent)
        self.parent = parent
        self.resize(250, 150)
        self.fname = fname
        self.audiolib = audiolib
        if audiolib:
            self.setWindowTitle("Add sound library")
        else:
            self.setWindowTitle("Add dictionary or frequency list")
            try:
                dictinfo(self.fname)
            except NotImplementedError:
                self.warn("Unsupported format")
                self.close()
            except IOError:
                self.warn("Failed to read file")
                self.close()

        self.parent.status("Reading " + self.fname)
        info = dictinfo(self.fname)
        self.parent.status("Reading done.")
        self.dicttype = info['type']
        self.path = info['path']
        self.basename = info['basename']
        self.initWidgets()
        self.setupWidgets()

    def initWidgets(self):
        self.name = QLineEdit()
        self.name.setText(self.basename)
        self.type = QComboBox()
        self.type.addItems(supported_dict_formats.inverse.keys())
        self.type.setCurrentText(supported_dict_formats[self.dicttype])
        self.lang = QComboBox()
        self.lang.addItems(langcodes.values())
        if self.dicttype == "cognates":
            self.lang.setCurrentText(langcodes["<all>"])
            self.lang.setEnabled(False)
            self.type.setEnabled(False)
            self.name.setText("cognates")
            self.name.setReadOnly(True)
        else:
            self.lang.setCurrentText(
                langcodes[settings.value("target_language", 'en')])
        self.commit_button = QPushButton("Add")
        self.commit_button.clicked.connect(self.commit)

    def setupWidgets(self):
        self._layout = QFormLayout(self)
        self._layout.addRow(QLabel("Name"), self.name)
        self._layout.addRow(QLabel("Type"), self.type)
        self._layout.addRow(QLabel("Language"), self.lang)
        self._layout.addRow(self.commit_button)

    def commit(self):
        "Give it a name, then add dictionary"
        name = self.name.text()
        dicts = json.loads(settings.value("custom_dicts", '[]'))
        lang = langcodes.inverse[self.lang.currentText()]
        existing_names = getDictsForLang(lang, dicts)\
            + getFreqlistsForLang(lang, dicts)\
            + getAudioDictsForLang(lang, dicts)\
            + ['wikt-en', 'gtrans', '####METAINFO']
        if name.lower() in [n.lower() for n in existing_names]:
            # Name conflict!!
            QMessageBox.critical(
                self,
                "Name conflict",
                f"A dictionary with name '{name}' already exists. "
                + "Please choose a different name",
            )
            return

        dictdb.dictimport(
            self.path,
            supported_dict_formats.inverse[self.type.currentText()],
            lang,
            self.name.text())
        dicts.append({"name": self.name.text(),
                      "type": supported_dict_formats.inverse[self.type.currentText()],
                      "path": self.path,
                      "lang": langcodes.inverse[self.lang.currentText()],
                      })
        settings.setValue("custom_dicts", json.dumps(dicts))
        self.parent.status(f"Importing {self.name.text()} to database..")
        self.parent.refresh()
        self.parent.status("Importing done.")
        self.parent.showStats()
        self.close()

    def warn(self, text):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(text)
        msg.exec()
