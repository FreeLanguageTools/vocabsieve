import sys
import os
import platform
from vocabsieve import __version__
from cx_Freeze import setup, Executable  # pylint: disable=import-error

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
include_files = [
    ('../vocabsieve/reader/templates/',
     'lib/vocabsieve/reader/templates/'),
    ('../vocabsieve/reader/static/',
     'lib/vocabsieve/reader/static/')]

PYNPUT_PLATFORM_SPECIFIC_MODULES = {
    "win32": ["pynput.keyboard._win32", "pynput.mouse._win32"],
    "darwin": ["pynput.keyboard._darwin", "pynput.mouse._darwin"]
}

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
        "requests",
        "markdownify",
        "lzo",
        "readmdict",
        "packaging",
        "pynput",
        "gevent"
    ] + PYNPUT_PLATFORM_SPECIFIC_MODULES.get(sys.platform, []),
    "include_files": include_files,
    "zip_include_packages": ["PyQt5"],
    "excludes": ["tkinter"],
    "bin_includes": ["liblzo2.so"],
    "include_msvcr": True,
    "silent_level": 1
}

# base="Win32GUI" should be used only for Windows GUI app
base = None
WINDOWS_OUTPUT_NAME = f"VocabSieve-v{__version__}-DEBUG-win64.msi"
SCRIPT = "app.py"
if sys.platform == "win32" and not os.environ.get("VOCABSIEVE_DEBUG_BUILD"):
    # If we are on a non-debug build on Windows, we want to use the GUI base to hide the console window
    base = "Win32GUI"
    WINDOWS_OUTPUT_NAME = f"VocabSieve-v{__version__}-win64.msi"
    SCRIPT = "app_win32.py"

bdist_msi_options = {
    "upgrade_code": "{F10E2AE2-7629-3CA2-AA85-498478E708D7}",
    "target_name": WINDOWS_OUTPUT_NAME
}

# x86_64 or arm64
PLATFORM_MACHINE_NAME = platform.machine()

bdist_mac_options = {
    'iconfile': "icon.icns",
    'bundle_name': f"VocabSieve-v{__version__}-macos-" + PLATFORM_MACHINE_NAME,
    'custom_info_plist': 'Info.plist',
}

bdist_dmg_options = {
    'volume_label': f"VocabSieve-v{__version__}-macos",
    'applications_shortcut': True,

}


setup(
    name="VocabSieve",
    version=__version__,
    description="Anki companion for language learning",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
        "bdist_mac": bdist_mac_options,
        "bdist_dmg": bdist_dmg_options
    },
    executables=[Executable(SCRIPT,
                            base=base,
                            icon="icon.ico",
                            shortcut_name="VocabSieve",
                            shortcut_dir="DesktopFolder")]
)
