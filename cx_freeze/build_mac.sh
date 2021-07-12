#!/usr/bin/env bash
python3 setup.py bdist_mac --iconfile icon.icns --bundle-name=ssmtool --custom-info-plist Info.plist
cd build
create-dmg "ssmtool.app"
