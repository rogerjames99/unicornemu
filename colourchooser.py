#!/usr/bin/env python

from gi.repository import Gtk
import os

class ColourChooser:
    def __init__(self):
        # Set up the gui                     
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(os.getcwd(), 'colourchooser.ui'))
        self.builder.connect_signals(self)
        self.window = self.builder.get_object('colourChooserApplicationWindow')
        self.chooser = self.builder.get_object('colourChooserWidget')
        self.window.show()
    
    def quit_cb(self, *args):
        Gtk.main_quit()
        
if __name__ == '__main__':
    ui = ColourChooser()
    Gtk.main()


# At the moment this is not showing the widget properpy until you move the slider or resize the window
# I have no idea why!
