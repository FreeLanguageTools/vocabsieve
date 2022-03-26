#!/usr/bin/env bash
rm -rf build
python3 setup.py --quiet bdist_mac --iconfile icon.icns --bundle-name=vocabsieve --custom-info-plist Info.plist
cd build
create-dmg "vocabsieve.app"
