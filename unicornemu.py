#!/usr/bin/env python

import logging
import argparse
import os
from gi.repository import Gtk , GLib, GObject
import cairo
import numpy as np
import random
import threading
import socket
import time
import struct

def logmatrix(logger, matrix):
    xx, yx, xy, yy, x0, y0 = matrix
    logger('Matrix xx=%f yx=%f xy=%f yy=%f x0=%f y0=%f', xx, yx, xy, yy, x0, y0)

class UnicornEmu:
    def __init__(self):
        # Constants
        self.imageSize = 1000

        # Initialise logging
        logging.basicConfig(filename='unicornemu.log', level=logging.DEBUG, filemode='w', \
                             format='%(thread)x %(funcName)s %(lineno)d %(levelname)s:%(message)s')
                             
        logging.debug('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        
        # Process command line options
        parser = argparse.ArgumentParser(description='Scratchgpio compatible emulator for Unicorn Hat')
        parser.add_argument('hostname', default='localhost', nargs='?',
                   help='The hostname of the scratch desktop')

        args = parser.parse_args()
        self.hostname = args.hostname                
        
        # Set up the gui                     
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(os.getcwd(), 'unicornemu.ui'))
        self.builder.connect_signals(self)
        self.window = self.builder.get_object('unicornemuApplicationWindow')
        self.window.show()
        
        # Use cairo to do the matrix stuff
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.imageSize, self.imageSize)
                
        self.scratch = SocketThread(self.hostname, 42001, self.surface, self.builder.get_object('drawingArea'))
        

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
        Gtk.main_quit()
        
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
        self.lastColour = 'off'

        
       
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
                
            self.socket.settimeout(1)
                
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
                    socket.close()
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
                        logging.debug('matrixuse')
                    elif command == 'allon':
                        logging.debug('allon')
                    elif command == 'alloff':
                        self.alloff()
                    elif command == 'sweep':
                        self.sweep()
                    elif command.startswith('red'):
                        logging.debug('red')
                    elif command.startswith('green'):
                        logging.debug('green')
                    elif command.startswith('blue'):
                        logging.debug('blue')
                    elif command.startswith('colour'):
                        logging.debug('colour')
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
        
    def alloff(self):
        logging.debug('alloff')
        self.context.set_source_rgb(0, 0, 0)
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

    def pixel(self, command):
        logging.debug('pixel')
        if command.find(',') != -1:
            logging.debug('Its a coordinate')
            if command[1] == ',' and command[0].isdigit() and command[2].isdigit():
                col = int(command[0])
                row = int(command[2])
                colour = command[3:]
                if len(colour) == 0:
                    colour = self.lastColour
                elif colour.isalpha():
                    if self.tcolours.has_key(colour):
                        r, g, b = self.tcolours.get(colour)
                        if colour == random:
                            r = random.random()
                            g = random.random()
                            b = random.random()
                        self.context.set_source_rgba(r, g, b)
                        self.context.rectangle(col, row, 1, 1)
                        self.context.fill()
                        GLib.idle_add(self.update)
                    else:
                        logging.debug('Unknown colour')
                else:
                    logging.debug('Pixel command badly formatted')
        elif command[0:1].isdigit() and command[2:].isalpha():
            logging.debug('Its an offset')
    
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

if __name__ == '__main__':
    # For backwards compatibity
    GObject.threads_init()

    ui = UnicornEmu()
    Gtk.main()
    
