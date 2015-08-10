#!/usr/bin/env python

import logging
import argparse
import os
from gi.repository import Gdk, Gtk, GLib, Gio, GObject, DBus
import cairo
import numpy as np
import random
import threading
import time
import struct
import avahi
import avahi

# Node definitions for accessing Avahi via DBUS

NodeInfoForServer = Gio.DBusNodeInfo.new_for_xml(
'''<?xml version="1.0" standalone='no'?><!--*-nxml-*-->
<?xml-stylesheet type="text/xsl" href="introspect.xsl"?>
<!DOCTYPE node SYSTEM "introspect.dtd">

<!--
  This file is part of avahi.

  avahi is free software; you can redistribute it and/or modify it
  under the terms of the GNU Lesser General Public License as
  published by the Free Software Foundation; either version 2 of the
  License, or (at your option) any later version.

  avahi is distributed in the hope that it will be useful, but
  WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
  General Public License for more details.

  You should have received a copy of the GNU Lesser General Public
  License along with avahi; if not, write to the Free Software
  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
  02111-1307 USA.
-->

<node>

 <interface name="org.freedesktop.DBus.Introspectable">
    <method name="Introspect">
      <arg name="data" type="s" direction="out"/>
    </method>
  </interface>

  <interface name="org.freedesktop.Avahi.Server">

    <method name="GetVersionString">
      <arg name="version" type="s" direction="out"/>
    </method>

    <method name="GetAPIVersion">
      <arg name="version" type="u" direction="out"/>
    </method>

    <method name="GetHostName">
      <arg name="name" type="s" direction="out"/>
    </method>
    <method name="SetHostName">
      <arg name="name" type="s" direction="in"/>
    </method>
    <method name="GetHostNameFqdn">
      <arg name="name" type="s" direction="out"/>
    </method>
    <method name="GetDomainName">
      <arg name="name" type="s" direction="out"/>
    </method>

    <method name="IsNSSSupportAvailable">
      <arg name="yes" type="b" direction="out"/>
    </method>

    <method name="GetState">
      <arg name="state" type="i" direction="out"/>
    </method>

    <signal name="StateChanged">
      <arg name="state" type="i"/>
      <arg name="error" type="s"/>
    </signal>

    <method name="GetLocalServiceCookie">
      <arg name="cookie" type="u" direction="out"/>
    </method>

    <method name="GetAlternativeHostName">
      <arg name="name" type="s" direction="in"/>
      <arg name="name" type="s" direction="out"/>
    </method>

    <method name="GetAlternativeServiceName">
      <arg name="name" type="s" direction="in"/>
      <arg name="name" type="s" direction="out"/>
    </method>

    <method name="GetNetworkInterfaceNameByIndex">
      <arg name="index" type="i" direction="in"/>
      <arg name="name" type="s" direction="out"/>
    </method>
    <method name="GetNetworkInterfaceIndexByName">
      <arg name="name" type="s" direction="in"/>
      <arg name="index" type="i" direction="out"/>
    </method>

    <method name="ResolveHostName">
      <arg name="interface" type="i" direction="in"/>
      <arg name="protocol" type="i" direction="in"/>
      <arg name="name" type="s" direction="in"/>
      <arg name="aprotocol" type="i" direction="in"/>
      <arg name="flags" type="u" direction="in"/>

      <arg name="interface" type="i" direction="out"/>
      <arg name="protocol" type="i" direction="out"/>
      <arg name="name" type="s" direction="out"/>
      <arg name="aprotocol" type="i" direction="out"/>
      <arg name="address" type="s" direction="out"/>
      <arg name="flags" type="u" direction="out"/>
    </method>

    <method name="ResolveAddress">
      <arg name="interface" type="i" direction="in"/>
      <arg name="protocol" type="i" direction="in"/>
      <arg name="address" type="s" direction="in"/>
      <arg name="flags" type="u" direction="in"/>

      <arg name="interface" type="i" direction="out"/>
      <arg name="protocol" type="i" direction="out"/>
      <arg name="aprotocol" type="i" direction="out"/>
      <arg name="address" type="s" direction="out"/>
      <arg name="name" type="s" direction="out"/>
      <arg name="flags" type="u" direction="out"/>
    </method>

    <method name="ResolveService">
      <arg name="interface" type="i" direction="in"/>
      <arg name="protocol" type="i" direction="in"/>
      <arg name="name" type="s" direction="in"/>
      <arg name="type" type="s" direction="in"/>
      <arg name="domain" type="s" direction="in"/>
      <arg name="aprotocol" type="i" direction="in"/>
      <arg name="flags" type="u" direction="in"/>

      <arg name="interface" type="i" direction="out"/>
      <arg name="protocol" type="i" direction="out"/>
      <arg name="name" type="s" direction="out"/>
      <arg name="type" type="s" direction="out"/>
      <arg name="domain" type="s" direction="out"/>
      <arg name="host" type="s" direction="out"/>
      <arg name="aprotocol" type="i" direction="out"/>
      <arg name="address" type="s" direction="out"/>
      <arg name="port" type="q" direction="out"/>
      <arg name="txt" type="aay" direction="out"/>
      <arg name="flags" type="u" direction="out"/>
    </method>

    <method name="EntryGroupNew">
      <arg name="path" type="o" direction="out"/>
    </method>

    <method name="DomainBrowserNew">
      <arg name="interface" type="i" direction="in"/>
      <arg name="protocol" type="i" direction="in"/>
      <arg name="domain" type="s" direction="in"/>
      <arg name="btype" type="i" direction="in"/>
      <arg name="flags" type="u" direction="in"/>

      <arg name="path" type="o" direction="out"/>
    </method>

    <method name="ServiceTypeBrowserNew">
      <arg name="interface" type="i" direction="in"/>
      <arg name="protocol" type="i" direction="in"/>
      <arg name="domain" type="s" direction="in"/>
      <arg name="flags" type="u" direction="in"/>

      <arg name="path" type="o" direction="out"/>
    </method>

    <method name="ServiceBrowserNew">
      <arg name="interface" type="i" direction="in"/>
      <arg name="protocol" type="i" direction="in"/>
      <arg name="type" type="s" direction="in"/>
      <arg name="domain" type="s" direction="in"/>
      <arg name="flags" type="u" direction="in"/>

      <arg name="path" type="o" direction="out"/>
    </method>

    <method name="ServiceResolverNew">
      <arg name="interface" type="i" direction="in"/>
      <arg name="protocol" type="i" direction="in"/>
      <arg name="name" type="s" direction="in"/>
      <arg name="type" type="s" direction="in"/>
      <arg name="domain" type="s" direction="in"/>
      <arg name="aprotocol" type="i" direction="in"/>
      <arg name="flags" type="u" direction="in"/>

      <arg name="path" type="o" direction="out"/>
    </method>

    <method name="HostNameResolverNew">
      <arg name="interface" type="i" direction="in"/>
      <arg name="protocol" type="i" direction="in"/>
      <arg name="name" type="s" direction="in"/>
      <arg name="aprotocol" type="i" direction="in"/>
      <arg name="flags" type="u" direction="in"/>

      <arg name="path" type="o" direction="out"/>
    </method>

    <method name="AddressResolverNew">
      <arg name="interface" type="i" direction="in"/>
      <arg name="protocol" type="i" direction="in"/>
      <arg name="address" type="s" direction="in"/>
      <arg name="flags" type="u" direction="in"/>

      <arg name="path" type="o" direction="out"/>
    </method>

    <method name="RecordBrowserNew">
      <arg name="interface" type="i" direction="in"/>
      <arg name="protocol" type="i" direction="in"/>
      <arg name="name" type="s" direction="in"/>
      <arg name="clazz" type="q" direction="in"/>
      <arg name="type" type="q" direction="in"/>
      <arg name="flags" type="u" direction="in"/>

      <arg name="path" type="o" direction="out"/>
    </method>


  </interface>
</node>
''')

NodeInfoForServiceBrowser = Gio.DBusNodeInfo.new_for_xml('''<?xml version="1.0" standalone='no'?><!--*-nxml-*-->
<?xml-stylesheet type="text/xsl" href="introspect.xsl"?>
<!DOCTYPE node SYSTEM "introspect.dtd">

<!--
  This file is part of avahi.

  avahi is free software; you can redistribute it and/or modify it
  under the terms of the GNU Lesser General Public License as
  published by the Free Software Foundation; either version 2 of the
  License, or (at your option) any later version.

  avahi is distributed in the hope that it will be useful, but
  WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
  General Public License for more details.

  You should have received a copy of the GNU Lesser General Public
  License along with avahi; if not, write to the Free Software
  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
  02111-1307 USA.
-->

<node>

  <interface name="org.freedesktop.DBus.Introspectable">
    <method name="Introspect">
      <arg name="data" type="s" direction="out" />
    </method>
  </interface>

  <interface name="org.freedesktop.Avahi.ServiceBrowser">

    <method name="Free"/>

    <signal name="ItemNew">
      <arg name="interface" type="i"/>
      <arg name="protocol" type="i"/>
      <arg name="name" type="s"/>
      <arg name="type" type="s"/>
      <arg name="domain" type="s"/>
      <arg name="flags" type="u"/>
    </signal>

    <signal name="ItemRemove">
      <arg name="interface" type="i"/>
      <arg name="protocol" type="i"/>
      <arg name="name" type="s"/>
      <arg name="type" type="s"/>
      <arg name="domain" type="s"/>
      <arg name="flags" type="u"/>
    </signal>

    <signal name="Failure">
      <arg name="error" type="s"/>
    </signal>

    <signal name="AllForNow"/>

    <signal name="CacheExhausted"/>

  </interface>
</node>
''')



logFormat = '%(thread)x %(funcName)s %(lineno)d %(levelname)s:%(message)s'

def logmatrix(logger, matrix):
    xx, yx, xy, yy, x0, y0 = matrix
    logger('Matrix xx=%f yx=%f xy=%f yy=%f x0=%f y0=%f', xx, yx, xy, yy, x0, y0)

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
                
                '''    
                print 'expand', self.drawingArea.get_property('expand'), \
                        'height-request', self.drawingArea.get_property('height-request'), \
                        'width-request', self.drawingArea.get_property('width-request'), \
                        'hexpand', self.drawingArea.get_property('hexpand'), \
                        'vexpand', self.drawingArea.get_property('vexpand'), \
                        'hexpand-set', self.drawingArea.get_property('hexpand-set'), \
                        'vexpand-set', self.drawingArea.get_property('vexpand-set')
                        
                GLib.idle_add(self.constrain_aspect_ration_callback)
                '''
                    
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
                logging.debug('Started connection process %d', GLib.get_monotonic_time())
                if  len(self.address) > 0:
                    self.socketClient.connect_to_host_async(self.address, self.portNumber, None, self.connect_to_host_async_callback, None)
                else:
                    self.socketClient.connect_to_host_async(self.hostname, self.portNumber, None, self.connect_to_host_async_callback, None)
                
            ###############################################################################################################
            # Callbacks                
            ###############################################################################################################
            
            def connect_to_host_async_callback(self, source_object, res, user_data):
                logging.debug( 'async_callback %d', GLib.get_monotonic_time())
                try:
                    self.socketConnection = self.socketClient.connect_to_host_finish(res)
                except GLib.Error, error:
                    if error.code == Gio.IOErrorEnum.CONNECTION_REFUSED or \
                            error.code == Gio.IOErrorEnum.TIMED_OUT:
                        # Scratch has not responded or has refused the connection
                        # Try again in 30 seconds
                        logging.debug(error.message)
                        logging.debug('Retry connect in 30 seconds')
                        self.frame.get_label_widget().set_text("%s '%s'" % (self.hostname_for_title, '!'))
                        GLib.timeout_add_seconds(30, self.retry_connect)
                        return
                    elif error.code == Gio.IOErrorEnum.HOST_NOT_FOUND or \
                            error.code == Gio.IOErrorEnum.FAILED: # Gtk seems to return zero for host not found
                        # Cannot resolve the hostname
                        logging.debug(error.message)
                        logging.debug('Retry connect in 30 seconds')
                        self.frame.get_label_widget().set_text("%s '%s'" % (self.hostname_for_title, error.message))
                        GLib.timeout_add_seconds(30, self.retry_connect)
                        return
                    elif error.code == Gio.IOErrorEnum.NETWORK_UNREACHABLE or \
                            error.code == Gio.IOErrorEnum.HOST_UNREACHABLE:
                        # Network failure (ICMP destination unreachable code)
                        logging.debug(error.message)
                        logging.debug('creating timeout %d', error.code)
                        self.frame.get_label_widget().set_text('%s (%s)' % (self.hostname_for_title, error.message))
                        GLib.timeout_add_seconds(30, self.retry_connect)
                        return
                    else:
                        logging.debug("connect callback code %d domain '%s' message '%s'", error.code, error.domain, error.message)
                        dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING, Gtk.ButtonsType.CLOSE, error.message)
                        dialog.run()
                        self.window.close()
                        return
                    
                if self.socketConnection != None:
                    logging.debug('Connected at first attempt')
                    self.frame.get_label_widget().set_text('%s (connected)' % self.hostname_for_title)
                    self.inputStream = self.socketConnection.get_input_stream()
                    # Start read scratch messages
                    self.inputStream.read_bytes_async(4, GLib.PRIORITY_HIGH, None, self.read_scratch_message_size_callback, None)
                else:
                    logging.debug('should not get here 1')

            def connect_to_host_async_timer_callback(self, source_object, res, user_data):
                try:
                    self.socketConnection = self.socketClient.connect_to_host_finish(res)
                except GLib.Error, error:
                    if error.code == Gio.IOErrorEnum.CONNECTION_REFUSED or \
                            error.code == Gio.IOErrorEnum.TIMED_OUT:
                        # Scratch has not responded or has refused the connection
                        # Try again in 30 seconds
                        logging.debug(error.message)
                        logging.debug('Retry connect in 30 seconds')
                        self.frame.get_label_widget().set_text('%s (%s)' % (self.hostname_for_title, error.message))
                        GLib.timeout_add_seconds(30, self.retry_connect)
                        return
                    elif error.code == Gio.IOErrorEnum.HOST_NOT_FOUND or \
                            error.code == Gio.IOErrorEnum.FAILED: # Gtk seems to return zero for host not found
                        # Cannot resolve the hostname
                        logging.debug(error.message)
                        logging.debug('Retry connect in 30 seconds')
                        self.frame.get_label_widget().set_text('%s (%s)' % (self.hostname_for_title, error.message))
                        GLib.timeout_add_seconds(30, self.retry_connect)
                        return
                    elif error.code == Gio.IOErrorEnum.NETWORK_UNREACHABLE or \
                            error.code == Gio.IOErrorEnum.HOST_UNREACHABLE:
                        # Network failure (ICMP destination unreachable code)
                        logging.debug(error.message)
                        logging.debug('creating timeout %d', error.code)
                        self.frame.get_label_widget().set_text('%s (%s)' % (self.hostname_for_title, error.message))
                        GLib.timeout_add_seconds(30, self.retry_connect)
                        return
                    else:
                        logging.debug("connect callback code %d domain '%s' message '%s'", error.code, error.domain, error.message)
                        dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING, Gtk.ButtonsType.CLOSE, error.message)
                        dialog.run()
                        self.window.close()
                        return
                
                if self.socketConnection:
                    logging.debug('Connected after a retry')
                    self.frame.get_label_widget().set_text('%s (connected)' % self.hostname_for_title)
                    self.inputStream = self.socketConnection.get_input_stream()
                    self.inputStream.read_bytes_async(4, GLib.PRIORITY_HIGH, None, self.read_scratch_message_size_callback, None)
                else:
                    logging.debug('should not get here 2')
                
            def constrain_aspect_ration_callback(self):
                print 'Constrain aspect ratio' # I have tried this four ways since last sunday and still cannot get it to work!!!!
                hints = Gdk.Geometry()
                hints.max_aspect = hints.min_aspect = 1.
                self.drawingArea.get_toplevel().set_geometry_hints(self.drawingArea, hints, Gdk.WindowHints.ASPECT)
            
            def drawMatrix(self, widget, cr):
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
                logging.debug('read_scratch_message_content_callback')
                try:
                    scratch_message = self.inputStream.read_bytes_finish(res)
                except GLib.Error, error:
                        dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING, Gtk.ButtonsType.CLOSE, error.message)
                        dialog.run()
                        self.window.close()
                        return
                
                if scratch_message.get_size() != self.scratch_message_length:
                    # I assume the connection is broken in some way so close it and start again
                    # May need to rethink this if I see fragmentation
                    logging.debug('Reconnecting')
                    self.socketConnection.close()
                    self.window.builder.get_object('unicornemuMainMatrixLabel').set_text('%s (connection lost)' % self.hostname_for_title)
                    self.socketClient = Gio.SocketClient.new()
                    GLib.timeout_add_seconds(30, self.retry_connect)
                    return
                
                logging.debug("Scratch message '%s'", scratch_message.get_data())

                # Process message
                self.process_scratch_message(scratch_message.get_data())
                
                # Start again
                self.inputStream.read_bytes_async(4, GLib.PRIORITY_HIGH, None, self.read_scratch_message_size_callback, None)
                
            def read_scratch_message_size_callback(self, source_object, res, user_data):
                logging.debug('read_scratch_message_size_callback')
                try:
                    count_bytes = self.inputStream.read_bytes_finish(res)
                except GLib.Error, error:
                        dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING, Gtk.ButtonsType.CLOSE, error.message)
                        dialog.run()
                        self.window.close()
                        return
                
                if count_bytes.get_size() != 4:
                    # I assume the connection is broken in some way so close it and start again
                    logging.debug('Reconnecting')
                    self.socketConnection.close()
                    self.window.builder.get_object('unicornemuMainMatrixLabel').set_text('%s (connection lost)' % self.hostname_for_title)
                    self.socketClient = Gio.SocketClient.new()
                    GLib.timeout_add_seconds(30, self.retry_connect)
                    return
                
                self.scratch_message_length = struct.unpack('>L', count_bytes.get_data())[0]
                
                
                logging.debug('Scratch message length %d', self.scratch_message_length)
                # Read the content of the scratch message
                self.inputStream.read_bytes_async(self.scratch_message_length, GLib.PRIORITY_HIGH, None, 
                                                self.read_scratch_message_content_callback, None)
                                                
            ###############################################################################################################
            # Methods              
            ###############################################################################################################
            
            def retry_connect(self):
                logging.debug('retry connect')
                self.socketClient.connect_to_host_async(self.hostname,
                                                        self.portNumber,
                                                        None,
                                                        self.connect_to_host_async_timer_callback, None)
                # make this a one off timer
                return False

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

            def update(self):
                logging.debug('Dirtying the drawing area')
                self.drawingArea.queue_draw()
                
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

            def matrixuse(self):
                logging.debug('matrixuse')
                
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
                
            def sweep(self):
                logging.debug('sweep')
                for x in range(1,self.hatSize + 1):
                    for y in range(1,self.hatSize + 1):
                        self.context.set_source_rgba(random.random(), random.random(), random.random())
                        self.context.rectangle(x, y, 1, 1)
                        self.context.fill()
                        self.update()
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
            
        ###############################################################################################################
        # Initialisation
        ###############################################################################################################
 
        def __init__(self, application, *args):
            # Constants
            self.localHostname = GLib.get_host_name()
            
            # Local variables
            self.avahiToThumbnailMap = {} # indexed by avahi domain and name
            
            # Set up the gui                                 
            self.builder = Gtk.Builder.new_from_resource('/uk/co/beardandsandals/UnicornEmu/unicornemu.ui')    
            self.builder.connect_signals(self)
            mainWindow = self.builder.get_object('unicornEmuApplicationWindow')
            mainWindow.set_application(application)
            mainWindow.show()
            
            self.primaryMatrix = self.MatrixDisplay(application.hostname, "", 42001, self.builder.get_object('unicornEmuLocalDisplayBox'))
            
            # Start the process of connecting to Avahi
            if application.avahiSupport:
                Gio.bus_get(Gio.BusType.SYSTEM, None, self.bus_get_callback, None)

        ###############################################################################################################
        # Callbacks                
        ###############################################################################################################

        def browserCallback(self, proxy, sender, signal, args):
            if signal == 'ItemNew':
                '''
                <signal name="ItemNew">
                  <arg name="interface" type="i"/>   
                  <arg name="protocol" type="i"/>
                  <arg name="name" type="s"/>
                  <arg name="type" type="s"/>
                  <arg name="domain" type="s"/>
                  <arg name="flags" type="u"/>
                </signal>
                '''
                interface = args[0] # The 
                protocol = args[1]
                name = args[2]
                service_type = args[3]
                domain = args[4]
                flags = args[5]
                
                logging.debug("ItemNew -\ncacheNumber %d\nprotocol %d\nname '%s'\ntype '%s'\ndomain '%s'\nflags 0x%X", \
                            interface, protocol, name, service_type, domain, flags)
                            
                if (domain, name) in self.avahiToThumbnailMap:
                    # ignore this for the time being - more work needed to handle service detail changes
                    logging.debug("Ignoring avahi entry already in cache")
                    return
                
                '''
                <method name="ResolveService">
                  <arg name="interface" type="i" direction="in"/>
                  <arg name="protocol" type="i" direction="in"/>
                  <arg name="name" type="s" direction="in"/>
                  <arg name="type" type="s" direction="in"/>
                  <arg name="domain" type="s" direction="in"/>
                  <arg name="aprotocol" type="i" direction="in"/>
                  <arg name="flags" type="u" direction="in"/>

                  <arg name="interface" type="i" direction="out"/>
                  <arg name="protocol" type="i" direction="out"/>
                  <arg name="name" type="s" direction="out"/>
                  <arg name="type" type="s" direction="out"/>
                  <arg name="domain" type="s" direction="out"/>
                  <arg name="host" type="s" direction="out"/>
                  <arg name="aprotocol" type="i" direction="out"/>
                  <arg name="address" type="s" direction="out"/>
                  <arg name="port" type="q" direction="out"/>
                  <arg name="txt" type="aay" direction="out"/>
                  <arg name="flags" type="u" direction="out"/>
                </method>
                '''
                try:
                    returns = self.avahiserver.ResolveService('(iisssiu)', interface, protocol, name, service_type,
                                                                        domain, avahi.PROTO_INET, 0)
                except GLib.Error, error:
                    logging.debug("Error on ResolveService method call -- code %d message '%s'", error.code, error.message)
                    return
                                                                        
                resolved_interface = args[0]
                resolved_protocol = args[1]
                resolved_name = args[2]
                resolved_service_type = args[3]
                resolved_domain = args[4]
                hostname = returns[5]
                aprotocol = returns[6]
                address = returns[7]
                portnumber = int(returns[8])
                txt = returns[9]
                resolved_flags = returns[10]
                logging.debug("Found service -\nresolved_interface %d\nresolved_protocol %d\nresolved_name '%s\n"
                                "resolved_service_type '%s'\nresolved_domain '%s'\n"
                                "hostname '%s\n' aprotocol %d\naddress '%s'\n"
                                "portnumber 0x%X\ntxt '%s'\nresolved_flags 0x%X", \
                            resolved_interface, resolved_protocol, resolved_name, resolved_service_type,  resolved_domain, \
                            hostname, aprotocol, address, portnumber, txt, resolved_flags)
                                        
                if hostname.split('.')[0] != self.localHostname: 
                    logging.debug("Creating thumbnail for remote host '%s'", hostname)
                    self.create_new_thumbnail(resolved_domain, resolved_name, hostname, address, portnumber)

                    
            elif signal == 'ItemRemove':
                '''
                <signal name="ItemRemove"
                  <arg name="interface" type="i"/>
                  <arg name="protocol" type="i"/>
                  <arg name="name" type="s"/>
                  <arg name="type" type="s"/>
                  <arg name="domain" type="s"/>
                  <arg name="flags" type="u"/>
                </signal>
                '''
                interface = args[0]
                protocol = args[1]
                name = args[2]
                service_type = args[3]
                domain = args[4]
                flags = args[5]
                
                logging.debug("ItemRemove -\ninterface %d\nprotocol %d\nname '%s'\ntype '%s'\ndomain '%s'\nflags 0x%X", \
                            interface, protocol, name, service_type, domain, flags)
                
                if (domain, name) in self.avahiToThumbnailMap:
                    logging.debug("Kill the wabbit")
                    self.destroy_thumbnail(domain, name)
                else:
                    logging.debug("domain '%s' name '%s' not in my cache", domain, name)
                    
            elif signal == 'Failure':
                '''
                <signal name="Failure">
                  <arg name="error" type="s"/>
                </signal>
                '''
                logging.debug('Failure ignored')
            elif signal == 'AllForNow':
                '''
                <signal name="AllForNow"/>
                '''
                logging.debug('AllForNow ignored')
            elif signal == 'CacheExhausted':
                '''
                <signal name="CacheExhausted"/>
                '''
                logging.debug('CacheExhausted ignored')
            else:
                logging.debug("ignoring signal signal %s'", signal)
            
        def bus_get_callback(self, source_object, res, user_data):
            self.systemDBusConnection = Gio.bus_get_finish(res)
            
            # Subscribe to the DBUS signal 'ItemNew' that is sent by Avahi Service Browser Objects to signal new services becoming available.
            # Also subscribe to the 'AllForNow' signal that used to signal that nothing more is availbale.
            # I need do this at this point because when I call the Avahi Server proxy object's ServiceBrowserNew method the new remote object
            # will immediately send an 'ItemNew' signal for each service that is currently available. followed by a single 'AllForNow' signal.
            # These signals often arrive before the local DBusProxy object has completed its initialisation and I have had a chance to use its
            # connect method to hook up to its rebroadcast of DBUS signals on the GObject signalling system.
            # I will unsubscribe these signals as soon as GObject signal has been successfully hooked up
            self.ItemNewId = self.systemDBusConnection.signal_subscribe(None, 'org.freedesktop.Avahi.ServiceBrowser', 'ItemNew', None, 
                                                        None, 0, self.dbus_signal_callback, None)
            self.AllForNowId = self.systemDBusConnection.signal_subscribe(None, 'org.freedesktop.Avahi.ServiceBrowser', 'AllForNow', None, 
                                                        None, 0, self.dbus_signal_callback, None)
            
            # Request a proxy for an Avahi DBUS_INTERFACE_SERVER object
            Gio.DBusProxy.new(self.systemDBusConnection, 0, NodeInfoForServer.lookup_interface(avahi.DBUS_INTERFACE_SERVER),
                                                avahi.DBUS_NAME,
                                                avahi.DBUS_PATH_SERVER,
                                                avahi.DBUS_INTERFACE_SERVER, None,
                                                self.new_server_proxy_callback, None)
                                                
        def dbus_signal_callback(self, connection, sender_name, object_path, interface_name, signal_name, arguments, user_data):
            if (signal_name == 'ItemNew') or (signal_name == 'AllForNow'):
                # Pass the signal on to my GObject signal handler
                self.browserCallback(None, sender_name, signal_name, arguments)
            else:
                logging.debug('Should never see this')
                Application.release()
                                                
        def new_browser_proxy_callback(self, source_object, res, user_data):
            self.avahibrowser = Gio.DBusProxy.new_finish(res)
            self.avahibrowser.connect('g-signal', self.browserCallback)
            self.systemDBusConnection.signal_unsubscribe(self.ItemNewId)
            self.systemDBusConnection.signal_unsubscribe(self.AllForNowId)
                   
        def new_server_proxy_callback(self, source_object, res, user_data):
            self.avahiserver = Gio.DBusProxy.new_finish(res)        
            avahibrowserpath = self.avahiserver.ServiceBrowserNew('(iissu)',
                                    avahi.IF_UNSPEC,
                                    avahi.PROTO_INET,
                                    '_scratch._tcp',
                                    'local',
                                    0)
            
            Gio.DBusProxy.new(self.systemDBusConnection, 0, NodeInfoForServiceBrowser.lookup_interface(avahi.DBUS_INTERFACE_SERVICE_BROWSER),
                                                avahi.DBUS_NAME,
                                                avahibrowserpath,
                                                avahi.DBUS_INTERFACE_SERVICE_BROWSER, None,
                                                self.new_browser_proxy_callback, None)
        
        def quit_cb(self, *args):
            logging.debug('Shutting down')
            logging.shutdown()

        ###############################################################################################################
        # Methods            
        ###############################################################################################################
        
        def create_new_thumbnail(self, avahiDomain, avahiName, hostname, address, portnumber):
            # If this is a new host then create thumbnail
            # For the time being this means I will ignore calls for multiple ports on the same host
            if not (avahiDomain, avahiName) in self.avahiToThumbnailMap:
                # Create a new thumbnail window for a remote scratch host
                self.avahiToThumbnailMap[(avahiDomain, avahiName)] = self.MatrixDisplay(hostname, address, portnumber, self.builder.get_object('unicormEmuRemoteDisplayBox'))
                logging.debug("Thumbnail map after add '%s'", self.avahiToThumbnailMap)
                
        def destroy_thumbnail(self, avahiDomain, avahiName):
            logging.debug("Thumbnail map before delete'%s'", self.avahiToThumbnailMap)
            matrixDisplay = self.avahiToThumbnailMap[(avahiDomain, avahiName)]
            matrixDisplay.frame.destroy()
            del self.avahiToThumbnailMap[(avahiDomain, avahiName)] # I am hoping that this detroys the MatrixDisplay object

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
        parser.add_argument('-a', '--avahi', nargs='?', const=True, default=False,
                   help='Enable avahi support')

        args = parser.parse_args()
        self.hostname = args.hostname
        self.avahiSupport = args.avahi
                        
        Gtk.Application.__init__(self, application_id=application_id, flags=flags)
        
        # Hook up the activate signal
        self.connect('activate', self.activate_callback)
        
        # Initialise logging
        logging.basicConfig(filename='unicornemu.log', level=logging.DEBUG, filemode='w', \
                             format=logFormat)
                             
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        if args.verbose:
            formatter = logging.Formatter(logFormat)
            console.setFormatter(formatter)
            logging.getLogger('').addHandler(console)
                             
        logging.debug('Loading resources')
        
        # Load resources
        try:
            resources = Gio.Resource.load(os.path.join('/usr/share/unicornemu', 'unicornemu.gresource'))
        except GLib.Error:
            resources = Gio.Resource.load(os.path.join(os.getcwd(), 'resources/unicornemu.gresource'))
            
        Gio.resources_register(resources)

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
    # Initialize GTK Application
    Application = UnicornEmu("uk.co.beardandsandals.unicornemu", Gio.ApplicationFlags.FLAGS_NONE)

    # Start GUI
    Application.run(None)

if __name__ == "__main__":
    # For backwards compatibity
    GObject.threads_init()
    
    # Initialize the GTK application
    main()
    
