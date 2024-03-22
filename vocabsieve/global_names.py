from io import StringIO
from .constants import DEBUG_ENV
from PyQt5.QtCore import QStandardPaths, QSettings, QCoreApplication
from PyQt5.QtWidgets import QApplication
import qdarktheme
import os
import threading
from datetime import datetime
from loguru import logger
import platform
import sys

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


if platform.system() == "Darwin":
    MOD = "Cmd"
else:
    MOD = "Ctrl"

app_organization = "FreeLanguageTools"


def _get_settings_app_title():
    return title_prefix + DEBUG_ENV if DEBUG_ENV else title_prefix


app_name = _get_settings_app_title()

# qdarktheme.enable_hi_dpi function must be called before QCoreApplication is created
qdarktheme.enable_hi_dpi()
QCoreApplication.setApplicationName(app_name)
QCoreApplication.setOrganizationName(app_organization)
app = QApplication(sys.argv)
settings = QSettings(app_organization, app_name)
datapath = QStandardPaths.writableLocation(QStandardPaths.DataLocation)
forvopath = os.path.join(datapath, "forvo")
_imagepath = os.path.join(datapath, "images")
os.makedirs(_imagepath, exist_ok=True)

_today_log_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
os.makedirs(os.path.join(datapath, "log"), exist_ok=True)
_log_path = os.path.join(datapath, "log", f"session-{_today_log_name}.txt")

logger.add(_log_path, level="DEBUG")

session_logs = StringIO()
logger.add(session_logs, level="DEBUG")
