# Build Instructions

We are using `cx_Freeze` to build our distributable binaries.

`app.py` is a copy of `ssmtool.py` in the root directory, renamed to avoid naming conflicts.

Because of a bug in either cx_Freeze or `pymorphy2`, you **must manually patch** the `analyzer.py` module in `pymorphy2`. 

Please replace the module in your own pymorphy2 installation with the `analyzer.py` in the directory. (You can find this path by running `pip install pymorphy2`) This is not necessary when you run the script from source, nor is it necessary in Linux packages.

This patch uses an alternative way to get the path to data in the module `pymorphy2_dicts_ru` without `pkg_resources`, and assumes that the module is installed.

## Windows
First, install `cx_Freeze` from `pip`.
Then, install `ssmtool` package too.

Then, type `python setup.py bdist_msi` (creates installer)

OR

`python setup.py build_exe` (creates an executable in a folder)

There is currently no way to create a single file standalone executable with this script for Windows. You may want to find external tools to create that from the folder using the second option.

## macOS
First, install `cx_Freeze` from `pip`.
Then, install `ssmtool` package too.

You also need `create-dmg` tool from NPM to run this script, but you can use an alternative instead after the .app is generated.

Run `./build_mac.sh`

The .app and .dmg file will be in `build/`