#!/usr/bin/env python

import argparse
import cairo
from gi.repository import Gdk, Gtk, GLib, Gio, GObject, DBus
import logging
import os
import random
import select
import struct
import sys
import threading

import time

logFormat = '%(relativeCreated)d %(thread)x %(funcName)s %(lineno)d %(levelname)s:%(message)s'
#logFormat = '%(funcName)s %(lineno)d %(levelname)s:%(message)s'

def logmatrix(logger, matrix):
    #xx, yx, xy, yy, x0, y0 = matrix
    #logger('Matrix xx=%f yx=%f xy=%f yy=%f x0=%f y0=%f', xx, yx, xy, yy, x0, y0)
    return

class UnicornEmu(Gtk.Application):

    ###############################################################################################################
    # Local classes
    ###############################################################################################################
 
    class MyWindow(object):
        
        ###############################################################################################################
        # Local classes
        ###############################################################################################################
 
        class MatrixDisplay(object):

            ###############################################################################################################
            # Initialisation
            ###############################################################################################################
 

            def __init__(self, hostname, address, portNumber, container):
                logging.debug('Creating new MatrixDisplay object')
                
                self.hatSize = 8
                self.imageSize = 1000
                self.hostname = hostname
                self.address = address
                self.portNumber = portNumber
                self.sweepx = 1
                self.sweepy = 1
                self.cancellable = Gio.Cancellable.new()
                self.runPublisher = False

                
                # Use cairo to do the matrix stuff
                self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.imageSize, self.imageSize)
                self.context = cairo.Context(self.surface)
                
                # Create gtk stuff
                builder = Gtk.Builder.new_from_resource('/uk/co/beardandsandals/UnicornEmu/remotehost.ui')    
                builder.connect_signals(self)
                self.frame = builder.get_object('unicornemuRemoteHost')
                self.drawingArea = builder.get_object('drawingArea')
                    
                self.tcolours = {'r': (1, 0, 0), 'red': (1, 0, 0), 'g': (0, 1, 0), 'green': (0, 1, 0), 'b': (0, 0, 1), 'blue': (0, 0, 1),
                            'c': (0, 1, 1), 'cyan': (0, 1, 1), 'm': (1, 0, 1), 'magenta': (1, 0, 1), 'y': (1, 1, 0), 'yellow': (1, 1, 0),
                            'w': (1, 1, 1), 'white': (1, 1, 1), '0': (0, 0, 0), 'off': (0, 0, 0), '1': (1, 1, 1), 'on': (1, 1, 1),
                            'z': (0, 0, 0), 'invert': (0, 0, 0), 'random' : (0,0,0)}
                self.lastColour = (0,0,0)
                
                if hostname == 'localhost':
                    self.hostname_for_title = GLib.get_host_name()
                    self.drawingArea.set_size_request(500, 500)
                    container.pack_end(self.frame, False, False, 0)
                    container.set_child_packing(self.frame, True, True, 0, Gtk.PackType.START)
                else:
                    self.hostname_for_title = hostname
                    self.drawingArea.set_size_request(100, 100)
                    container.pack_start(self.frame, False, False, 0)
                
                logging.debug('Surface matrix')
                self.context.scale(float(self.surface.get_width()) / self.hatSize, -float(self.surface.get_height()) / self.hatSize)
                self.context.translate(-1, -(self.hatSize + 1))
                logmatrix(logging.debug, self.context.get_matrix())
                
                for x in range(1,self.hatSize + 1):
                    for y in range(1,self.hatSize + 1):
                        self.context.set_source_rgba(random.random(), random.random(), random.random())
                        self.context.rectangle(x, y, 1, 1)
                        self.context.fill()
                
                self.update()
                
                # Connect to scratch
                self.socketClient = Gio.SocketClient.new() # Keep this hanging about in case of time outs etc.
                logging.debug('Started connection process')
                if  len(self.address) > 0:
                    self.socketClient.connect_to_host_async(self.address, self.portNumber, self.cancellable, self.connect_to_host_async_callback, None)
                else:
                    self.socketClient.connect_to_host_async(self.hostname, self.portNumber, self.cancellable, self.connect_to_host_async_callback, None)
                
            ###############################################################################################################
            # Callbacks                
            ###############################################################################################################
            
            def zeroconfRegisterCallback(self, sdRef, flags, errorCode, name, regtype, domain):
                if errorCode == pybonjour.kDNSServiceErr_NoError:
                    logging.debug("Registered service - name '%s' regtype '%s' domain '%s'", name, regtype, domain)
                else:
                    logging.debug("Failed to register service - errorcode %d", errorCode)
        
            def connect_to_host_async_callback(self, source_object, res, user_data):
                logging.debug("async_callback - hostname '%s'", self.hostname)
                label = self.frame.get_label_widget()
                if label is None:
                    return
                try:
                    self.socketConnection = self.socketClient.connect_to_host_finish(res)
                except GLib.GError, error:
                    if error.code == Gio.IOErrorEnum.CONNECTION_REFUSED or \
                            error.code == Gio.IOErrorEnum.TIMED_OUT:
                        # Scratch has not responded or has refused the connection
                        # Try again in 30 seconds
                        logging.debug(error.message)
                        logging.debug('Retry connect in 30 seconds')
                        label.set_text("%s '%s'" % (self.hostname_for_title, error.message))
                        self.createTimeout(30, self.retry_connect_callback)
                        return
                    elif error.code == Gio.IOErrorEnum.HOST_NOT_FOUND or \
                            error.code == Gio.IOErrorEnum.FAILED: # Gtk seems to return zero for host not found
                        # Cannot resolve the hostname
                        logging.debug(error.message)
                        logging.debug('Retry connect in 30 seconds')
                        label.set_text("%s '%s'" % (self.hostname_for_title, error.message))
                        self.createTimeout(30, self.retry_connect_callback)
                        return
                    elif error.code == Gio.IOErrorEnum.NETWORK_UNREACHABLE or \
                            error.code == Gio.IOErrorEnum.HOST_UNREACHABLE:
                        # Network failure (ICMP destination unreachable code)
                        logging.debug(error.message)
                        logging.debug('creating timeout %d', error.code)
                        label.set_text('%s (%s)' % (self.hostname_for_title, error.message))
                        self.createTimeout(30, self.retry_connect_callback)
                        return
                    else:
                        logging.debug("connect callback code %d domain '%s' message '%s'", error.code, error.domain, error.message)
                        dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING, Gtk.ButtonsType.CLOSE, error.message)
                        dialog.run()
                        self.window.close()
                        return
                    
                if not self.socketConnection is None:
                    logging.debug('Connected at first attempt')
                    label.set_text('%s (connected)' % self.hostname_for_title)
                    self.inputStream = self.socketConnection.get_input_stream()
                    self.publishHost()
                    # Start read scratch messages
                    self.inputStream.read_bytes_async(4, GLib.PRIORITY_HIGH, self.cancellable, self.read_scratch_message_size_callback, None)
                else:
                    logging.debug('should not get here 1')

            def connect_to_host_async_timer_callback(self, source_object, res, user_data):
                logging.debug("timer_callback - hostname '%s'", self.hostname)
                label = self.frame.get_label_widget()
                if label is None:
                    return
                try:
                    self.socketConnection = self.socketClient.connect_to_host_finish(res)
                except GLib.GError, error:
                    if error.code == Gio.IOErrorEnum.CONNECTION_REFUSED or \
                            error.code == Gio.IOErrorEnum.TIMED_OUT:
                        # Scratch has not responded or has refused the connection
                        # Try again in 30 seconds
                        logging.debug(error.message)
                        logging.debug('Retry connect in 30 seconds')
                        label.set_text('%s (%s)' % (self.hostname_for_title, error.message))
                        self.createTimeout(30, self.retry_connect_callback)
                        return
                    elif error.code == Gio.IOErrorEnum.HOST_NOT_FOUND or \
                            error.code == Gio.IOErrorEnum.FAILED: # Gtk seems to return zero for host not found
                        # Cannot resolve the hostname
                        logging.debug(error.message)
                        logging.debug('Retry connect in 30 seconds')
                        label.set_text('%s (%s)' % (self.hostname_for_title, error.message))
                        self.createTimeout(30, self.retry_connect_callback)
                        return
                    elif error.code == Gio.IOErrorEnum.NETWORK_UNREACHABLE or \
                            error.code == Gio.IOErrorEnum.HOST_UNREACHABLE:
                        # Network failure (ICMP destination unreachable code)
                        logging.debug(error.message)
                        logging.debug('creating timeout %d', error.code)
                        label.set_text('%s (%s)' % (self.hostname_for_title, error.message))
                        self.createTimeout(30, self.retry_connect_callback)
                        return
                    else:
                        logging.debug("connect callback code %d domain '%s' message '%s'", error.code, error.domain, error.message)
                        dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING, Gtk.ButtonsType.CLOSE, error.message)
                        dialog.run()
                        self.window.close()
                        return
                
                if self.socketConnection:
                    logging.debug('Connected after a retry')
                    label.set_text('%s (connected)' % self.hostname_for_title)
                    self.inputStream = self.socketConnection.get_input_stream()
                    self.publishHost()
                    self.inputStream.read_bytes_async(4, GLib.PRIORITY_HIGH, self.cancellable, self.read_scratch_message_size_callback, None)
                else:
                    logging.debug('should not get here 2')
                
            def drawMatrix(self, widget, cr): # linked to draw signal
                logging.debug('Draw callback')
                x ,y, width, height = cr.clip_extents()
                xscale = float(width) / float(self.surface.get_width())
                yscale = float(height) / float(self.surface.get_height())
                cr.scale(xscale, yscale)
                cr.set_operator(cairo.OPERATOR_SOURCE)
                cr.set_source_surface(self.surface)
                cr.paint()
                return False
            
            def notify_callback(self):
                pass
            
            def read_scratch_message_content_callback(self, source_object, res, user_data):
                logging.debug("read_scratch_message_content_callback - host '%s'", self.hostname)
                try:
                    scratch_message = self.inputStream.read_bytes_finish(res)
                except GLib.GError, error:
                        dialog = Gtk.MessageDialog(self.frame, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING, Gtk.ButtonsType.CLOSE, error.message)
                        dialog.run()
                        #self.window.close()
                        return
                finally:
                    logging.debug('Resetting cancellable')
                    self.cancellable.reset()
                
                if scratch_message.get_size() != self.scratch_message_length:
                    # I assume the connection is broken in some way so close it and start again
                    # May need to rethink this if I see fragmentation
                    logging.debug('Read size != message size - Reconnecting')
                    self.socketConnection.close()
                    self.frame.get_label_widget().set_text('%s (connection lost)' % self.hostname_for_title)
                    if self.runPublisher == True:
                        self.runPublisher = False
                        self.publisherThread.join()

                    self.socketClient = Gio.SocketClient.new()
                    self.createTimeout(30, self.retry_connect_callback)
                    return
                
                logging.debug("Scratch message '%s'", scratch_message.get_data())

                # Process message
                self.process_scratch_message(scratch_message.get_data())
                
                # Start again
                self.inputStream.read_bytes_async(4, GLib.PRIORITY_HIGH, None, self.read_scratch_message_size_callback, None)
                
            def read_scratch_message_size_callback(self, source_object, res, user_data):
                logging.debug("read_scratch_message_size_callback - hostname '%s'", self.hostname)
                try:
                    count_bytes = self.inputStream.read_bytes_finish(res)
                except GLib.GError, error:
                        dialog = Gtk.MessageDialog(self.frame, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING, Gtk.ButtonsType.CLOSE, error.message)
                        dialog.run()
                        #self.window.close()
                        return
                finally:
                    logging.debug('Resetting cancellable')
                    self.cancellable.reset()
                
                if count_bytes.get_size() != 4:
                    # I assume the connection is broken in some way so close it and start again
                    logging.debug('read size != 4 reconnecting')
                    self.socketConnection.close()
                    self.frame.get_label_widget().set_text('%s (connection lost)' % self.hostname_for_title)
                    if self.runPublisher == True:
                        self.runPublisher = False
                        self.publisherThread.join()
                    self.socketClient = Gio.SocketClient.new()
                    self.createTimeout(30, self.retry_connect_callback)
                    return
                
                self.scratch_message_length = struct.unpack('>L', count_bytes.get_data())[0]
                
                
                logging.debug('Scratch message length %d', self.scratch_message_length)
                # Read the content of the scratch message
                self.inputStream.read_bytes_async(self.scratch_message_length, GLib.PRIORITY_HIGH, None, 
                                                self.read_scratch_message_content_callback, None)
                                                
            def retry_connect_callback(self, userdata):
                logging.debug('retry connect callback')
                self.socketClient.connect_to_host_async(self.hostname,
                                                        self.portNumber,
                                                        self.cancellable,
                                                        self.connect_to_host_async_timer_callback, None)
                # make this a one off timer
                return False

            def sweep_timer_callback(self):
                logging.debug('sweepx %d sweepy %d', self.sweepx, self.sweepy)
                self.sweepy += 1
                if self.sweepy > self.hatSize:
                    self.sweepy = 1
                    self.sweepx += 1
                self.context.set_source_rgba(random.random(), random.random(), random.random())
                self.context.rectangle(self.sweepx, self.sweepy, 1, 1)
                self.context.fill()
                self.update()
                if self.sweepx == self.hatSize and self.sweepy == self.hatSize:
                    return False
                return True
                                                
            ###############################################################################################################
            # Methods              
            ###############################################################################################################
            
            def alloff(self):
                logging.debug('alloff')
                self.context.set_source_rgb(0, 0, 0)
                self.context.paint()
                self.update()
                
            def allon(self):
                logging.debug('allon')
                self.context.set_source_rgb(1, 1, 1)
                self.context.paint()
                self.update()
                
            def cleanup(self): # Kill any callbacks
                if not self.timeoutSource is None:
                    logging.debug('Removing timeout from main loop')
                    self.timeoutSource.destroy()
                    
                if not self.cancellable is None:
                    logging.debug('Cleaning up cancellable functions')
                    self.cancellable.cancel()
                else:
                    logging.debug('No cancellable functions')
                
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
                        self.update()
                    else:
                        logging.debug('Col command badly formatted - bad colour')
                else:
                    logging.debug('Col command badly formatted %s %s %d', command[0], command[1:], len(command[1:]))
            
            def colour(self, command):
                logging.debug('colour')
                paintColour = self.processColour(command)

                if(paintColour[0] >= 0.):
                    self.lastColour = paintColour
                    
            def createTimeout(self, interval, callback):
                logging.debug('Creating new timeout_source')
                self.timeoutSource = GLib.timeout_source_new_seconds(interval)  
                self.timeoutSource.set_callback(callback)
                self.timeoutSource.attach(None)
                          
            def matrixuse(self):
                logging.debug('matrixuse')
                
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
                                
                self.update()
            
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
                    logging.debug('Col %d Row %d Colour %s' % col, row, colour)
                    paintColour = self.processColour(colour)
                else:
                    paintColour = self.lastColour

                if(paintColour[0] >= 0.):
                    self.lastColour = paintColour
                    self.context.set_source_rgba(self.lastColour[0], self.lastColour[1], self.lastColour[2])
                    self.context.rectangle(col, row, 1, 1)
                    self.context.fill()
                    self.update()
            
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
                        logging.debug('Colour number string %s' % colour)
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
                        
            def process_scratch_message(self, message):
                words = message.split(' ',1)
            
                if words[0].lower() != 'broadcast':
                    logging.debug('Discarding message; not a broadcast')
                    return
                    
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
                        
            def publishHost(self):
                if self.hostname == 'localhost':
                    if Application.zeroconfSupport:
                        # Publish using zeroconf
                        self.publisherThread = threading.Thread(target = self.runPublishHostZeroconf)
                        self.runPublisher = True
                        self.publisherThread.start()
            
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
                        self.update()
                    else:
                        logging.debug('Row command badly formatted - bad colour')
                else:
                    logging.debug('Row command badly formatted %s %s %d', command[0], command[1:], len(command[1:]))
            
            def runPublishHostZeroconf(self):
                logging.debug('Running the zeroconf publisher')
                self.register_sdRef = pybonjour.DNSServiceRegister(name = '%s Scratch Remote Sensor Server' % self.hostname_for_title,
                                                                    regtype = '_scratch._tcp', port = 42001, callBack = self.zeroconfRegisterCallback)
                try:
                    try:
                        while self.runPublisher:
                            ready = select.select([self.register_sdRef], [], [], 1) # I hate having to use a timeout here! What a waste of cycles.
                            if self.register_sdRef in ready[0]:
                                pybonjour.DNSServiceProcessResult(self.register_sdRef)
                    except (KeyboardInterrupt, SystemExit):
                        pass
                finally:
                    logging.debug('Closing the zeroconf publisher')
                    self.register_sdRef.close()
                

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

            def sweep(self):
                logging.debug('sweep')
                self.sweepx = 1
                self.sweepy = 1
                self.context.set_source_rgba(random.random(), random.random(), random.random())
                self.context.rectangle(self.sweepx, self.sweepy, 1, 1)
                self.context.fill()
                self.update()
                self.timeoutId = GLib.timeout_add(50, self.sweep_timer_callback)
            
            def update(self):
                logging.debug('Dirtying the drawing area')
                self.drawingArea.queue_draw()
                
        ###############################################################################################################
        # Initialisation
        ###############################################################################################################
 
        def __init__(self, application, *args):
            # Constants
            self.localHostname = GLib.get_host_name()
            
            # Local variables
            self.zeroconfToThumbnailMap = {} # indexed by zeoconf domain and name
            
            # Set up the gui                                 
            self.builder = Gtk.Builder.new_from_resource('/uk/co/beardandsandals/UnicornEmu/unicornemu.ui')    
            self.builder.connect_signals(self)
            mainWindow = self.builder.get_object('unicornEmuApplicationWindow')
            mainWindow.set_application(application)
            mainWindow.show()
            
            self.primaryMatrix = self.MatrixDisplay(application.hostname, "", 42001, self.builder.get_object('unicornEmuLocalDisplayBox'))
            
            self.runZeroconf = False
            if application.zeroconfSupport:
                # Run the zeroconf service browser
                # Easiest to use my own thread. I would really like to integrate this better with GOBject.
                # More research needed on tbis
                self.zeroconfBrowserThread = threading.Thread(target = self.runZeroconfBrowser)
                self.runZeroconf = True
                self.zeroconfBrowserThread.start()
                

        ###############################################################################################################
        # Callbacks                
        ###############################################################################################################

        def zeroconfBrowserCallback(self, sdRef, flags, interfaceIndex, errorCode, serviceName,
                                    regtype, replyDomain):
                                        
            if errorCode != pybonjour.kDNSServiceErr_NoError:
                return

            if flags & pybonjour.kDNSServiceFlagsAdd:
                logging.debug("Service '%s' added - regtype '%s' replyDomain '%s'", serviceName, regtype, replyDomain)
                self.zeroconfResolved = []

                if (replyDomain, serviceName) in self.zeroconfToThumbnailMap:
                    # ignore this for the time being - more work needed to handle service detail changes
                    logging.debug("Ignoring zeroconf entry already in cache")
                    return
                    
                self.zeroconfServiceName = serviceName
                self.zeroconfReplyDomain = replyDomain
                    
                resolve_sdRef = pybonjour.DNSServiceResolve(0,
                                                            interfaceIndex,
                                                            serviceName,
                                                            regtype,
                                                            replyDomain,
                                                            self.zeroconfResolverCallback)

                try:
                    while not self.zeroconfResolved:
                        ready = select.select([resolve_sdRef], [], [], 5)
                        if resolve_sdRef not in ready[0]:
                            logging.debug('Resolve timed out')
                            break
                        pybonjour.DNSServiceProcessResult(resolve_sdRef)
                    else:
                        self.zeroconfResolved.pop()
                finally:
                    resolve_sdRef.close()
                    
            else:
                logging.debug("Service '%s' removed - replyDomain '%s'", serviceName, replyDomain)
                if (replyDomain, serviceName) in self.zeroconfToThumbnailMap:
                    logging.debug("Destroy thumbnail")
                    self.destroy_thumbnail(replyDomain, serviceName)
                else:
                    logging.debug("domain '%s' name '%s' not in my cache", serviceName, replyDomain)
            
        def zeroconfResolverCallback(self, sdRef, flags, interfaceIndex, errorCode, fullname,
                             hosttarget, port, txtRecord):
            if errorCode == pybonjour.kDNSServiceErr_NoError:
                logging.debug("Resolved service: fullname '%s' hosttarget '%s' port %s", fullname, hosttarget, port)
                self.zeroconfResolved.append(True)
                if hosttarget.split('.')[0].lower() != self.localHostname.lower(): # Case insensitive comparison 
                    logging.debug("Creating thumbnail for remote host '%s'", hosttarget)
                    # Need to queue this on the gui thread
                    GLib.idle_add(self.create_new_thumbnail, self.zeroconfReplyDomain, self.zeroconfServiceName, hosttarget, '', port)

        def quit_cb(self, *args):
            logging.debug('Shutting down')
            if self.runZeroconf == True:
                self.runZeroconf = False
                self.zeroconfBrowserThread.join()
            if self.primaryMatrix.runPublisher == True:
                self.primaryMatrix.runPublisher = False
                self.primaryMatrix.publisherThread.join()
            logging.shutdown()

        ###############################################################################################################
        # Methods            
        ###############################################################################################################
        
        def create_new_thumbnail(self, zeroconfDomain, zeroconfName, hostname, address, portnumber):
            # If this is a new host then create thumbnail
            # For the time being this means I will ignore calls for multiple ports on the same host
            if not (zeroconfDomain, zeroconfName) in self.zeroconfToThumbnailMap:
                # Create a new thumbnail window for a remote scratch host
                self.zeroconfToThumbnailMap[(zeroconfDomain, zeroconfName)] = self.MatrixDisplay(hostname, address, portnumber, self.builder.get_object('unicormEmuRemoteDisplayBox'))
                logging.debug("Thumbnail map after add '%s'", self.zeroconfToThumbnailMap)
            return False # This function can be called via GLib.idle_add
                
        def destroy_thumbnail(self, zeroconfDomain, zeroconfName):
            logging.debug("Thumbnail map before delete'%s'", self.zeroconfToThumbnailMap)
            matrixDisplay = self.zeroconfToThumbnailMap[(zeroconfDomain, zeroconfName)]
            matrixDisplay.cleanup()
            matrixDisplay.frame.destroy()
            del self.zeroconfToThumbnailMap[(zeroconfDomain, zeroconfName)] # I am hoping that this destroys the MatrixDisplay object
            
        def runZeroconfBrowser(self):
            logging.debug('Running the zeroconf browser')
            self.browse_sdRef = pybonjour.DNSServiceBrowse(regtype = '_scratch._tcp',
                                                            callBack = self.zeroconfBrowserCallback)
            try:
                try:
                    while self.runZeroconf:
                        ready = select.select([self.browse_sdRef], [], [], 1) # I hate having to use a timeout here! What a waste of cycles.
                        if self.browse_sdRef in ready[0]:
                            pybonjour.DNSServiceProcessResult(self.browse_sdRef)
                except (KeyboardInterrupt, SystemExit):
                    pass
            finally:
                logging.debug('Closing the zeroconf browser')
                self.browse_sdRef.close()
                
    ###############################################################################################################
    # Initialisation
    ###############################################################################################################

    def __init__(self, application_id, flags):
        # Process command line options
        parser = argparse.ArgumentParser(description='Scratchgpio compatible emulator for Unicorn Hat')
        parser.add_argument('hostname', default='localhost', nargs='?',
                   help='The hostname of the scratch desktop')
        parser.add_argument('-v', '--verbose', nargs='?', const=True, default=False,
                   help='Send debug logging to stderr')
        parser.add_argument('--no-zeroconf', dest='zeroconf', action='store_false',
                   help='Disable zeroconf support')
        parser.set_defaults(zeroconf=True)

        args = parser.parse_args()
        self.hostname = args.hostname
                
                        
        Gtk.Application.__init__(self, application_id=application_id, flags=flags)
        
        # Hook up the activate signal
        self.connect('activate', self.activate_callback)
        
        # Initialise logging
        logging.basicConfig(filename=os.path.expanduser('~/unicornemu.log'), level=logging.DEBUG, filemode='w', \
                             format=logFormat)
                             
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        if args.verbose:
            formatter = logging.Formatter(logFormat)
            console.setFormatter(formatter)
            logging.getLogger('').addHandler(console)
        
        self.zeroconfSupport = False 
        if args.zeroconf == True:  
            try:
                global pybonjour
                import pybonjour
                self.zeroconfSupport = True
            except ImportError, error:
                dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK, "Zeroconf support not available")
                dialog.run()
                             
        logging.debug('Loading resources')
        
        # Load resources
        try:
            logging.debug("sys.platform '%s'", sys.platform)
            if sys.platform == 'win32':
                # Windows look in the current directory
                resources = Gio.Resource.load('unicornemu.gresource')
            else:
                resources = Gio.Resource.load(os.path.join('/usr/share/unicornemu', 'unicornemu.gresource'))
        except GLib.GError:
            resources = Gio.Resource.load(os.path.join(os.getcwd(), 'resources/unicornemu.gresource'))            

        try:
            Gio.resources_register(resources)
        except AttributeError:
            Gio.Resource._register(resources) # Backward compatibility

        logging.debug('Resources loaded and registered')
        
    ###############################################################################################################
    # Callbacks                
    ###############################################################################################################
        
    def activate_callback(self, *args):
        self.MyWindow(self, self.hostname)

        
    ###############################################################################################################
    # Methods            
    ###############################################################################################################
    
    # This class has no methods yet
    
def main():
    global Application
    # Initialize GTK Application
    Application = UnicornEmu("uk.co.beardandsandals.unicornemu", Gio.ApplicationFlags.FLAGS_NONE)

    # Start GUI
    Application.run(None)

if __name__ == "__main__":
    # For backwards compatibity
    GObject.threads_init()
    
    # Initialize the GTK application
    main()
    
