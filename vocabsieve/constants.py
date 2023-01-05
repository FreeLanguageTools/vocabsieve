from __future__ import annotations  # for Python 3.7-3.9

import os

from typing_extensions import (  # for Python <3.11 with (Not)Required
    NotRequired, TypedDict)
from typing import Literal


DEBUG_ENV = os.environ.get("VOCABSIEVE_DEBUG")


class LookUpResults(TypedDict):
    word: str
    definition: str
    definition2: NotRequired[str]


DefinitionDisplayModes = Literal["Raw", "Plaintext", "Markdown", "HTML"]