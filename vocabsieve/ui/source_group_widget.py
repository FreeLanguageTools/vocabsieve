from PyQt5 import QtGui
from PyQt5.QtWidgets import QListWidget, QAbstractItemView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent


class SourceGroupWidget(QListWidget):
    """
    Represent a dictionary group configuration
    """

    def __init__(self) -> None:
        super().__init__()
        self.setToolTip("Drop dictionaries here from the right panel")
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.MoveAction)


class AllSourcesWidget(QListWidget):
    """
    This widget should act as a list of dictionary names that can be dragged from
    Dropping stuff on it should not add anything to the widget
    """

    def __init__(self) -> None:
        super().__init__()
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        event.accept()
