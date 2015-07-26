#!/usr/bin/env python

import logging
import argparse
import os
from gi.repository import Gtk, GLib, Gio, GObject, DBus
import cairo
import numpy as np
import random
import threading
import time
import struct
import avahi
import avahi
import socket

AvahiSupport = False

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
 
    class Window(object):
        
        ###############################################################################################################
        # Initialisation
        ###############################################################################################################
 
        def __init__(self, application, *args):
            # Constants
            self.imageSize = 1000

            
            # Set up the gui                     
            self.builder = Gtk.Builder()
            try:
                self.builder.add_from_file(os.path.join('/usr/share/unicornemu', 'unicornemu.ui'))
            except GLib.Error:
                self.builder.add_from_file(os.path.join(os.getcwd(), 'unicornemu.ui'))
                
            self.builder.connect_signals(self)
            self.mainWindow = self.builder.get_object('unicornemuApplicationWindow')
            self.mainWindow.set_application(application)
            if application.hostname == 'localhost':
                # Get real hostname
                title = socket.gethostname()
            else:
                title = application.hostname
            self.builder.get_object('unicornemuMainMatrixLabel').set_text(title)
            self.mainWindow.show()
            
            # Use cairo to do the matrix stuff
            self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.imageSize, self.imageSize)
                    
            self.scratch = SocketThread(application.hostname, 42001, self.surface, self.builder.get_object('drawingArea'))
        
        ###############################################################################################################
        # Callbacks                
        ###############################################################################################################
        
        def quit_cb(self, *args):
            logging.debug('Shutting down')
            self.scratch.terminate()
            logging.shutdown()
            self.close()

        ###############################################################################################################
        # Methods            
        ###############################################################################################################
        
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
                             
        logging.debug('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        
        # Start the process of connecting to Avahi
        if self.avahiSupport:
            Gio.bus_get(Gio.BusType.SYSTEM, None, self.bus_get_callback, None)

        
    ###############################################################################################################
    # Callbacks                
    ###############################################################################################################
        
    def activate_callback(self, *args):
        self.Window(self, self.hostname)

    def browserCallback(self, proxy, sender, signal, args):
        if signal == 'ItemNew':
            '''
            ResolveService
                in i interface
                in i protocol
                in s name
                in s type
                in s domain
                in i aprotocol
                in u flags
                out i interface
                out i protocol
                out s name
                out s type
                out s domain
                out s host
                out i aprotocol
                out s address
                out q port
                out aay txt
                out u flags
            '''
            returns = self.avahiserver.ResolveService('(iisssiu)',
                    args[0], # Interface
                    args[1], # Protocol
                    args[2], # Name
                    args[3], # Service Type 
                    args[4], # Domain
                    avahi.PROTO_UNSPEC, # aprotocol 
                    0) # flags
            print "Found service - name '%s\ntype '%s\ndomain '%s'\nhost '%s'\naprotocol %d\nip-address '%s'\nport number #%d" \
                    % (returns[2], returns[3], returns[4], returns[5], returns[6], returns[7], returns[8])
        else:
            print 'signal', signal, 'arguments', args
        
    def bus_get_callback(self, source_object, res, user_data):
        self.systemDBusConnection = Gio.bus_get_finish(res)
        
        # Subscribe to the DBUS signal 'ItemNew' that is sent by Avahi Service Browser Objects to signal new services becoming available.
        # Also subscribe to the 'AllForNow' signal that used to signal that nothing more is availbale.
        # I need do this at this point because when I call the Avahi Server proxy object's ServiceBrowserNew method the new remote object
        # will immediately send an 'ItemNew' signal for each service that is currently available. followed by a single 'AllForNow' signal.
        # These signals often arrive before the local DBusProxy object has completed its initialisation and I have had a chane to use its
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
            print 'Should never see this'
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
    
        
    ###############################################################################################################
    # Methods            
    ###############################################################################################################
    
    # This class has no methods yet
    
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
    
