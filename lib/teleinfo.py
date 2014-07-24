# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

Teleinfo 

Implements
==========

- Teleinfo

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2014 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os
import traceback
import serial as serial
import domogik.tests.common.testserial as testserial


class TeleinfoException(Exception):
    """
    Teleinfo exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class Teleinfo:
    """ Teleinfo
        Frame format information in the read() function description
    """

    def __init__(self, log, callback, stop, device, interval, fake_device):
        """ Init Teleinfo object
            @param log : log instance
            @param callback : callback
            @param stop : stop flag
            @param device : teleinformation device
            @param interval : interval in seconds between each read on the device
            @param fake_device : fake device. If None, this will not be used. Else, the fake serial device library will be used
        """
        self.log = log
        self._callback = callback
        self._stop = stop
        self._device = device
        self._fake_device = fake_device
        self._interval = interval

    def open(self):
        """ Try to open the teleinfo device
        """
        try:
            self.log.info("Try to open {0}".format(self._device))
            if self._fake_device != None:
                self._ser = testserial.Serial(self._fake_device, baudrate=1200, bytesize=7, 
                                          parity = 'E',stopbits=1)
            else:
                self._ser = serial.Serial(self._device, baudrate=1200, bytesize=7, 
                                          parity = 'E',stopbits=1)

            self.log.info("Teleinfo modem successfully opened")
        except:
            error = "Error opening Teleinfo modem '{0}' : {1} ".format(self._device, traceback.format_exc())
            self.log.error(error)
            raise TeleinfoException(error)

    def listen(self):
        """ Listen to the teleinfo device
        """
        try:
            while not self._stop.isSet():
                frame = self.read()
                #self.log.debug("Frame received : {0}".format(frame))
                self._callback(frame)
                #print(frame)
                self._stop.wait(self._interval)
        except serial.SerialException as e:
            if self._stop.isSet():
                pass
            else:
                raise e

    def close(self):
        """ Close the teleinfo device
        """
        self._stop.set()
        if self._ser.isOpen():
            self._ser.close()

    def read(self):
        """ Fetch one full frame for serial port
            If some part of the frame is corrupted,
            it waits until the next one, so if you have corruption issue,
            this method can take time but it ensures that the frame returned is valid
            @return frame : list of dict {name, value, checksum}

            Information about a frame :
            * it starts with \x02
            * there are several groups in a frame : \n<name> <value> <checksum>\r. Example : \nHCHP 030297217 2\r
            * it ends with \x02
        """
        self.log.debug("AVANT READ")
        # first read
        resp = self._ser.readline()
        self.log.debug("READ : {0}".format(resp))
        is_ok = False
        frame = []
        while not is_ok:
            self.log.debug("WHILE.....")
            try:
                # wait for the start of a new frame (\x02)
                while '\x02' not in resp:
                    resp = self._ser.readline()
                    self.log.debug("READ : {0}".format(resp))
                #\x02 is the start of a frame, so do a loop until we reach the end of the frame
                self.log.debug("New frame :")
                # first read
                resp = self._ser.readline()
                self.log.debug("READ : {0}".format(resp))
                #A new frame starts
                #\x03 is the end of the frame
                # until the end, process the groups in the frame
                error = False
                while '\x03' not in resp:
                    # process the frame content (the groups)
                    #Don't use strip() here because the checksum can be ' '
                    if len(resp.replace('\r','').replace('\n','').split()) == 2:
                        #The checksum char is ' '
                        # TODO : check that "PTEC HP..  " is handler by this code
                        name, value = resp.replace('\r','').replace('\n','').split()
                        checksum = ' '
                        self.log.debug("- name : {0}, value : {1}, checksum : ' '".format(name, value, checksum))
                    else:
                        name, value, checksum = resp.replace('\r','').replace('\n','').split()
                        self.log.debug("- name : {0}, value : {1}, checksum : {2}".format(name, value, checksum))

                    # check if the group is valid
                    if self._is_valid(resp, checksum):
                        frame.append({"name" : name, "value" : value, "checksum" : checksum})
                    else:
                        error = True
                        self.log.warning("Frame corrupted, waiting for a new one...")
                        break

                        # TODO : delete
                        ##This frame is corrupted, we need to wait until the next one
                        #frame = []
                        #while '\x02' not in resp:
                        #    resp = self._ser.readline()
                        #    self.log.debug("READ : {0}".format(resp))
                        #self.log.debug("New frame detected after the corrupted one.")

                    # wait for the next group in the frame
                    resp = self._ser.readline()
                    self.log.debug("READ : {0}".format(resp))
                #\x03 has been detected, that's the last line of the frame
                #if len(resp.replace('\r','').replace('\n','').split()) == 2:

                # TODO : how to handle in a better way the last group ?
                # => change the way we handle the while()
                self.log.warning("DEVELOPMENT IN PROGRESS : last group missing in the frame")
                if not error:
                    self.log.debug("* End frame")
                    is_ok = True
                #    #The checksum char is ' '
                #    name, value = resp.replace('\r','').replace('\n','').replace('\x02','').replace('\x03','').split()
                #    checksum = ' '
                #else:
                #    buf_data = resp.replace('\r','').replace('\n','').replace('\x02','').replace('\x03','')
                #    if len(buf_data) > 0:
                #        name, value, checksum = buf_data.split()
                #    else: 
                #        name = None
                #if name and self._is_valid(resp, checksum):
                #    frame.append({"name" : name, "value" : value, "checksum" : checksum})
                #    self.log.debug("* End frame, is valid : {0}".format(frame))
                #    is_ok = True
                #elif name is None:
                #    pass
                #else:
                #    self.log.warning("Last frame is invalid")
                #    resp = self._ser.readline()
                #    self.log.debug("READ : {0}".format(resp))
            except ValueError:
                self.log.debug(traceback.format_exc())
                #Badly formatted frame
                #This frame is corrupted, we need to wait until the next one
                frame = []
                #while '\x02' not in resp:
                #    resp = self._ser.readline()
                #    self.log.debug("READ except : {0}".format(resp))
                break;
        return frame

    def _is_valid(self, frame, checksum):
        """ Check if a frame is valid
            @param frame : the full frame
            @param checksum : the frame checksum
        """
        #self.log.debug("Check checksum : f = {0}, chk = {1}".format(frame, checksum))
        datas = ' '.join(frame.split()[0:2])
        my_sum = 0
        for cks in datas:
            my_sum = my_sum + ord(cks)
        computed_checksum = ( my_sum & int("111111", 2) ) + 0x20
        #self.log.debug("computed_checksum = {0}".format(chr(computed_checksum)))
        if chr(computed_checksum) == checksum:
            return True
        else:
            self.log.warning("Invalid checksum for '{0}' : checksum is {1}. Waiting checksum was {2}".format(frame, computed_checksum, checksum))
            return False

