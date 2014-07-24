#!/usr/bin/python
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

- TeleinfoManager

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2014 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin

from domogik_packages.plugin_teleinfo.lib.teleinfo import Teleinfo, TeleinfoException
import threading
import traceback
import re


class TeleinfoManager(XplPlugin):
    """ Get teleinformation informations
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='teleinfo')

        # check if the plugin is configured. If not, this will stop the plugin and log an error
        #if not self.check_configured():
        #    return

        # get the devices list
        self.devices = self.get_device_list(quit_if_no_device = True)

        # create a Teleinfo for each device
        threads = {}
        teleinfo_list = {}
        idx = 0
        for a_device in self.devices:
            try:
                # global device parameters
                device = self.get_parameter(a_device, "device")
                interval = self.get_parameter(a_device, "interval")
                
                teleinfo_list[device] = Teleinfo(self.log, self.send_xpl, self.get_stop(), device, interval, self.options.test_option)
                teleinfo_list[device].open()

                # start the teleinfo thread
                self.log.info(u"Start monitoring teleinfo device '{0}'".format(device))
                thr_name = "{0}".format(device)
                threads[thr_name] = threading.Thread(None,
                                              teleinfo_list[device].listen,
                                              thr_name,
                                              (),
                                              {})
                threads[thr_name].start()
                self.register_thread(threads[thr_name])
                idx += 1

            except:
                self.log.error(traceback.format_exc())
                # we don't quit plugin if an error occured
                # a teleinfo device can be KO and the others be ok
                #self.force_leave()
                #return



        self.ready()
        self.log.info(u"Plugin ready :)")



    def send_xpl(self, frame):
        ''' Send a frame from teleinfo device to xpl
        @param frame : a dictionnary mapping teleinfo informations
        '''
        my_temp_message = XplMessage()
        my_temp_message.set_type("xpl-stat")
        if "ADIR1" in frame:
            my_temp_message.set_schema("teleinfo.short")
        else:
            my_temp_message.set_schema("teleinfo.basic")

        try:
            key = None
            val = None
            for entry in frame:
                key = re.sub('[^\w\.]','',entry["name"].lower())
                val = re.sub('[^\w\.]','',entry["value"].lower())
                my_temp_message.add_data({ key : val })
            my_temp_message.add_data({"device": "teleinfo"})
        except :
            self.log.error("Error while creating xpl message : {0} ; key : {1} ; val : {2}. Error is : {3}".format(my_temp_message, key, val, traceback.formar_exc()))

        try:
            self.myxpl.send(my_temp_message)
        except XplMessageError:
            #We ignore the message if some values are not correct because it can happen with teleinfo ...
            self.log.debug("Bad xpl message to send. This may happen due to some invalid teleinfo data. Xpl message is : {0}".format(str(my_temp_message)))
            pass

if __name__ == "__main__":
    teleinfo = TeleinfoManager()
