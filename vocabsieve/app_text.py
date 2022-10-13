from .constants import DEBUGGING, DEBUG_ENV
from . import __version__

def _getDebugDescription():
    return "(debug=" + str(DEBUG_ENV) + ")"
debug_description = _getDebugDescription()

def app_title(include_version: bool):
    title = "VocabSieve" 
    if include_version:
        title += f" v{__version__}"
    if DEBUGGING: 
        title += " " + debug_description

    return title
app_organization = "FreeLanguageTools"