from .constants import DEBUG_ENV
from PyQt5.QtCore import QStandardPaths, QSettings, QCoreApplication
import os
import threading
from . import __version__
lock = threading.Lock()
def _get_debug_description():
    return "(debug=" + DEBUG_ENV + ")"

title_prefix = "VocabSieve" 
def app_title(include_version: bool):
    title = title_prefix
    
    if include_version:
        title += f" v{__version__}"
    if DEBUG_ENV: 
        title += _get_debug_description()

    return title

app_organization = "FreeLanguageTools"
def _get_settings_app_title():
    return title_prefix + DEBUG_ENV if DEBUG_ENV else title_prefix
app_name = _get_settings_app_title()

QCoreApplication.setApplicationName(app_name)
QCoreApplication.setOrganizationName(app_organization)

settings = QSettings(app_organization, app_name)
datapath = QStandardPaths.writableLocation(QStandardPaths.DataLocation)
forvopath = os.path.join(datapath, "forvo")
