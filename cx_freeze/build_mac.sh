#!/usr/bin/env bash
rm -rf build
python3 setup.py --quiet bdist_mac --iconfile icon.icns --bundle-name=ssmtool --custom-info-plist Info.plist
cd build
create-dmg "ssmtool.app"
