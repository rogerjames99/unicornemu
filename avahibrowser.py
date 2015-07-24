#!/usr/bin/env python
from gi.repository import Gio, GLib, GObject, Gtk
import avahi
import signal
import time

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

# Use Gio.Application as a parent to avoid using involving all the GTk+ GUI stuff
class avahibrowser(Gio.Application):
    
    def do_activate(self):  # Define this to suppress glib warning
        pass
        
    def service_resolved(self, *args):
        print 'service resolved'
        print 'name:', args[2]
        print 'address:', args[7]
        print 'port:', args[8]

    def print_error(self, *args):
        print 'error_handler'
        print args[0]
        
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
        
    def new_browser_proxy_callback(self, source_object, res, user_data):
        self.avahibrowser = Gio.DBusProxy.new_finish(res)
        self.avahibrowser.connect('g-signal', self.browserCallback)
        
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
    
    def dbus_signal_callback(self, connection, sender_name, object_path, interface_name, signal_name, arguments, user_data):
        if (signal_name == 'ItemNew') or (signal_name == 'AllForNow'):
            # Pass the signal on to my GObject signal handler
            self.browserCallback(None, sender_name, signal_name, arguments)
        else:
            print 'Should never see this'
            Application.release()

        
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
                                            
    # Gnome application initialization routine
    def __init__(self, application_id, flags):
        Gio.Application.__init__(self, application_id=application_id, flags=flags)
        
        # Start the process of connecting to Avahi
        Gio.bus_get(Gio.BusType.SYSTEM, None, self.bus_get_callback, None)
        
def InitSignal(app):
    # This the hacky stuff I have to do properly handle unix signals in the GObject world
    def signal_action(signal):
        app.release()

    def idle_handler(*args):
        print("Python signal handler activated.")
        GLib.idle_add(signal_action, priority=GLib.PRIORITY_HIGH)

    def handler(*args):
        signal_action(args[0])

    def install_glib_handler(sig):
        unix_signal_add = None

        if hasattr(GLib, "unix_signal_add"):
            unix_signal_add = GLib.unix_signal_add
        elif hasattr(GLib, "unix_signal_add_full"):
            unix_signal_add = GLib.unix_signal_add_full

        if unix_signal_add:
            unix_signal_add(GLib.PRIORITY_HIGH, sig, handler, sig)
        else:
            print("Can't install GLib signal handler, too old gi.")

    SIGS = [getattr(signal, s, None) for s in "SIGINT SIGTERM SIGHUP".split()]
    for sig in filter(None, SIGS):
        signal.signal(sig, idle_handler)
        GLib.idle_add(install_glib_handler, sig, priority=GLib.PRIORITY_HIGH)

if __name__ == "__main__":
    Application = avahibrowser("uk.co.beardandsandals.avahibrowser", Gio.ApplicationFlags.FLAGS_NONE)
    
    # Set up python and Gio signal handling
    InitSignal(Application)
    
    Application.hold()

    Application.run(None)
    
    print 'Goodbye'
