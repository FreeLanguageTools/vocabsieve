import ssmtool.main
from PyQt5 import QtCore

def test_config_button(qtbot):
    widget = ssmtool.main.DictionaryWindow()
    qtbot.addWidget(widget)

    # click in the Greet button and make sure it updates the appropriate label
    qtbot.mouseClick(widget.config_button, QtCore.Qt.LeftButton)

    assert widget.settings_dialog

def test_lookup(qtbot):
    widget = ssmtool.main.DictionaryWindow()
    qtbot.addWidget(widget)
    try:
        widget.lookup("hello")
        assert True
    except:
        assert False, "Lookup did not work"
    # click in the Greet button and make sure it updates the appropriate label