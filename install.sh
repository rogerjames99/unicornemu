#!/usr/bin/env bash

# Desktop file
cp unicornemu.desktop  /usr/share/applications
cp colourchooser.desktop /usr/share/applications

# Icons
cp unicornemu.png /usr/share/icons/hicolor/48x48/apps

# Scripts
cp unicornemu.py /usr/local/bin/unicornemu
cp colourchooser.py /usr/local/bin/colourchooser

#User interface files
mkdir /usr/share/unicornemu
cp unicornemu.ui /usr/share/unicornemu
cp colourchooser.ui /usr/share/unicornemu
