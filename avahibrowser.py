#!/usr/bin/env python
from gi.repository import Gio, GLib, GObject, Gtk
import avahi
import signal

class avahibrowser(Gio.Application):
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
            print "Found service '%s' type '%s' domain '%s' " % (args[2], args[3], args[4])
            #self.avahiserver.ResolveService('iisssiu',     
            #    args[0], # Interface
            #    args[1], # Protocol
            #    args[2], # Name
            #    args[3], # Service Type 
            #    args[4], # Domain
            #    avahi.PROTO_UNSPEC, dbus.UInt32(0), 
            #    reply_handler=self.service_resolved, error_handler=self.print_error)
        else:
            print 'signal', signal, 'arguments', args
        
    def do_activate(self):
        print 'Activated'

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
                                            
        self.avahibrowser.connect('g-signal', self.browserCallback)
                    
    # Gnome application initialization routine
    def __init__(self, application_id, flags):
        Gio.Application.__init__(self, application_id=application_id, flags=flags)

if __name__ == "__main__":
    # For backwards compatibity
    GObject.threads_init()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Application = avahibrowser("uk.co.beardandsandals.avahibrowser", Gio.ApplicationFlags.FLAGS_NONE)
    Application.hold()
    Application.run(None)
