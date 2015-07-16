#!/usr/bin/env bash

# Desktop file
cp unicornemu.desktop  /usr/share/applications
cp colourchooser.desktop /usr/share/applications

# Icons
cp unicornemu.png /usr/share/icons/hicolor/48x48/apps
cp colourchooser.png /usr/share/icons/hicolor/48x48/apps
gtk-update-icon-cache -f /usr/share/icons/hicolor

# Scripts
cp unicornemu.py /usr/local/bin/unicornemu
chmod a+x /usr/local/bin/unicornemu
cp colourchooser.py /usr/local/bin/colourchooser
chmod a+x /usr/local/bin/colourchooser

#User interface files
mkdir /usr/share/unicornemu
cp unicornemu.ui /usr/share/unicornemu
cp colourchooser.ui /usr/share/unicornemu

# Avahi service def
cp scratch-remote-sensor.service /etc/avahi/services

# Scratch projects
cp unicorn.sb "/home/team/Documents/Scratch Projects"
