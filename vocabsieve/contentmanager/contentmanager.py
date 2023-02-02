from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from bidict import bidict
from operator import itemgetter
from .dialog import AddContentDialog
from ..dictionary import langs_supported

class ContentManager(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.settings = parent.settings
        self.setWindowTitle("Manage content")
        self.parent = parent
        self.rec = parent.rec
        self.resize(500, 500)
        self.initWidgets()
        self.setupWidgets()

    def initWidgets(self):
        self.tview = QTreeWidget()
        self.tview.setColumnCount(3)
        self.tview.setHeaderLabels(["Name", "Date", "Word count"])
        self.add_file = QPushButton("Import single file (ebook, subtitle file)..")
        self.add_file.clicked.connect(self.onAddFile)
        #self.add_url = QPushButton("Import internet article (by URL)..")
        self.add_folder = QPushButton(
            "Import folder (combined in one entry, for series, etc)..")
        self.add_folder.clicked.connect(self.onAddFolder)
        self.remove = QPushButton("Remove selected")
        self.remove.clicked.connect(self.onRemove)
        self.rebuild = QPushButton("Rebuild seen words database")
        self.rebuild.clicked.connect(self.rebuildDB)
        self.bar = QStatusBar()
        self.refresh()

    def setupWidgets(self):
        self.layout = QVBoxLayout(self)
        label = QLabel("Vocabsieve supports tracking your progress by recording content you read. Add content here when you finish reading them")
        label.setWordWrap(True)
        self.layout.addWidget(label)
        self.layout.addWidget(self.tview)
        self.layout.addWidget(self.add_file)
        #self.layout.addWidget(self.add_url)
        self.layout.addWidget(self.add_folder)
        self.layout.addWidget(self.remove)
        self.layout.addWidget(self.rebuild)
        self.layout.addWidget(self.bar)

    def onAddFile(self):
        path, _ = QFileDialog.getOpenFileName(
                self, "Choose a file to import", 
                QStandardPaths.writableLocation(QStandardPaths.HomeLocation), 
                "Files (*.epub *.fb2 *.mobi *.html *.azw *.azw3 *.kfx *.srt *.vtt *.ass)"
                )
        if path:
            AddContentDialog(self, path).exec()
             
    def refresh(self):
        self.tview.clear()
        langcode = self.settings.value("target_language", 'en')
        items = list(self.rec.getContents(langcode))
        items = sorted(items, key=itemgetter(2), reverse=True)

        for name, content, jd in items:
            treeitem = QTreeWidgetItem([name, QDate.fromJulianDay(jd).toString("yyyy-MM-dd"), str(len(content.split()))])
            self.tview.addTopLevelItem(treeitem)
        for i in range(3):
            self.tview.resizeColumnToContents(i)
        impressions, uniques = self.rec.countSeen(langcode)
        self.status(f"Total: {uniques} lemmas seen {impressions} times")
    
    def status(self, msg, t=0):
        self.bar.showMessage(msg, t)

    def onAddFolder(self):
        path = QFileDialog.getExistingDirectory(
                self, "Choose a folder to import", 
                QStandardPaths.writableLocation(QStandardPaths.HomeLocation), 
                )
        if path:
            AddContentDialog(self, path).exec()

    def onRemove(self):
        item = self.tview.currentItem()
        if item:
            name = item.text(0)
            self.rec.deleteContent(name)
            self.refresh()

    def rebuildDB(self):
        self.rec.rebuildSeen()
        self.refresh()