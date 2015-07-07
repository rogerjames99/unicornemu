#!/usr/bin/env python

import logging
import argparse
import os
from gi.repository import Gtk
import cairo
import numpy as np
import random
import threading
import socket
import time
import struct


class UnicornEmu:
    def __init__(self):
        # Constants
        self.imageSize = 1000

        
        # Initialise logging
        logging.basicConfig(filename='unicornemu.log', level=logging.DEBUG, filemode='w', \
                             format='%(thread)x %(funcName)s %(lineno)d %(levelname)s:%(message)s')
        
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

        
       
        self.context.scale(float(self.surface.get_width()) / self.hatSize, float(self.surface.get_height()) / self.hatSize)
        # Put some random colours in
        for y in range(self.hatSize):
            for x in range(self.hatSize):
                self.context.set_source_rgba(random.random(), random.random(), random.random())
                self.context.rectangle(x, y, 1, 1)
                self.context.fill()
                
        # dirty the drawingArea
        self.drawingArea.queue_draw()
                
        # Intialise the thread
        threading.Thread.__init__(self)                
        self.stop_event = threading.Event()
        self.start()
        
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
        self.drawingArea.queue_draw()
        
    def sweep(self):
        logging.debug('sweep')
        for y in range(self.hatSize):
            for x in range(self.hatSize):
                self.context.set_source_rgba(random.random(), random.random(), random.random())
                self.context.rectangle(x, y, 1, 1)
                self.context.fill()
                self.drawingArea.queue_draw()
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
        # This needs cleaning up the scaling and translation matrices are done in the wrong order
        if command.startswith('up'):
            testmatrix = cairo.Matrix(x0=0, y0=1, xx=float(surface.get_width())/self.hatSize, yy=float(surface.get_height())/self.hatSize)
            pattern.set_matrix(cairo.Matrix(x0=0, y0=1.0 * float(surface.get_height())/self.hatSize, xx=float(surface.get_width())/self.hatSize, yy=float(surface.get_height())/self.hatSize))
            self.context.set_source(pattern)
            self.context.paint()
            self.context.set_source_rgba(0, 0, 0)
            self.context.rectangle(0, 7, self.hatSize, 1)
            self.context.fill()
        elif command.startswith('down'):
            pattern.set_matrix(cairo.Matrix(x0=0, y0=-1.0 * float(surface.get_height())/self.hatSize, xx=float(surface.get_width())/self.hatSize, yy=float(surface.get_height())/self.hatSize))
            self.context.set_source(pattern)
            self.context.paint()
            self.context.set_source_rgba(0, 0, 0)
            self.context.rectangle(0, 0, self.hatSize, 1)
            self.context.fill()
        elif command.startswith('left'):
            pattern.set_matrix(cairo.Matrix(x0=1.0 * float(surface.get_width())/self.hatSize, y0=0, xx=float(surface.get_width())/self.hatSize, yy=float(surface.get_height())/self.hatSize))
            self.context.set_source(pattern)
            self.context.paint()
            self.context.set_source_rgba(0, 0, 0)
            self.context.rectangle(7, 0, 1, self.hatSize)
            self.context.fill()
        elif command.startswith('right'):
            pattern.set_matrix(cairo.Matrix(x0=-1.0 * float(surface.get_width())/self.hatSize, y0=0, xx=float(surface.get_width())/self.hatSize, yy=float(surface.get_height())/self.hatSize))
            self.context.set_source(pattern)
            self.context.paint()
            self.context.set_source_rgba(0, 0, 0)
            self.context.rectangle(0, 0, 1, self.hatSize)
            self.context.fill()
        else:
            return
            
        self.drawingArea.queue_draw()

    def pixel(self, command):
        logging.debug('pixel')
        if command.find(',') != -1:
            logging.debug('Its a coordinate')
            if command[1] == ',' and command[0].isdigit() and command[2].isdigit():
                x = int(command[0])
                y = int(command[2])
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
                        self.context.rectangle(x, y, 1, 1)
                        self.context.fill()
                        self.drawingArea.queue_draw()
                    else:
                        logging.debug('Unknown colour')
                else:
                    logging.debug('Pixel command badly formatted')
        elif command[0:1].isdigit() and command[2:].isalpha():
            logging.debug('Its an offset')
    
    def row(self, command):
        logging.debug('row')
        if command[0].isdigit() and int(command[0]) < 8 and command[1:].isalpha() and len(command[1:]) == 8:
            for i in range(8):
                if self.tcolours.has_key(command[1+i]):
                    r, g, b = self.tcolours.get(command[1+i])
                    self.context.set_source_rgba(r, g, b)
                    self.context.rectangle(i, int(command[0]), 1, 1)
                    self.context.fill()
                else:
                    break
            if i == 7:
                self.drawingArea.queue_draw()
            else:
                logging.debug('Pixel command badly formatted - bad clour')
        else:
            logging.debug('Pixel command badly formatted %s %s %d', command[0], coammnd[1:], len(command[1:]))

    def col(self, command):
        logging.debug('col')
        if command[0].isdigit() and int(command[0]) < 8 and command[1:].isalpha() and len(command[1:]) == 8:
            for i in range(8):
                if self.tcolours.has_key(command[1+i]):
                    r, g, b = self.tcolours.get(command[1+i])
                    self.context.set_source_rgba(r, g, b)
                    self.context.rectangle(int(command[0]), i, 1, 1)
                    self.context.fill()
                else:
                    break
            if i == 7:
                self.drawingArea.queue_draw()
            else:
                logging.debug('Pixel command badly formatted - bad colour')
        else:
            logging.debug('Pixel command badly formatted %s %s %d', command[0], coammnd[1:], len(command[1:]))

    def terminate(self):
        logging.debug('Terminating scratch thread')
        self.stop_event.set()
        threading.Thread.join(self)        

if __name__ == '__main__':
    ui = UnicornEmu()
    Gtk.main()
'''
    lettercolours = ['r', 'g', 'b', 'c', 'm', 'y', 'w', '0', '1', 'z']
    ledcolours = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow', 'white', 'off', 'on',
                  'invert', 'random']

    if tcolours is None:  #only define dictionary on first pass
        tcolours = {'red': (255, 0, 0), 'green': (0, 255, 0), 'blue': (0, 0, 255),
                    'cyan': (0, 255, 255), 'magenta': (255, 0, 255), 'yellow': (255, 255, 0),
                    'white': (255, 255, 255), 'off': (0, 0, 0), 'on': (255, 255, 255),
                    'invert': (0, 0, 0)}

    origdataraw = self.dataraw
    self.dataraw = self.dataraw[self.dataraw.find(
        "broadcast") + 10:]  # split dataraw so that operations are sequential
    broadcastList = ((self.dataraw).strip()).split(' ')

    for broadcastListLoop in broadcastList:
        self.dataraw = " " + str(broadcastListLoop) + " "

        if self.bFindValue("matrixuse"):
            #print "mu" , self.value
            if self.value == '4':
                self.matrixUse = 4
                self.matrixMult = 4
                self.matrixLimit = 4
                self.matrixRangemax = 2
                #print self.matrixMult,self.matrixLimit,self.matrixRangemax
            elif self.value == '9':
                self.matrixUse = 9
                self.matrixMult = 3
                self.matrixLimit = 2
                self.matrixRangemax = 3
                #print self.matrixMult,self.matrixLimit,self.matrixRangemax
            elif self.value == '16':
                self.matrixUse = 16
                self.matrixMult = 2
                self.matrixLimit = 2
                self.matrixRangemax = 4
                #print self.matrixMult,self.matrixLimit,self.matrixRangemax
            else:
                self.matrixUse = 64
                self.matrixMult = 1
                self.matrixLimit = 1
                self.matrixRangemax = 8
                #print self.matrixMult,self.matrixLimit,self.matrixRangemax

        #print "outside", self.matrixMult,self.matrixLimit,self.matrixRangemax

        if self.bFind("allon"):
            for y in range(0, 8):
                for x in range(0, 8):
                    UH.set_pixel(x, y, self.matrixRed, self.matrixGreen, self.matrixBlue)
            UH.show()

        if self.bFind("alloff"):
            for y in range(0, 8):
                for x in range(0, 8):
                    UH.set_pixel(x, y, 0, 0, 0)
            UH.show()

        if self.bFind("sweep"):
            print "sweep"

            for ym in range(0, self.matrixRangemax):
                for xm in range(0, self.matrixRangemax):
                    self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                        ledcolours[random.randint(0, 6)], (0, 0, 0))
                    for yy in range(0, self.matrixLimit):
                        for xx in range(0, self.matrixLimit):
                            UH.set_pixel((xm * self.matrixMult) + xx,
                                         7 - ((ym * self.matrixMult) + yy), self.matrixRed,
                                         self.matrixGreen, self.matrixBlue)
                    UH.show()
                    time.sleep(0.05)

        if self.bFindValue("red"):
            self.matrixRed = int(self.valueNumeric) if self.valueIsNumeric else 0
            if self.value == "on": self.matrixRed = 255
            if self.value == "off": self.matrixRed = 0

        if self.bFindValue("green"):
            self.matrixGreen = int(self.valueNumeric) if self.valueIsNumeric else 0
            if self.value == "on": self.matrixGreen = 255
            if self.value == "off": self.matrixGreen = 0

        if self.bFindValue("blue"):
            self.matrixBlue = int(self.valueNumeric) if self.valueIsNumeric else 0
            if self.value == "on": self.matrixBlue = 255
            if self.value == "off": self.matrixBlue = 0

        if self.bFindValue("colour"):
            #print "colour" ,self.value
            if self.value == "invert":
                tcolours[
                    "invert"] = 255 - self.matrixRed, 255 - self.matrixGreen, 255 - self.matrixBlue
            if self.valueIsNumeric:
                colourIndex = max(1, min(8, int(self.value))) - 1
                self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                    ledcolours[colourIndex], (128, 128, 128))
            else:
                if self.value[0] == "#":
                    try:
                        self.value = (self.value + "00000000")[0:7]
                        self.matrixRed = int(self.value[1:3], 16)
                        self.matrixGreen = int(self.value[3:5], 16)
                        self.matrixBlue = int(self.value[5:], 16)
                        #print "matrxired", self.matrixRed
                    except:
                        pass
                else:
                    ledcolour = self.value
                    self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(self.value, (
                        128, 128, 128))
                    if ledcolour == 'random': self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                        ledcolours[random.randint(0, 6)], (128, 128, 128))
            tcolours["on"] = self.matrixRed, self.matrixGreen, self.matrixBlue

            #print "rgb", self.matrixRed,self.matrixGreen,self.matrixBlue
            #print tcolours

        if self.bFind("pixel"):
            pixelProcessed = False
            for ym in range(0, self.matrixRangemax):
                for xm in range(0, self.matrixRangemax):
                    for ledcolour in ledcolours:
                        if (self.bFindValue("pixel", ledcolour) and (
                                    self.value == (str(xm + 1) + "," + str(ym + 1)))):
                            print "1st catch,xm,ym", xm, ym
                            self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                                ledcolour, (self.matrixRed, self.matrixGreen, self.matrixBlue))
                            if ledcolour == 'random':
                                self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                                    ledcolours[random.randint(0, 6)], (64, 64, 64))
                            #print "pixel",self.matrixRed,self.matrixGreen,self.matrixBlue
                            for yy in range(0, self.matrixLimit):
                                for xx in range(0, self.matrixLimit):
                                    #print "led no" ,led
                                    if (ledcolour != "invert"):
                                        UH.set_pixel((xm * self.matrixMult) + xx,
                                                     7 - ((ym * self.matrixMult) + yy),
                                                     self.matrixRed, self.matrixGreen,
                                                     self.matrixBlue)
                                    else:
                                        gnp = UH.get_pixel((xm * self.matrixMult) + xx,
                                                           7 - ((ym * self.matrixMult) + yy))
                                        #print "before" ,gnp
                                        gnpi = map(lambda a: (255 - a), gnp)
                                        #print "after", gnpi
                                        r, g, b = gnpi
                                        #print "rgb", r,g,b
                                        UH.set_pixel((xm * self.matrixMult) + xx,
                                                     7 - ((ym * self.matrixMult) + yy), r, g, b)
                            UH.show()
                            pixelProcessed = True

            if not pixelProcessed:
                #print "#", self.value[-7:]
                fullvalue = self.value
                if ("xxxxxxx" + fullvalue)[-7] == "#":
                    for ym in range(0, self.matrixRangemax):
                        for xm in range(0, self.matrixRangemax):
                            if (self.bFindValue("pixel", fullvalue[-7:]) and (
                                        self.value == (str(xm + 1) + "," + str(ym + 1)))):
                                #print "led,self.value",led,self.value
                                try:
                                    c = (fullvalue[-7:] + "00000000")[0:7]
                                    #print "full", c
                                    r = int(c[1:3], 16)
                                    g = int(c[3:5], 16)
                                    b = int(c[5:], 16)
                                    for yy in range(0, self.matrixLimit):
                                        for xx in range(0, self.matrixLimit):
                                            UH.set_pixel((xm * self.matrixMult) + xx,
                                                         7 - ((ym * self.matrixMult) + yy), r,
                                                         g, b)
                                    UH.show()
                                    pixelProcessed = True
                                except:
                                    pass

            if not pixelProcessed:
                for ym in range(0, self.matrixRangemax):
                    for xm in range(0, self.matrixRangemax):
                        if self.bFindValue("pixel" + str(xm + 1) + "," + str(ym + 1)):
                            ledcolour = self.value
                            self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                                ledcolour, (self.matrixRed, self.matrixGreen, self.matrixBlue))
                            if ledcolour == 'random': self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                                ledcolours[random.randint(0, 6)], (32, 32, 32))
                            print "3rd catch xm,ym ", xm, ym
                            for yy in range(0, self.matrixLimit):
                                for xx in range(0, self.matrixLimit):
                                    UH.set_pixel((xm * self.matrixMult) + xx,
                                                 7 - ((ym * self.matrixMult) + yy),
                                                 self.matrixRed, self.matrixGreen,
                                                 self.matrixBlue)
                            UH.show()
                            pixelProcessed = True

            if not pixelProcessed:
                for led in range(0, self.matrixUse):
                    if (self.bFindValue("pixel") and self.value == str(led + 1)):
                        ym = int(int(led) / self.matrixRangemax)
                        xm = led % self.matrixRangemax
                        #print "xm,ym" ,xm,ym
                        #print self.matrixRed,self.matrixGreen,self.matrixBlue
                        #print self.matrixMult,self.matrixLimit,self.matrixRangemax,led, ym, ym
                        for yy in range(0, self.matrixLimit):
                            for xx in range(0, self.matrixLimit):
                                UH.set_pixel((xm * self.matrixMult) + xx,
                                             7 - ((ym * self.matrixMult) + yy), self.matrixRed,
                                             self.matrixGreen, self.matrixBlue)
                        UH.show()
                        pixelProcessed = True

            if not pixelProcessed:
                for led in range(0, self.matrixUse):
                    for ledcolour in ledcolours:
                        if (self.bFindValue("pixel", ledcolour) and self.value == str(led + 1)):
                            ym = int(int(led) / self.matrixRangemax)
                            xm = led % self.matrixRangemax
                            #print "xm,ym" ,xm,ym
                            self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                                ledcolour, (self.matrixRed, self.matrixGreen, self.matrixBlue))
                            if ledcolour == 'random':
                                self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                                    ledcolours[random.randint(0, 6)], (64, 64, 64))
                            #print "pixel",self.matrixRed,self.matrixGreen,self.matrixBlue
                            for yy in range(0, self.matrixLimit):
                                for xx in range(0, self.matrixLimit):
                                    #print "led no" ,led
                                    if (ledcolour != "invert"):
                                        UH.set_pixel((xm * self.matrixMult) + xx,
                                                     7 - ((ym * self.matrixMult) + yy),
                                                     self.matrixRed, self.matrixGreen,
                                                     self.matrixBlue)
                                    else:
                                        gnp = UH.get_pixel((xm * self.matrixMult) + xx,
                                                           7 - ((ym * self.matrixMult) + yy))
                                        #print "before" ,gnp
                                        gnpi = map(lambda a: (255 - a), gnp)
                                        #print "after", gnpi
                                        r, g, b = gnpi
                                        #print "rgb", r,g,b
                                        UH.set_pixel((xm * self.matrixMult) + xx,
                                                     7 - ((ym * self.matrixMult) + yy), r, g, b)
                            UH.show()
                            pixelProcessed = True

            if not pixelProcessed:
                #print "#", self.value[-7:]
                fullvalue = self.value
                if ("xxxxxxx" + fullvalue)[-7] == "#":
                    for led in range(0, self.matrixUse):
                        if (self.bFindValue("pixel", fullvalue[-7:]) and self.value == str(
                                    led + 1)):
                            ym = int(int(led) / self.matrixRangemax)
                            xm = led % self.matrixRangemax
                            #print "led,self.value",led,self.value
                            try:
                                c = (fullvalue[-7:] + "00000000")[0:7]
                                #print "full", c
                                r = int(c[1:3], 16)
                                g = int(c[3:5], 16)
                                b = int(c[5:], 16)
                                for yy in range(0, self.matrixLimit):
                                    for xx in range(0, self.matrixLimit):
                                        UH.set_pixel((xm * self.matrixMult) + xx,
                                                     7 - ((ym * self.matrixMult) + yy), r, g, b)
                                UH.show()
                                pixelProcessed = True
                            except:
                                pass

            if self.bFind("getpixel"):
                for ym in range(0, self.matrixRangemax):
                    for xm in range(0, self.matrixRangemax):
                        if self.bFindValue("getpixel" + str(xm + 1) + "," + str(ym + 1)):
                            gnp = UH.get_pixel(xm * self.matrixMult, 7 - (ym * self.matrixMult))
                            #print "getpixel led,xm,ymgnp",led,xm,ym,gnp
                            r, g, b = gnp
                            bcolourname = "#" + ("000000" + (str(
                                hex(b + (g * 256) + (r * 256 * 256))))[2:])[-6:]
                            bcolour = str(r).zfill(3) + str(g).zfill(3) + str(b).zfill(3)
                            #ledcolours = ['red','green','blue','cyan','magenta','yellow','white','off','on','invert','random']
                            #bcolourname = "black"
                            try:
                                bcolourname = ledcolours[
                                    ["255000000", "000255000", "000000255", "000255255",
                                     "255000255", "255255000", "255255255"].index(bcolour)]
                            except ValueError:
                                pass
                            #print "col lookup", bcolourname
                            sensor_name = 'colour'
                            bcast_str = 'sensor-update "%s" %s' % (sensor_name, bcolourname)
                            #print 'sending: %s' % bcast_str
                            msgQueue.put((5,bcast_str))

                for led in range(0, self.matrixUse):
                    if (self.bFindValue("getpixel") and self.value == str(led + 1)):
                        ym = int(int(led) / self.matrixRangemax)
                        xm = led % self.matrixRangemax
                        gnp = UH.get_pixel(xm * self.matrixMult, 7 - (ym * self.matrixMult))
                        #print "getpixel led,xm,ymgnp",led,xm,ym,gnp
                        r, g, b = gnp
                        bcolourname = "#" + ("000000" + (str(hex(b + (g * 256) + (r * 256 * 256))))[
                                                        2:])[-6:]
                        bcolour = str(r).zfill(3) + str(g).zfill(3) + str(b).zfill(3)
                        #ledcolours = ['red','green','blue','cyan','magenta','yellow','white','off','on','invert','random']
                        #bcolourname = "black"
                        try:
                            bcolourname = ledcolours[
                                ["255000000", "000255000", "000000255", "000255255", "255000255",
                                 "255255000", "255255255"].index(bcolour)]
                        except ValueError:
                            pass
                        #print "col lookup", bcolourname
                        sensor_name = 'colour'
                        bcast_str = 'sensor-update "%s" %s' % (sensor_name, bcolourname)
                        #print 'sending: %s' % bcast_str
                        msgQueue.put((5,bcast_str))


        if self.bFindValue("bright"):
            sghGC.ledDim = int(self.valueNumeric) if self.valueIsNumeric else 20
            try:
                UH.brightness(max(0, min(1, float(float(sghGC.ledDim) / 100))))
                UH.show()
                sensor_name = 'bright'
                bcast_str = 'sensor-update "%s" %d' % (sensor_name, sghGC.ledDim)
                #print 'sending: %s' % bcast_str
                msgQueue.put((5,bcast_str))
            except:
                pass

        if self.bFindValue('matrixpattern'):
            bit_pattern = (
                              self.value + 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')[
                          0:64]
            #print 'bit_pattern %s' % bit_pattern
            for j in range(0, 64):
                ym = j // 8
                xm = j - (8 * ym)
                bp = bit_pattern[j]
                if bp in lettercolours:
                    self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                        ledcolours[lettercolours.index(bp)],
                        (self.matrixRed, self.matrixGreen, self.matrixBlue))
                    UH.set_pixel(xm, 7 - ym, self.matrixRed, self.matrixGreen, self.matrixBlue)
            UH.show()
            
        if self.bFind("moveleft"):
            for y in range(0, self.matrixRangemax):
                for x in range(0, self.matrixRangemax - 1):
                    oldr, oldg, oldb = UH.get_pixel(x + 1, y)
                    #print "oldpixel" , oldpixel
                    UH.set_pixel(x, y, oldr, oldg, oldb)
                UH.set_pixel(7, y, 0, 0, 0)
            UH.show()

        if self.bFind("moveright"):
            for y in range(0, self.matrixRangemax):
                for x in range(self.matrixRangemax - 1, 0, -1):
                    #print "y,x",y,x
                    oldr, oldg, oldb = UH.get_pixel(x - 1, y)
                    #print "oldpixel" , oldpixel
                    UH.set_pixel(x, y, oldr, oldg, oldb)
                UH.set_pixel(0, y, 0, 0, 0)
            UH.show()

        if self.bFind("moveup"):
            for x in range(0, self.matrixRangemax):
                for y in range(0, self.matrixRangemax - 1):
                    oldr, oldg, oldb = UH.get_pixel(x, y + 1)
                    #print "oldpixel" , oldpixel
                    UH.set_pixel(x, y, oldr, oldg, oldb)
                UH.set_pixel(x, 7, 0, 0, 0)
            UH.show()

        if self.bFind("movedown"):
            for x in range(0, self.matrixRangemax):
                for y in range(self.matrixRangemax - 1, 0, -1):
                    #print "y,x",y,x
                    oldr, oldg, oldb = UH.get_pixel(x, y - 1)
                    #print "oldpixel" , oldpixel
                    UH.set_pixel(x, y, oldr, oldg, oldb)
                UH.set_pixel(x, 0, 0, 0, 0)
            UH.show()
        
        if self.bFind("invert"):
            for index in range(0, self.matrixUse):
                oldr, oldg, oldb = UH.get_neopixel(index)
                #print "oldpixel" , oldpixel
                UH.set_neopixel(index, 255 - oldr, 255 - oldg, 255 - oldb)
            UH.show()

        if self.bFindValue("level"):
            if self.valueIsNumeric:
                for index in range(0, self.matrixUse):
                    oldr, oldg, oldb = tuple(
                        [max(0, min(255, int(elim * (self.valueNumeric / 100.0)))) for elim in
                         UH.get_neopixel(index)])
                    #print "old" , oldr,oldg,oldb
                    #print "oldpixel" , oldpixel
                    UH.set_neopixel(index, oldr, oldg, oldb)
                UH.show()

        rowList = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        for i in range(0, 8):
            if self.bFindValue('row' + rowList[i]):
                bit_pattern = (self.value + "xxxxxxxx")[0:8]
                #print 'bit_pattern %s' % bit_pattern
                for j in range(0, 8):
                    ym = i
                    xm = j
                    bp = bit_pattern[j]
                    if bp in lettercolours:
                        self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                            ledcolours[lettercolours.index(bp)],
                            (self.matrixRed, self.matrixGreen, self.matrixBlue))
                        UH.set_pixel(xm, 7 - ym, self.matrixRed, self.matrixGreen,
                                     self.matrixBlue)
                UH.show()

        for i in range(0, 8):
            if self.bFindValue('row' + str(i + 1)):
                bit_pattern = (self.value + "xxxxxxxx")[0:8]
                #print 'bit_pattern %s' % bit_pattern
                for j in range(0, 8):
                    ym = i
                    xm = j
                    bp = bit_pattern[j]
                    if bp in lettercolours:
                        self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                            ledcolours[lettercolours.index(bp)],
                            (self.matrixRed, self.matrixGreen, self.matrixBlue))
                        UH.set_pixel(xm, 7 - ym, self.matrixRed, self.matrixGreen,
                                     self.matrixBlue)
                UH.show()

        colList = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        for i in range(0, 8):
            if self.bFindValue('col' + colList[i]):
                #print self.value
                bit_pattern = (self.value + "xxxxxxxx")[0:8]
                for j in range(0, 8):
                    ym = j
                    xm = i
                    bp = bit_pattern[j]
                    if bp in lettercolours:
                        self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                            ledcolours[lettercolours.index(bp)],
                            (self.matrixRed, self.matrixGreen, self.matrixBlue))
                        UH.set_pixel(xm, 7 - ym, self.matrixRed, self.matrixGreen,
                                     self.matrixBlue)
                UH.show()

        for i in range(0, 8):
            if self.bFindValue('col' + str(i + 1)):
                #print tcolours
                #print self.matrixRed,self.matrixGreen,self.matrixBlue
                #print self.value
                bit_pattern = (self.value + "xxxxxxxx")[0:8]
                for j in range(0, 8):
                    ym = j
                    xm = i
                    bp = bit_pattern[j]
                    if bp in lettercolours:
                        self.matrixRed, self.matrixGreen, self.matrixBlue = tcolours.get(
                            ledcolours[lettercolours.index(bp)],
                            (self.matrixRed, self.matrixGreen, self.matrixBlue))

                        UH.set_pixel(xm, 7 - ym, self.matrixRed, self.matrixGreen,
                                     self.matrixBlue)
                UH.show()

        if self.bFindValue('loadimage'):
            try:
                sb = subprocess.Popen(
                    ['convert', '-scale', '8x8!', '+matte', self.value, 'sghimage.bmp']).wait()
            except:
                pass
            #time.sleep(1)
            # When reading a binary file, always add a 'b' to the file open mode
            with open('sghimage.bmp', 'rb') as f:
                #with open(self.value + '.bmp', 'rb') as f:
                # BMP files store their width and height statring at byte 18 (12h), so seek
                # to that position
                f.seek(10)

                # The width and height are 4 bytes each, so read 8 bytes to get both of them
                bytes = f.read(4)

                # Here, we decode the byte array from the last step. The width and height
                # are each unsigned, little endian, 4 byte integers, so they have the format
                # code '<II'. See http://docs.python.org/3/library/struct.html for more info
                bmpdata = int(struct.unpack('<I', bytes)[0])
                #print bmpdata

                # Print the width and height of the image
                print('Data starts at:  ' + str(bmpdata))
                f.seek(bmpdata)

                bytes = f.read(192)  # move to start of pixel data
                pixel = struct.unpack('192B', bytes)  #get 64 pixels * 3 for BGR
                #print "pixel",pixel
                for i in range(0, 64):
                    UH.set_pixel(i % 8, 7 - (i // 8), pixel[(i * 3) + 2], pixel[(i * 3) + 1],
                                 pixel[(i * 3) + 0])

                UH.show()

        if self.bFindValue('saveimage'):
            # try:
            # sb = subprocess.Popen(['convert', '-scale', '8x8!', '+matte', self.value , 'sghimage.bmp']).wait()
            # except:
            # pass
            #time.sleep(1)
            # When reading a binary file, always add a 'b' to the file open mode
            with open('sghimage.bmp', 'wb') as f:
                header = [0x42, 0x4D, 0xF6, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x36,
                          0x00, 0x00, 0x00, 0x28, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00,
                          0x08, 0x00, 0x00, 0x00, 0x01, 0x00, 0x18, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x13, 0x0B, 0x00, 0x00, 0x13, 0x0B,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
                for i in header:
                    f.write(chr(i))
                for i in range(0, 64):
                    r, g, b = UH.get_pixel(i % 8, 7 - (i // 8))
                    #print "rgb",r,g,b
                    f.write(chr(b))
                    f.write(chr(g))
                    f.write(chr(r))
            sb = subprocess.Popen(['cp', 'sghimage.bmp', self.value + '.bmp']).wait()

        if self.bFindValue('load2image'):
            try:
                sb = subprocess.Popen(['convert', '-scale', '16x16!', '+matte', self.value,
                                       'sghimage.bmp']).wait()
            except:
                pass
            #time.sleep(1)
            # When reading a binary file, always add a 'b' to the file open mode
            with open('sghimage.bmp', 'rb') as f:
                #with open(self.value + '.bmp', 'rb') as f:
                # BMP files store their width and height statring at byte 18 (12h), so seek
                # to that position
                f.seek(10)

                # The width and height are 4 bytes each, so read 8 bytes to get both of them
                bytes = f.read(4)

                # Here, we decode the byte array from the last step. The width and height
                # are each unsigned, little endian, 4 byte integers, so they have the format
                # code '<II'. See http://docs.python.org/3/library/struct.html for more info
                bmpdata = int(struct.unpack('<I', bytes)[0])

                # Print the width and height of the image
                print('Data starts at:  ' + str(bmpdata))
                f.seek(bmpdata)

                bytes = f.read(768)  # move to start of pixel data
                pixel = struct.unpack('768B', bytes)  #get 64 pixels * 3 for BGR
                #print "pixel",pixel

                j = -18
                for i in range(0, 64):
                    if i % 8 == 0:
                        j += 18
                    else:
                        j += 2
                    #print "i,j",i,j
                    UH.set_pixel(i % 8, 7 - (i // 8), pixel[(j * 3) + 2], pixel[(j * 3) + 1],
                                 pixel[(j * 3) + 0])
                UH.show()
'''
