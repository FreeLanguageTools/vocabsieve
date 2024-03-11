import sys
from vocabsieve import __version__
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
include_files = [
    ('../../vocabsieve/reader/templates/',
     'lib/vocabsieve/reader/templates/'),
    ('../../vocabsieve/reader/static/',
     'lib/vocabsieve/reader/static/')]
build_exe_options = {
    "includes": [
        "vocabsieve",
        "setuptools",
        "bs4",
        "lxml",
        "simplemma",
        "pyqtgraph",
        "qdarktheme",
        "bidict",
        "pystardict",
        "flask",
        "pymorphy3",
        "pymorphy3_dicts_ru",
        "pymorphy3_dicts_uk",
        "jinja2.ext",
        "sqlite3",
        "charset_normalizer",
        "slpp",
        "ebooklib",
        "markdown",
        "markdownify",
        "lzo",
        "readmdict",
        "packaging",
        "pynput",
        "pynput.keyboard._win32",
        "pynput.mouse._win32",
        "gevent"
        ],
    "include_files": include_files,
    "zip_include_packages": ["PyQt5"],
    "excludes": ["tkinter"],
    "bin_includes": ["liblzo2.so"],
    "include_msvcr": True,
    "silent_level": 1
    }

bdist_msi_options = {
    "upgrade_code": "{F10E2AE2-7629-3CA2-AA85-498478E708D7}",
    "target_name": f"VocabSieve-v{__version__}-win64.msi"
    }

# base="Win32GUI" should be used only for Windows GUI app
base = None
if sys.platform == "win32":
    base = "Win32GUI"


setup(
    name="VocabSieve",
    version=__version__,
    description="A simple sentence mining tool",
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
    executables=[Executable("app.py",
                            base=base,
                            icon="../icon.ico",
                            shortcut_name="VocabSieve",
                            shortcut_dir="DesktopFolder")]
)
