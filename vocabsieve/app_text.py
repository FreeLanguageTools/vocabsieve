from .constants import DEBUG_ENV
from . import __version__

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
settings_app_title = _get_settings_app_title()

