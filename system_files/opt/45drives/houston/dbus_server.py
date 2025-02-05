#!/usr/bin/env python3

import dbus
import dbus.service
import dbus.mainloop.glib
import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib


dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)


class DBusService(dbus.service.Object):
    def __init__(self, bus_name):
        bus_path = "/org/_45drives/Houston"
        dbus.service.Object.__init__(self, bus_name, bus_path)

    @dbus.service.signal("org._45drives.Houston", signature="s")
    def Message(self, message):
        """Signal that an event has occurred."""
        print(f"[D-Bus Signal Sent] {message}")

    @dbus.service.method("org._45drives.Houston", in_signature="s")
    def ForwardMessage(self, message):
        print(f"[forwarding message] {message}")
        self.Message(message)


bus = dbus.SystemBus()
bus_name = dbus.service.BusName("org._45drives.Houston", bus)
service = DBusService(bus_name)

loop = GLib.MainLoop()
loop.run()
