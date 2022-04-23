import sys
from vocabsieve import __version__
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
include_files = [
    ('../vocabsieve/ext/reader/templates/',
     'lib/vocabsieve/ext/reader/templates/'),
    ('../vocabsieve/ext/reader/static/',
     'lib/vocabsieve/ext/reader/static/')]
build_exe_options = {
    "includes": [
        "vocabsieve",
        "setuptools",
        "PyQt5",
        "bs4",
        "lxml",
        "simplemma",
        "bidict",
        "pystardict",
        "flask",
        "pymorphy2",
        "playsound",
        "flask_sqlalchemy",
        "jinja2.ext",
        "sqlalchemy",
        "sqlite3",
        "sqlalchemy.sql.default_comparator",
        "sqlalchemy.dialects.sqlite",
        "charset_normalizer",
        "slpp",
        "ebooklib",
        "pycountry"],
    "include_files": include_files,
    "excludes": ["tkinter"],
    "include_msvcr": True}

# base="Win32GUI" should be used only for Windows GUI app
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="VocabSieve",
    version=__version__,
    description="A simple sentence mining tool",
    options={"build_exe": build_exe_options},
    executables=[Executable("app.py",
                            base=base,
                            icon="icon.ico",
                            shortcut_name="VocabSieve",
                            shortcut_dir="DesktopFolder")]
)
