# Build Instructions

We are using `cx_Freeze` to build our distributable binaries.

`app.py` is a copy of `vocabsieve.py` in the root directory, renamed to avoid naming conflicts.

## Windows
First, install `cx_Freeze` from `pip`.
Then, install `vocabsieve` package too.

Then, type `python setup.py bdist_msi` (creates installer)

OR

`python setup.py build_exe` (creates an executable in a folder)

There is currently no way to create a single file standalone executable with this script for Windows. You may want to find external tools to create that from the folder using the second option.

## macOS
First, install `cx_Freeze` from `pip`.
Then, install `vocabsieve` package too.

You also need `create-dmg` tool from NPM to run this script, but you can use an alternative instead after the .app is generated.

Run `./build_mac.sh`

The .app and .dmg file will be in `build/`
