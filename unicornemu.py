#!/usr/bin/env python

import logging
import argparse
import os
from gi.repository import Gtk, GLib, Gio, GObject, DBus
import cairo
import numpy as np
import random
import threading
import socket
import time
import struct

AvahiSupport = False


logFormat = '%(thread)x %(funcName)s %(lineno)d %(levelname)s:%(message)s'

def logmatrix(logger, matrix):
    xx, yx, xy, yy, x0, y0 = matrix
    logger('Matrix xx=%f yx=%f xy=%f yy=%f x0=%f y0=%f', xx, yx, xy, yy, x0, y0)

class UnicornEmu(Gtk.Application):
    class Window(object):
        def __init__(self, application, *args):
            # Constants
            self.imageSize = 1000

            
            # Set up the gui                     
            self.builder = Gtk.Builder()
            try:
                self.builder.add_from_file(os.path.join('/usr/share/unicornemu', 'unicornemu.ui'))
            except FileError:
                self.builder.add_from_file(os.path.join(os.getcwd(), 'unicornemu.ui'))
                
            self.builder.connect_signals(self)
            self.mainWindow = self.builder.get_object('unicornemuApplicationWindow')
            self.mainWindow.set_application(application)
            self.mainWindow.show()
            
            # Use cairo to do the matrix stuff
            self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.imageSize, self.imageSize)
                    
            self.scratch = SocketThread(application.hostname, 42001, self.surface, self.builder.get_object('drawingArea'))
            
            if AvahiSupport:
                self.avahi = AvahiThread()
            
        def close(self, *args):
            self.mainWindow.destroy()
            
        def drawit(self, widget, cr):
            logging.debug('Draw callback')
            x ,y, width, height = cr.clip_extents()
            xscale = float(width) / float(self.surface.get_width())
            yscale = float(height) / float(self.surface.get_height())
            cr.scale(xscale, yscale)
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.set_source_surface(self.surface)
            cr.paint()
            return False
                            
        def quit_cb(self, *args):
            logging.debug('Shutting down')
            self.scratch.terminate()
            logging.shutdown()
            self.close()

    # Gnome application initialization routine
    def __init__(self, application_id, flags):
        
        # Process command line options
        parser = argparse.ArgumentParser(description='Scratchgpio compatible emulator for Unicorn Hat')
        parser.add_argument('hostname', default='localhost', nargs='?',
                   help='The hostname of the scratch desktop')
        parser.add_argument('-v', '--verbose', nargs='?', const=True, default=False,
                   help='Send debug logging to stderr')
        parser.add_argument('-a', '--avahi', nargs='?', const=True, default=False,
                   help='Enable avahi support')

        args = parser.parse_args()
        self.hostname = args.hostname                
        Gtk.Application.__init__(self, application_id=application_id, flags=flags)
        self.connect("activate", self.new_window)

        # Initialise logging
        logging.basicConfig(filename='unicornemu.log', level=logging.DEBUG, filemode='w', \
                             format=logFormat)
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        if args.verbose:
            formatter = logging.Formatter(logFormat)
            console.setFormatter(formatter)
            logging.getLogger('').addHandler(console)
                             
        logging.debug('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        
    def new_window(self, *args):
        self.Window(self, self.hostname)
        
class AvahiThread(threading.Thread):
    def __init__(self):
        # Intialise the thread
        threading.Thread.__init__(self)                
        self.start()

    def service_resolved(*args):
        print 'service resolved'
        print 'name:', args[2]
        print 'address:', args[7]
        print 'port:', args[8]

    def print_error(*args):
        print 'error_handler'
        print args[0]
    
    def myhandler(interface, protocol, name, stype, domain, flags):
        print "Found service '%s' type '%s' domain '%s' " % (name, stype, domain)

        server.ResolveService(interface, protocol, name, stype, 
            domain, avahi.PROTO_UNSPEC, dbus.UInt32(0), 
            reply_handler=service_resolved, error_handler=print_error)
            
    def run(self):
        loop = DBusGMainLoop()

        bus = dbus.SystemBus(mainloop=loop)

        server = dbus.Interface( bus.get_object(avahi.DBUS_NAME, '/'),
                'org.freedesktop.Avahi.Server')

        sbrowser = dbus.Interface(bus.get_object(avahi.DBUS_NAME,
                server.ServiceBrowserNew(avahi.IF_UNSPEC,
                    avahi.PROTO_UNSPEC, TYPE, 'local', dbus.UInt32(0))),
                avahi.DBUS_INTERFACE_SERVICE_BROWSER)

        sbrowser.connect_to_signal("ItemNew", myhandler)

        gobject.MainLoop().run()
        

class SocketThread(threading.Thread):
    def __init__(self, host, port, surface, drawingArea):
        self.host = host
        self.port = port
        self.surface = surface
        self.context = cairo.Context(self.surface)
        self.drawingArea = drawingArea
        self.hatSize = 8
        self.tcolours = {'r': (1, 0, 0), 'red': (1, 0, 0), 'g': (0, 1, 0), 'green': (0, 1, 0), 'b': (0, 0, 1), 'blue': (0, 0, 1),
                    'c': (0, 1, 1), 'cyan': (0, 1, 1), 'm': (1, 0, 1), 'magenta': (1, 0, 1), 'y': (1, 1, 0), 'yellow': (1, 1, 0),
                    'w': (1, 1, 1), 'white': (1, 1, 1), '0': (0, 0, 0), 'off': (0, 0, 0), '1': (1, 1, 1), 'on': (1, 1, 1),
                    'z': (0, 0, 0), 'invert': (0, 0, 0), 'random' : (0,0,0)}
        self.lastColour = (0,0,0)

        
       
        logging.debug('Surface matrix')
        self.context.scale(float(self.surface.get_width()) / self.hatSize, -float(self.surface.get_height()) / self.hatSize)
        self.context.translate(-1, -(self.hatSize + 1))
        logmatrix(logging.debug, self.context.get_matrix())
        
        for x in range(1,self.hatSize + 1):
            for y in range(1,self.hatSize + 1):
                self.context.set_source_rgba(random.random(), random.random(), random.random())
                self.context.rectangle(x, y, 1, 1)
                self.context.fill()
        
        GLib.idle_add(self.update)
        
        # Intialise the thread
        threading.Thread.__init__(self)                
        self.stop_event = threading.Event()
        self.start()
        
    def update(self):
        logging.debug('Dirtying the drawing area')
        self.drawingArea.queue_draw()

        
    def run(self):
        while not self.stop_event.isSet():
            try:
                logging.debug('Trying')
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                logging.debug('Connected')
            except socket.error:
                logging.debug('There was an error connecting to Scratch!')
                logging.debug("I couldn't find a Mesh session at host: %s, port: %d", self.host, self.port)
                time.sleep(3)
                continue
                
            self.socket.settimeout(0.1)
                
            while not self.stop_event.isSet():
                try:
                    data = self.socket.recv(4)
                    if len(data) < 4:
                        logging.debug('RSP message < 4 bytes received - the reomte end has probably gone away')
                        self.socket.close()
                        break
                    temp = data[0:4] # Just in case the string hasn't shrunk. Do I need this?
                    message_length = struct.unpack('>L', temp)[0]
                    logging.debug('Scratch RSP data length %d', message_length)
                    data = self.socket.recv(message_length)
                    logging.debug('Scratch RSP received data: %s', data)
                except socket.timeout:
                    continue                    
                except socket.error:
                    logging.debug('Error receiving RSP message from Scratch')
                    self.socket.close()
                    break
                    
                words = data.split(' ',1)
                
                if words[0].lower() != 'broadcast':
                    logging.debug('Discarding message; not a broadcast')
                    continue
                    
                broadcast_message = words[1][1:-1]
                broadcast_message = broadcast_message.lower()
                commands = broadcast_message.split(' ')
                
                for command in commands:
                    if command.startswith('matrixuse'):
                        self.matrixuse()
                    elif command == 'allon':
                        self.allon()
                    elif command == 'alloff':
                        self.alloff()
                    elif command == 'sweep':
                        self.sweep()
                    elif command.startswith('red'):
                        self.setComponent('red', command[3:])
                        logging.debug('red')
                    elif command.startswith('green'):
                        logging.debug('green')
                    elif command.startswith('blue'):
                        logging.debug('blue')
                    elif command.startswith('colour'):
                        self.colour(command[6:])
                    elif command.startswith('pixel'):
                        self.pixel(command[5:])
                    elif command.startswith('bright'):
                        logging.debug('bright')
                    elif command.startswith('matrixpattern'):
                        logging.debug('matrixpattern')
                    elif command.startswith('move'):
                        self.move(command[4:])
                    elif command == 'invert':
                        logging.debug('invert')
                    elif command.startswith('level'):
                        logging.debug('level')
                    elif command.startswith('row'):
                        self.row(command[3:])
                    elif command.startswith('col'):
                        self.col(command[3:])
                    elif command.startswith('loadimage'):
                        logging.debug('loadimage')
                    elif command.startswith('saveimage'):
                        logging.debug('saveimage')
                    elif command.startswith('load2image'):
                        logging.debug('load2image')
               
        self.socket.close()
        
    def colour(self, command):
        logging.debug('colour')
        paintColour = self.processColour(command)

        if(paintColour[0] >= 0.):
            self.lastColour = paintColour
        
    def setComponent(self, component, parameters):
        logging.debug('setComponent component: %s parameters %s', component, parameters)
        if component == 'red':
            index = 0
        elif component == 'green':
            index = 1
        elif component == 'blue':
            index = 2
        else:
            logging.debug('setComponent invalid component')
            return
        
        colour -1    
        try:
            colour = int(parameters)
        except ValueError:
            pass
            
        if colour >= 0 and colour < 256:
            self.lastColour[index] = float(colour) / 255.
            return
        elif parameters == 'on':
            self.lastColour[index] = 1
        elif parameters == 'off':
            self.lastColour[index] = 0
        else:
            logging.debug('setComponent invalid colour')

    def matrixuse(slef):
        logging.debug('matrixuse')
        
    def alloff(self):
        logging.debug('alloff')
        self.context.set_source_rgb(0, 0, 0)
        self.context.paint()
        GLib.idle_add(self.update)
        
    def allon(self):
        logging.debug('allon')
        self.context.set_source_rgb(1, 1, 1)
        self.context.paint()
        GLib.idle_add(self.update)
        
    def sweep(self):
        logging.debug('sweep')
        for x in range(1,self.hatSize + 1):
            for y in range(1,self.hatSize + 1):
                self.context.set_source_rgba(random.random(), random.random(), random.random())
                self.context.rectangle(x, y, 1, 1)
                self.context.fill()
                GLib.idle_add(self.update)
                time.sleep(0.05)
    
    def move(self, command):
        logging.debug('move')
        # Grab the current contents of the surface
        pattern = cairo.SurfacePattern(self.surface)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.surface.get_width(), self.surface.get_height())
        context = cairo.Context(surface)
        context.set_source(pattern)
        context.paint()
        pattern = cairo.SurfacePattern(surface)
        moveMatrix = cairo.Matrix()
        moveMatrix.scale(float(surface.get_width()) / self.hatSize, -float(surface.get_height()) / self.hatSize)
        moveMatrix.translate(-1, -(self.hatSize + 1))
        logmatrix(logging.debug, moveMatrix)

        if command.startswith('up'):
            moveMatrix.translate(0,-1)
            logmatrix(logging.debug, moveMatrix)
            pattern.set_matrix(moveMatrix)
            self.context.set_source(pattern)
            self.context.paint()
            self.context.set_source_rgba(0, 0, 0)
            self.context.rectangle(1, 1, self.hatSize, 1)
            self.context.fill()
        elif command.startswith('down'):
            moveMatrix.translate(0,1)
            logmatrix(logging.debug, moveMatrix)
            pattern.set_matrix(moveMatrix)
            self.context.set_source(pattern)
            self.context.paint()
            self.context.set_source_rgba(0, 0, 0)
            self.context.rectangle(1, self.hatSize, self.hatSize, 1)
            self.context.fill()
        elif command.startswith('left'):
            moveMatrix.translate(1,0)
            logmatrix(logging.debug, moveMatrix)
            pattern.set_matrix(moveMatrix)
            self.context.set_source(pattern)
            self.context.paint()
            self.context.set_source_rgba(0, 0, 0)
            self.context.rectangle(self.hatSize, 1, 1, self.hatSize)
            self.context.fill()
        elif command.startswith('right'):
            moveMatrix.translate(-1,0)
            logmatrix(logging.debug, moveMatrix)
            pattern.set_matrix(moveMatrix)
            self.context.set_source(pattern)
            self.context.paint()
            self.context.set_source_rgba(0, 0, 0)
            self.context.rectangle(1, 1, 1, self.hatSize)
            self.context.fill()
        else:
            return
                        
        GLib.idle_add(self.update)
    
    def processColour(self, colour):  
        paintColour = (-1, 0, 0)
        if len(colour) > 0:
            if colour.isalpha():
                if self.tcolours.has_key(colour):
                    if colour == 'random':
                        paintColour = (random.random(), random.random(), random.random())
                    elif colour == 'on':
                        paintColour = self.lastColour
                    elif colour == 'invert':
                        pass
                    else:
                        paintColour = self.tcolours.get(colour)
                else:
                    logging.debug('Unknown colour')
            else:
                # Check for some kind of number
                colournumber = -1
                if colour[0] == '#':
                    colour = colour.replace('#', '0x', 1)
                logging.debug('Colour number string %s', colour)
                try:
                    colournumber = int(colour, 0)
                except ValueError:
                    pass
                if colournumber >= 0 and colournumber < 0xffffff:
                    r = float((colournumber & 0xff0000) >> 16) / 255.
                    g = float((colournumber & 0xff00) >> 8) / 255.
                    b = float(colournumber & 0xff)/ 255.
                    paintColour = (r, g, b)
                else:
                    logging.debug('Bad colour number')
        else:
            logging.debug('Badly formatted colour command')
        return paintColour
                
    def pixel(self, command):
        logging.debug('pixel')
        if command.find(',') != -1:
            logging.debug('Its a coordinate')
            if command[1] == ',' and command[0].isdigit() and command[2].isdigit():
                try:
                    col = int(command[0])
                except ValueError:
                    logging.debug('Bad column coordinate')
                    col = 0
                try:
                    row = int(command[2])
                except ValueError:
                    logging.debug('Bad row coordinate')
                    row = 0
                colour = command[3:]
        elif len(command) > 0:
            logging.debug('Its an offset')
            try:
                if len(command) > 1:
                    offset = int(command[0:2]) - 1
                    colour = command[2:]
                else:
                    offset = int(command[0]) - 1
                    colour = command[1:]
            except ValueError:
                logging.debug('Bad offset')
                offset = 0
            row, col = divmod(offset, self.hatSize)
            row = row + 1
            col = col + 1
            
        
        if len(colour) > 0:
            logging.debug('Col %d Row %d Colour %s', col, row, colour)
            paintColour = self.processColour(colour)
        else:
            paintColour = self.lastColour

        if(paintColour[0] >= 0.):
            self.lastColour = paintColour
            self.context.set_source_rgba(self.lastColour[0], self.lastColour[1], self.lastColour[2])
            self.context.rectangle(col, row, 1, 1)
            self.context.fill()
            GLib.idle_add(self.update)
    
    def row(self, command):
        logging.debug('row')
        if command[0].isdigit() and int(command[0]) > 0 and int(command[0]) < 9 and command[1:].isalpha() and len(command[1:]) == 8:
            for col in range(1, self.hatSize + 1):
                if self.tcolours.has_key(command[col]):
                    r, g, b = self.tcolours.get(command[col])
                    self.context.set_source_rgba(r, g, b)
                    self.context.rectangle(col, int(command[0]), 1, 1)
                    self.context.fill()
                else:
                    break
            if col == self.hatSize:
                GLib.idle_add(self.update)
            else:
                logging.debug('Row command badly formatted - bad colour')
        else:
            logging.debug('Row command badly formatted %s %s %d', command[0], command[1:], len(command[1:]))

    def col(self, command):
        logging.debug('col')
        if command[0].isdigit() and int(command[0]) > 0 and int(command[0]) < 9 and command[1:].isalpha() and len(command[1:]) == 8:
            for row in range(1,self.hatSize + 1):
                if self.tcolours.has_key(command[row]):
                    r, g, b = self.tcolours.get(command[row])
                    self.context.set_source_rgba(r, g, b)
                    self.context.rectangle(int(command[0]), row, 1, 1)
                    self.context.fill()
                else:
                    break
            if row == self.hatSize:
                GLib.idle_add(self.update)
            else:
                logging.debug('Col command badly formatted - bad colour')
        else:
            logging.debug('Col command badly formatted %s %s %d', command[0], command[1:], len(command[1:]))

    def terminate(self):
        logging.debug('Terminating scratch thread')
        self.stop_event.set()
        threading.Thread.join(self)        

def main():
    # Initialize GTK Application
    Application = UnicornEmu("uk.co.beardandsandals.unicornemu", Gio.ApplicationFlags.FLAGS_NONE)

    # Start GUI

    Application.run(None)

if __name__ == "__main__":
    # For backwards compatibity
    GObject.threads_init()
    
    # Initialize the GTK application
    main()
    
