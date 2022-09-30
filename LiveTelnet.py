"""
# Copyright (C) 2007 Rob King (rob@e-mu.org)
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# For questions regarding this module contact
# Rob King <rob@e-mu.org> or visit http://www.e-mu.org
#

LiveTelnet is a very simple telnet server that works in the version of Python
included in Ableton Live.  To install, first make sure you have installed
Python 2.2.x in c:\Python22 (we use some of it's modules which are not included
in Ableton's version).  Next place all this directory inside the  MIDI Remote
Scripts directory of Ableton:
e.g. C:\Program Files\Ableton\Live 6.0.7\Resources\MIDI Remote Scripts
When you load up Ableton you should find the LiveAPI control surface listed
in Preferences > MIDI/Sync, select it.
Now you can use the telnet client of your choice to telnet to localhost port 23
where you will get an Interactive Python interpreter.
To get started quickly take a look in LiveUtils.py

"""

import Live
from io import StringIO
import socket, code
from . import LiveUtils

class LiveTelnet:
    __module__ = __name__
    __doc__ = "Main class that establishes the Live Telnet"

    def __init__(self, c_instance):
        self._LiveTelnet__c_instance = c_instance
        self.originalstdin = sys.stdin
        self.originalstdout = sys.stdout
        self.originalstderr = sys.stderr

        self.stdin = StringIO()
        self.stdout = StringIO()
        self.stderr = StringIO()

        self.telnetSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.telnetSocket.bind( ('', 23) )
        self.telnetSocket.setblocking(False)
        self.telnetSocket.listen(1)
        self.telnetConnection = None

        self.interpreter = code.InteractiveConsole(globals())

        self.telnetBuffer = ""
        self.lastData = ""
        self.commandBuffer = []

    def disconnect(self):

        #Be nice and return stdio to their original owners
        sys.stdin = self.originalstdin
        sys.stdout = self.originalstdout
        sys.stderr = self.originalstderr
        self.telnetSocket.close()

    def connect_script_instances(self, instanciated_scripts):
        """
        Called by the Application as soon as all scripts are initialized.
        You can connect yourself to other running scripts here, as we do it
        connect the extension modules
        """
        return

    def application(self):
        """returns a reference to the application that we are running in"""
        return Live.Application.get_application()

    def song(self):
        """returns a reference to the Live Song that we do interact with"""
        return self._LiveTelnet__c_instance.song()

    def handle(self):
        """returns a handle to the c_interface that is needed when forwarding MIDI events via the MIDI map"""
        return self._LiveTelnet__c_instance.handle()

    def refresh_state(self):
        """I'm sure this does something useful.."""
        return

    def is_extension(self):
        return False

    def request_rebuild_midi_map(self):
        """
        To be called from any components, as soon as their internal state changed in a
        way, that we do need to remap the mappings that are processed directly by the
        Live engine.
        Dont assume that the request will immediately result in a call to
        your build_midi_map function. For performance reasons this is only
        called once per GUI frame.
        """
        return

    def build_midi_map(self, midi_map_handle):
        """
        New MIDI mappings can only be set when the scripts 'build_midi_map' function
        is invoked by our C instance sibling. Its either invoked when we have requested it
        (see 'request_rebuild_midi_map' above) or when due to a change in Lives internal state,
        a rebuild is needed.
        """
        return

    def send(self, message):
        self.telnetConnection.send(message.encode())

    def update_display(self):
        #Updates every 100ms

        #Keep trying to accept a connection until someone actually connects
        if not self.telnetConnection:
            try:
                #Does anyone want to connect?
                self.telnetConnection, self.addr = self.telnetSocket.accept()
            except:
                #No one connected in this iteration
                pass
            else:
                #Yay! Someone connected! Send them the banner and first prompt.
                self.send("Welcome to the Ableton Live Python Interpreter (Python 2.2.1)\r\n")
                self.send("Brought to by LiveAPI.org\r\n")
                self.send(">>> ")
        else:
            #Someone's connected, so lets interact with them.
            try:
                #If the client has typed anything, get it
                data = self.telnetConnection.recv(1).decode()
            except:
                #Nope they haven't typed anything yet
                data = "" #

            #If return is pressed, process the command (This if statement is so ugly because ableton python doesn't have universal newlines)
            if (data == "\n" or data == "\r") and (self.lastData != "\n" and self.lastData != "\r"):
                continues = self.interpreter.push(self.telnetBuffer.rstrip()) #should be strip("/r/n") but ableton python throws an error
                self.commandBuffer.append(self.telnetBuffer.rstrip())
                self.telnetBuffer = ""

                #if the user input is multi-line, continue, otherwise return the results

                if continues:
                    self.send("... ")
                else:
                    #return stdout to the client
                    self.send(self.stdout.getvalue().replace("\n","\r\n"))
                    #return stderr to the client
                    self.send(self.stderr.getvalue().replace("\n","\r\n"))
                    self.send(">>> ")

                #Empty buffers by creating new stringIO objects
                #There's probably a better way to empty these
                self.stdin.close()
                self.stdout.close()
                self.stderr.close()
                self.stdin = StringIO()
                self.stdout = StringIO()
                self.stderr = StringIO()
                #re-redirect the stdio
                sys.stdin = self.stdin
                sys.stdout = self.stdout
                sys.stderr = self.stderr


            elif data == "\b": #deals with backspaces
                if len(self.telnetBuffer):
                    self.telnetBuffer = self.telnetBuffer[:-1]
                    self.send(" \b") #deletes the character on the console
                else:
                    self.send(" ")
            elif data != "\n" and data != "\r":
                self.telnetBuffer = self.telnetBuffer + data
            self.lastData = data

    def send_midi(self, midi_event_bytes):
        """
        Use this function to send MIDI events through Live to the _real_ MIDI devices
        that this script is assigned to.
        """
        pass

    def receive_midi(self, midi_bytes):
        return

    def can_lock_to_devices(self):
        return False

    def suggest_input_port(self):
        return ''

    def suggest_output_port(self):
        return ''

    def suggest_map_mode(self, cc_no):
        result = Live.MidiMap.MapMode.absolute
        if (cc_no in range(FID_PANNING_BASE, (FID_PANNING_BASE + NUM_CHANNEL_STRIPS))):
            result = Live.MidiMap.MapMode.relative_signed_bit
        return result

    def __handle_display_switch_ids(self, switch_id, value):
        pass