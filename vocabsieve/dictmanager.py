from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from .dictionary import *
from .tools import *
from .dictformats import supported_dict_formats, dictinfo
from bidict import bidict
import json
import os


class DictManager(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.settings = parent.settings
        self.setWindowTitle("Manage Local Dictionaries")
        self.parent = parent
        self.resize(500, 400)
        self.initWidgets()
        self.setupWidgets()
        self.refresh()
        self.showStats()
        # self.loadSettings()
        # self.setupAutosave()

    def initWidgets(self):
        self.tview = QTreeWidget()
        self.tview.setColumnCount(4)
        self.tview.setHeaderLabels(["Name", "Type", "Language", "Headwords"])
        self.add_dict = QPushButton("Import dictionary or frequency list..")
        self.add_dict.clicked.connect(self.onAdd)
        self.add_audio = QPushButton(
            "Import GoldenDict/LinguaLibre audio library..")
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
        self.bar = QStatusBar()

    def setupWidgets(self):
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(
            QLabel(
                "<strong>Note</strong>: "
                "<strong>Do not</strong> delete any files after importing them!<br>"
                "VocabSieve does not store a copy of these files; it only indexes and caches them.<br>"
                "If you delete the files, your dictionaries will disappear when the database is rebuilt."))
        self.layout.addWidget(self.tview)
        self.layout.addWidget(self.add_dict)
        self.layout.addWidget(self.add_audio)
        self.layout.addWidget(self.remove)
        self.layout.addWidget(self.rebuild)
        self.layout.addWidget(self.bar)

    def rebuildDB(self):
        start = time.time()
        dicts = json.loads(self.settings.value("custom_dicts", '[]'))
        dictdb.purge()
        n_dicts = len(dicts)
        for (i, item) in enumerate(dicts):
            try:
                self.status(f"Rebuilding database: dictionary ({i+1}/{n_dicts})"
                            ".. this can take a while.")
                QCoreApplication.processEvents()
                dictimport(item['path'], item['type'], item['lang'], item['name'])
            except Exception as e:
                print(e)

        QMessageBox.information(self, "Database rebuilt",
                                f"Database rebuilt in {format(time.time()-start, '.3f')} seconds.")
        self.refresh()
        self.showStats()

    def onAdd(self):
        fdialog = QFileDialog()
        fdialog.setFileMode(QFileDialog.ExistingFile)
        fdialog.setNameFilter("Dictionary files (*.json *.ifo *.mdx *.dsl *.dsl.dz *.csv *.tsv)")
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
        dicts = json.loads(self.settings.value("custom_dicts", '[]'))
        if dicts == []:
            return
        dictdelete(dicts[index.row()]['name'])
        del dicts[index.row()]
        self.settings.setValue("custom_dicts", json.dumps(dicts))
        self.refresh()
        self.showStats()

    def refresh(self):
        dicts = json.loads(self.settings.value("custom_dicts", '[]'))
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
        self.bar.showMessage(self.time() + " " + msg, t)

    def time(self):
        return QDateTime.currentDateTime().toString('[hh:mm:ss]')

    def closeEvent(self, event):
        self.parent.loadDictionaries()
        self.parent.loadFreqSources()
        self.parent.loadAudioDictionaries()
        event.accept()

    def showStats(self):
        n_dicts = dictdb.countDicts()
        n_entries = dictdb.countEntries()
        self.status(f"Total: {n_dicts} dictionaries, {n_entries} entries.", t=0)
        # t=0 means it will not disappear


class AddDictDialog(QDialog):
    def __init__(self, parent, fname, audiolib=False):
        super().__init__(parent)
        self.settings = parent.settings
        self.parent = parent
        self.resize(250, 150)
        self.fname = fname
        self.audiolib = audiolib
        if audiolib:
            self.setWindowTitle("Add dictionary or frequency list")
        else:
            self.setWindowTitle("Add sound library")
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
        self.lang.addItems(langs_supported.values())
        self.lang.setCurrentText(
            langcodes[self.settings.value("target_language")])
        self.commit_button = QPushButton("Add")
        self.commit_button.clicked.connect(self.commit)

    def setupWidgets(self):
        self.layout = QFormLayout(self)
        self.layout.addRow(QLabel("Name"), self.name)
        self.layout.addRow(QLabel("Type"), self.type)
        self.layout.addRow(QLabel("Language"), self.lang)
        self.layout.addRow(self.commit_button)

    def commit(self):
        "Give it a name, then add dictionary"
        name = self.name.text()
        dicts = json.loads(self.settings.value("custom_dicts", '[]'))
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

        dictimport(
            self.path,
            supported_dict_formats.inverse[self.type.currentText()],
            lang,
            self.name.text())
        dicts.append({"name": self.name.text(),
                      "type": supported_dict_formats.inverse[self.type.currentText()],
                      "path": self.path,
                      "lang": langcodes.inverse[self.lang.currentText()],
                      })
        self.settings.setValue("custom_dicts", json.dumps(dicts))
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
