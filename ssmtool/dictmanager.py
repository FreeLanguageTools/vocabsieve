from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from .dictionary import *
from .tools import *
from bidict import bidict

supported_dict_formats = bidict({"stardict": "StarDict", "json": "Simple JSON", "migaku": "Migaku Dictionary"})

class DictManager(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.settings = parent.settings
        self.setWindowTitle("Manage Local Dictionaries")
        self.parent = parent
        self.resize(700, 500)
        self.initWidgets()
        self.setupWidgets()
        self.refresh()
        self.initTimer()
        #self.loadSettings()
        #self.setupAutosave()

    def initWidgets(self):
        self.tview = QTreeWidget()
        self.tview.setColumnCount(3)
        self.tview.setHeaderLabels(["Name", "Type", "Language"])
        self.add = QPushButton("Import..")
        self.add.clicked.connect(self.onAdd)
        self.remove = QPushButton("Remove")
        self.remove.clicked.connect(self.onRemove)
        self.rebuild = QPushButton("Rebuild dictionary database")
        self.rebuild.setToolTip("""\
This will regenerate the database containing dictionary entries.
This program store all dictionary entries into a single database in order to
improve performance during lookups. The files be in their original location
to be reimported, otherwise this operation will fail.\
        """)
        self.rebuild.clicked.connect(self.rebuildDB)
        self.bar = QStatusBar()

    def setupWidgets(self):
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tview)
        self.layout.addWidget(self.add)
        self.layout.addWidget(self.remove)
        self.layout.addWidget(self.rebuild)
        self.layout.addWidget(self.bar)

    def rebuildDB(self):
        self.status("Rebuilding database..")
        dictrebuild(self.settings.value("custom_dicts", [], type=list))
        self.status("Database rebuilt.")

    def onAdd(self):
        fdialog = QFileDialog()
        fdialog.setFileMode(QFileDialog.ExistingFile)
        fdialog.setAcceptMode(QFileDialog.AcceptOpen)
        fdialog.setNameFilter("Dictionary files (*.json *.ifo)")
        fdialog.exec()
        if fdialog.selectedFiles() == []:
            return
        else:
            fname = fdialog.selectedFiles()[0]
        dialog = AddDictDialog(self, fname)
        dialog.exec()

    def onRemove(self):
        index = self.tview.indexFromItem(self.tview.currentItem())
        dicts = self.settings.value("custom_dicts", type=list)
        if dicts == []:
            return
        del dicts[index.row()]
        self.settings.setValue("custom_dicts", dicts)
        self.refresh()
        self.rebuildDB()
    
    def refresh(self):
        dicts = self.settings.value("custom_dicts", [], type=list)
        self.tview.clear()
        for item in dicts:
            treeitem = QTreeWidgetItem([item['name'], supported_dict_formats[item['type']], code.inverse[item['lang']]])
            self.tview.addTopLevelItem(treeitem)
        for i in range(3):
            self.tview.resizeColumnToContents(i)

    def status(self, msg):
        self.bar.showMessage(self.time() + " " + msg, 4000)

    def time(self):
        return QDateTime.currentDateTime().toString('[hh:mm:ss]')
    def closeEvent(self, event):
        self.parent.loadDictionaries()
        self.parent.loadDict2Options()
        event.accept()

    def initTimer(self):
        self.showStats()
        self.timer = QTimer()
        self.timer.timeout.connect(self.showStats)
        self.timer.start(500)

    def showStats(self):
        n_dicts = dictdb.countDicts()
        n_entries = dictdb.countEntries()
        if self.bar.currentMessage() == "":
            self.status(f"Total: {n_dicts} dictionaries, {n_entries} entries.")


class AddDictDialog(QDialog):
    def __init__(self, parent, fname):
        super().__init__(parent)
        self.settings = parent.settings
        self.parent = parent
        self.setWindowTitle("Add Dictionary")
        self.resize(250, 150)
        self.fname = fname

        if dictinfo(self.fname) == "Unsupported format":
            self.warn("Unsupported format")
            self.close()
        self.parent.status("Reading " + self.fname)
        info = dictinfo(self.fname)
        self.parent.status("Reading done.")
        self.dicttype = info['type']
        self.path = info['path']
        self.basename = info['basename']
        self.initWidgets()
        self.setupWidgets()
        #self.loadSettings()
        #self.setupAutosave()

    def initWidgets(self):
        self.name = QLineEdit()
        self.name.setText(self.basename)
        self.type = QComboBox()
        self.type.addItems(supported_dict_formats.inverse.keys())
        self.type.setCurrentText(supported_dict_formats[self.dicttype])
        self.lang = QComboBox()
        self.lang.addItems(code.keys())
        self.commit_button = QPushButton("Add")
        self.commit_button.clicked.connect(self.commit)


    def setupWidgets(self):
        self.layout = QFormLayout(self)
        self.layout.addRow(QLabel("Name"), self.name)
        self.layout.addRow(QLabel("Type"), self.type)
        self.layout.addRow(QLabel("Language"), self.lang)
        self.layout.addRow(self.commit_button)


    def commit(self):
        dictimport(
            self.path, 
            supported_dict_formats.inverse[self.type.currentText()], 
            code[self.lang.currentText()], 
            self.name.text())
        dicts = self.settings.value("custom_dicts", [], type=list)
        dicts.append({"name": self.name.text(), 
                      "type": supported_dict_formats.inverse[self.type.currentText()], 
                      "path": self.path, 
                      "lang": code[self.lang.currentText()]})
        self.settings.setValue("custom_dicts", dicts)
        self.parent.status(f"Importing {self.name.text()} to database..")
        self.parent.refresh()
        self.parent.status("Importing done.")
        self.close()


    def warn(self, text):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(text)
        msg.exec()
