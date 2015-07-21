#!/usr/bin/env python
from gi.repository import Gio, GLib, GObject, Gtk
import avahi

class avahibrowser(Gio.Application):
    
    def myhandler(interface, protocol, name, stype, domain, flags):
        print "Found service '%s' type '%s' domain '%s' " % (name, stype, domain)

        avahiserver.ResolveService(interface, protocol, name, stype, 
            domain, avahi.PROTO_UNSPEC, dbus.UInt32(0), 
            reply_handler=service_resolved, error_handler=print_error)

    def cb(proxy, sender, signal, args):
        ignore = proxy
        ignore = sender
        print 'ping', signal, args

    def do_activate(self):
        print 'Activated'
            
    def do_run_mainloop(self):
        print 'Running'
        
        
    # Gnome application initialization routine
    def __init__(self, application_id, flags):
        
        print 'Got to here'
        
        Gio.Application.__init__(self, application_id=application_id, flags=flags)
        print 'Got to here'
        '''
        dbus = None
        avahiserver = None

        browser_sigs = []


        self.systemDBusConnection = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)

        self.avahiserver = Gio.DBusProxy.new_sync(self.systemDBusConnection, 0, None,
                                            avahi.DBUS_NAME,
                                            avahi.DBUS_PATH_SERVER,
                                            avahi.DBUS_INTERFACE_SERVER, None)
                                
        avahibrowserpath = self.avahiserver.ServiceBrowserNew('(iissu)',
                                avahi.IF_UNSPEC,
                                avahi.PROTO_INET,
                                '_scratch._tcp',
                                'local',
                                0)
                                
        self.avahibrowser = Gio.DBusProxy.new_sync(self.systemDBusConnection, 0, None,
                                            avahi.DBUS_NAME,
                                            avahibrowserpath,
                                            avahi.DBUS_INTERFACE_SERVICE_BROWSER,
                                            None)
                                            
        self.avahibrowser.connect("g-signal", self.cb)
        '''
        print 'finished the init'


if __name__ == "__main__":
    # For backwards compatibity
    GObject.threads_init()
    Application = avahibrowser("uk.co.beardandsandals.avahibrowser", Gio.ApplicationFlags.FLAGS_NONE)
    print ' Contructed the app object'
    Application.run(None)
    print 'Fallen  off the bottom'




'''
import dbus, gobject, avahi
from dbus import DBusException
from dbus.mainloop.glib import DBusGMainLoop

TYPE = '_scratch._tcp'

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
'''
