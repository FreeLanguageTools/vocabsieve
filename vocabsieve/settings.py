from PyQt5.QtCore import *
from enum import Enum
from .app_text import settings_app_title, app_organization

settings = QSettings(app_organization, settings_app_title)

# Types

class BoldStyle(Enum):
    FONTWEIGHT = 1
    BOLDCHAR   = 2

# Defaults

defaults = {
    'bold_char': "_",
    'bold_style': BoldStyle.FONTWEIGHT.value
}

def set_defaults():
    for k, v in defaults.items():
        if not settings.value(k):
            settings.setValue(k, v)
set_defaults()
