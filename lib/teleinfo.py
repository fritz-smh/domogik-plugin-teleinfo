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
import serial
import time   


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
    """

    def __init__(self, log, callback, stop, device, interval):
        """ Init Disk object
            @param log : log instance
            @param callback : callback
            @param stop : stop flag
            @param device : teleinformation device
            @param interval : interval in seconds between each read on the device
        """
        self.log = log
        self._callback = callback
        self._stop = stop
        self._device = device
        self._interval = interval

    def open(self):
        """ Try to open the teleinfo device
        """
        try:
            self.log.info("Try to open {0}".format(self._device))
            self._ser = serial.Serial(self._device, 1200, bytesize=7, 
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
        """
        #Get the begin of the frame, marked by \x02
        resp = self._ser.readline()
        is_ok = False
        frame = []
        while not is_ok:
            try:
                while '\x02' not in resp:
                    resp = self._ser.readline()
                #\x02 is in the last line of a frame, so go until the next one
                self.log.debug("New frame :")
                resp = self._ser.readline()
                #A new frame starts
                #\x03 is the end of the frame
                while '\x03' not in resp:
                    #Don't use strip() here because the checksum can be ' '
                    if len(resp.replace('\r','').replace('\n','').split()) == 2:
                        #The checksum char is ' '
                        name, value = resp.replace('\r','').replace('\n','').split()
                        checksum = ' '
                    else:
                        name, value, checksum = resp.replace('\r','').replace('\n','').split()
                        self.log.debug("- name : {0}, value : {1}, checksum : {2}".format(name, value, checksum))
                    if self._is_valid(resp, checksum):
                        frame.append({"name" : name, "value" : value, "checksum" : checksum})
                    else:
                        self.log.warning("Frame corrupted, waiting for a new one...")
                        #This frame is corrupted, we need to wait until the next one
                        frame = []
                        while '\x02' not in resp:
                            resp = self._ser.readline()
                        self.log.debug("New frame detected after the corrupted one.")
                    resp = self._ser.readline()
                #\x03 has been detected, that's the last line of the frame
                if len(resp.replace('\r','').replace('\n','').split()) == 2:
                    #self.log.debug("* End frame")
                    #The checksum char is ' '
                    name, value = resp.replace('\r','').replace('\n','').replace('\x02','').replace('\x03','').split()
                    checksum = ' '
                else:
                    name, value, checksum = resp.replace('\r','').replace('\n','').replace('\x02','').replace('\x03','').split()
                if self._is_valid(resp, checksum):
                    frame.append({"name" : name, "value" : value, "checksum" : checksum})
                    #self.log.debug("* End frame, is valid : {0}".format(frame))
                    is_ok = True
                else:
                    self.log.warning("Last frame is invalid")
                    resp = self._ser.readline()
            except ValueError:
                #Badly formatted frame
                #This frame is corrupted, we need to wait until the next one
                frame = []
                while '\x02' not in resp:
                    resp = self._ser.readline()
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

