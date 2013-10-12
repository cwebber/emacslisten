#!/usr/bin/env python

# Copyright 2013 Christopher Allan Webber
#
# Emacslisten is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# Emacslisten is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Emacslisten.  If not, see <http://www.gnu.org/licenses/>.

# This incorporates components from the CMU Sphinx pythonsphinx and
# gstreamer tutorial:
#
## Copyright (c) 2008 Carnegie Mellon University.
##
## You may modify and redistribute this file under the same terms as
## the CMU Sphinx system.  See
## http://cmusphinx.sourceforge.net/html/LICENSE for more information.

import pygtk
pygtk.require('2.0')
import gtk

import gobject
import pygst
pygst.require('0.10')
gobject.threads_init()
import gst

import dbus
import dbus.service
import dbus.mainloop.glib

class ListenerDaemon(dbus.service.Object):
    """GStreamer/PocketSphinx Demo Application"""
    def __init__(self, conn, object_path="/org/dustycloud/EmacsListen/daemon"):
        """Initialize a ListenerDaemon object"""
        dbus.service.Object.__init__(self, conn, object_path)

        self.init_gui()
        self.init_gst()
        self.init_dbus()

    def init_gui(self):
        """Initialize the GUI components"""
        self.window = gtk.Window()
        self.window.connect("delete-event", gtk.main_quit)
        self.window.set_default_size(400,200)
        self.window.set_border_width(10)
        vbox = gtk.VBox()
        self.textbuf = gtk.TextBuffer()
        self.text = gtk.TextView(self.textbuf)
        self.text.set_wrap_mode(gtk.WRAP_WORD)
        vbox.pack_start(self.text)
        self.button = gtk.ToggleButton("Speak")
        self.button.connect('clicked', self.button_clicked)
        vbox.pack_start(self.button, False, False, 5)
        self.window.add(vbox)
        self.window.show_all()

    def init_gst(self):
        """Initialize the speech components"""
        self.pipeline = gst.parse_launch('pulsesrc ! audioconvert ! audioresample '
                                         + '! vader name=vad auto-threshold=true '
                                         + '! pocketsphinx name=asr ! fakesink')
        asr = self.pipeline.get_by_name('asr')
        asr.connect('partial_result', self.asr_partial_result)
        asr.connect('result', self.asr_result)
        asr.set_property('configured', True)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::application', self.application_message)

        self.pipeline.set_state(gst.STATE_PAUSED)

    def init_dbus(self):
        """
        Set ourselves up so we become a proper dbus object
        """
        pass

    def asr_partial_result(self, asr, text, uttid):
        """Forward partial result signals on the bus to the main thread."""
        struct = gst.Structure('partial_result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        asr.post_message(gst.message_new_application(asr, struct))

    def asr_result(self, asr, text, uttid):
        """Forward result signals on the bus to the main thread."""
        struct = gst.Structure('result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        asr.post_message(gst.message_new_application(asr, struct))

    def application_message(self, bus, msg):
        """Receive application messages from the bus."""
        msgtype = msg.structure.get_name()
        if msgtype == 'partial_result':
            self.partial_result(msg.structure['hyp'], msg.structure['uttid'])
        elif msgtype == 'result':
            self.final_result(msg.structure['hyp'], msg.structure['uttid'])
            self.pipeline.set_state(gst.STATE_PAUSED)
            self.button.set_active(False)

    @dbus.service.signal(dbus_interface="org.dustycloud.EmacsListen",
                         signature="su")
    def partial_result(self, hyp, uttid):
        """Delete any previous selection, insert text and select it."""
        # All this stuff appears as one single action
        self.textbuf.begin_user_action()
        self.textbuf.delete_selection(True, self.text.get_editable())
        self.textbuf.insert_at_cursor(hyp)
        ins = self.textbuf.get_insert()
        iter = self.textbuf.get_iter_at_mark(ins)
        iter.backward_chars(len(hyp))
        self.textbuf.move_mark(ins, iter)
        self.textbuf.end_user_action()

    @dbus.service.signal(dbus_interface="org.dustycloud.EmacsListen",
                         signature="su")
    def final_result(self, hyp, uttid):
        """Insert the final result."""
        # All this stuff appears as one single action
        self.textbuf.begin_user_action()
        self.textbuf.delete_selection(True, self.text.get_editable())
        self.textbuf.insert_at_cursor(hyp)
        self.textbuf.end_user_action()

    def button_clicked(self, button):
        """Handle button presses."""
        if button.get_active():
            button.set_label("Stop")
            self.pipeline.set_state(gst.STATE_PLAYING)
        else:
            button.set_label("Speak")
            vader = self.pipeline.get_by_name('vad')
            vader.set_property('silent', True)


if __name__ == "__main__":
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    session_bus = dbus.SessionBus()
    name = dbus.service.BusName('org.dustycloud.EmacsListen', session_bus)

    app = ListenerDaemon(session_bus)
    gtk.main()
