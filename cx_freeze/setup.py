import sys
from ssmtool import __version__
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
include_files = [('../ssmtool/ext/reader/templates/', 'lib/ssmtool/ext/reader/templates/'),
                 ('../ssmtool/ext/reader/static/', 'lib/ssmtool/ext/reader/static/')]
build_exe_options = {"includes": ["ssmtool", "setuptools", "PyQt5",
                                  "bs4", "lxml", "simplemma", "googletrans",
                                  "bidict", "pystardict", "flask", "pymorphy2",
                                  "pymorphy2_dicts", "playsound", "flask_sqlalchemy", 
                                  "jinja2.ext", "sqlalchemy",
                                  "sqlite3", "sqlalchemy.sql.default_comparator",
                                  "sqlalchemy.dialects.sqlite", "charset-normalizer", "slpp"],
                     "include_files": include_files,
                     "excludes": ["tkinter"],
                     "include_msvcr": True}

# base="Win32GUI" should be used only for Windows GUI app
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name = "ssmtool",
    version = __version__,
    description = "Simple Sentence Mining",
    options = {"build_exe": build_exe_options},
    executables = [Executable("app.py",
                              base=base,
                              icon="icon.ico",
                              shortcut_name="Simple Sentence Mining",
                              shortcut_dir="DesktopFolder")]
)
