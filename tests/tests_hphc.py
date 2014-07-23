#!/usr/bin/python
# -*- coding: utf-8 -*-

from domogik.xpl.common.plugin import XplPlugin
from domogik.tests.common.plugintestcase import PluginTestCase
from domogik.tests.common.testplugin import TestPlugin
from domogik.tests.common.testdevice import TestDevice
from domogik.tests.common.testsensor import TestSensor
from domogik.common.utils import get_sanitized_hostname
from datetime import datetime
import unittest
import sys
import os
import traceback

class TeleinfoTestCase(PluginTestCase):

    def test_0100_dummy(self):
        self.assertTrue(True)

if __name__ == "__main__":
    ### global variables
    device = "/dev/teleinfo"
    interval = 60

    # set up the xpl features
    xpl_plugin = XplPlugin(name = 'test',
                           daemonize = False,
                           parser = None,
                           nohub = True,
                           test  = True)

    # set up the plugin name
    name = "teleinfo"

    # set up the configuration of the plugin
    # configuration is done in test_0010_configure_the_plugin with the cfg content
    # notice that the old configuration is deleted before
    cfg = { 'configured' : True }

    ### start tests
    # load the test devices class
    td = TestDevice()

    # delete existing devices for this plugin on this host
    client_id = "{0}-{1}.{2}".format("plugin", name, get_sanitized_hostname())
    try:
        td.del_devices_by_client(client_id)
    except:
        print(u"Error while deleting all the test device for the client id '{0}' : {1}".format(client_id, traceback.format_exc()))
        sys.exit(1)

    # create a test device
    try:
        #device_id = td.create_device(client_id, "test_device_teleinfo", "teleinfo.electric_meter")
        
        params = td.get_params(client_id, "teleinfo.electric_meter")
    
        # fill in the params
        params["device_type"] = "teleinfo.electric_meter"
        params["name"] = "test_device_teleinfo"
        params["reference"] = "reference"
        params["description"] = "description"
        # global params
        for the_param in params['global']:
            if the_param['key'] == "interval":
                the_param['value'] = interval
            if the_param['key'] == "device":
                the_param['value'] = device
        print params['global']
        # xpl params
        pass # there are no xpl params for this plugin
        # create
        td.create_device(params)

    except:
        print(u"Error while creating the test devices : {0}".format(traceback.format_exc()))
        sys.exit(1)

    ### prepare and run the test suite
    suite = unittest.TestSuite()
    # check domogik is running, configure the plugin
    suite.addTest(TeleinfoTestCase("test_0001_domogik_is_running", xpl_plugin, name, cfg))
    suite.addTest(TeleinfoTestCase("test_0010_configure_the_plugin", xpl_plugin, name, cfg))

    # start the plugin
    suite.addTest(TeleinfoTestCase("test_0050_start_the_plugin", xpl_plugin, name, cfg))


    # do the specific plugin tests
    suite.addTest(TeleinfoTestCase("test_0100_dummy", xpl_plugin, name, cfg))

    # do some tests comon to all the plugins
    suite.addTest(TeleinfoTestCase("test_9900_hbeat", xpl_plugin, name, cfg))
    suite.addTest(TeleinfoTestCase("test_9990_stop_the_plugin", xpl_plugin, name, cfg))

    # quit
    res = unittest.TextTestRunner().run(suite)
    if res.wasSuccessful() == True:
        rc = 0   # tests are ok so the shell return code is 0
    else:
        rc = 1   # tests are ok so the shell return code is != 0
    xpl_plugin.force_leave(return_code = rc)


