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
# TODO : remove
import time

class TeleinfoTestCase(PluginTestCase):

    def test_0100_dummy(self):
        self.assertTrue(True)

    def test_0100_hphc(self):
        """ Test if the teleinfo.basic schema is sent when a frame is received
        """
        global interval
        global device
        global device_id

        # do the test
        print(u"Check that a MQ message for the frame received is sent.")
        
        data = {"adco" : "030928084432",
                "optarif" : "hc..",
                "isousc" : "45",
                "hchc" : "024073045",
                "hchp" : "030297217",
                "ptec" : "hp..",
                "iinst" : "001",
                "imax" : "048",
                "papp" : "00300",
                "hhphc" : "d",
                "motdetat" : "000000"}
        self.assertTrue(self.wait_for_mq( device_id = device_id,
                                          data = data,
                                          timeout = interval * 60))
        time.sleep(1)
        print(u"Check that the values of the MQ message has been inserted in database")
        sensor = TestSensor(device_id, "adco")
        self.assertTrue(sensor.get_last_value()[1] == data['adco'])
        sensor = TestSensor(device_id, "optarif")
        self.assertTrue(sensor.get_last_value()[1] == data['optarif'])
        sensor = TestSensor(device_id, "isousc")
        self.assertTrue(sensor.get_last_value()[1] == data['isousc'])
        sensor = TestSensor(device_id, "hchc")
        self.assertTrue(sensor.get_last_value()[1] == data['hchc'])
        sensor = TestSensor(device_id, "hchp")
        self.assertTrue(sensor.get_last_value()[1] == data['hchp'])
        sensor = TestSensor(device_id, "ptec")
        self.assertTrue(sensor.get_last_value()[1] == data['ptec'])
        sensor = TestSensor(device_id, "iinst")
        self.assertTrue(sensor.get_last_value()[1] == data['iinst'])
        sensor = TestSensor(device_id, "imax")
        self.assertTrue(sensor.get_last_value()[1] == data['imax'])
        sensor = TestSensor(device_id, "papp")
        self.assertTrue(sensor.get_last_value()[1] == data['papp'])
        sensor = TestSensor(device_id, "hhphc")
        self.assertTrue(sensor.get_last_value()[1] == data['hhphc'])
        sensor = TestSensor(device_id, "motdetat")
        self.assertTrue(sensor.get_last_value()[1] == data['motdetat'])


if __name__ == "__main__":

    test_folder = os.path.dirname(os.path.realpath(__file__))

    ### global variables
    device = "/dev/teleinfo"
    interval = 1

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

    # specific configuration for test mdode (handled by the manager for plugin startup)
    cfg['test_mode'] = True
    cfg['test_option'] = "{0}/tests_hphc_data.json".format(test_folder)

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
        device_id = td.create_device(params)['id']

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
    suite.addTest(TeleinfoTestCase("test_0100_hphc", xpl_plugin, name, cfg))

    # do some tests comon to all the plugins
    #suite.addTest(TeleinfoTestCase("test_9900_hbeat", xpl_plugin, name, cfg))
    suite.addTest(TeleinfoTestCase("test_9990_stop_the_plugin", xpl_plugin, name, cfg))

    # quit
    res = unittest.TextTestRunner().run(suite)
    if res.wasSuccessful() == True:
        rc = 0   # tests are ok so the shell return code is 0
    else:
        rc = 1   # tests are ok so the shell return code is != 0
    xpl_plugin.force_leave(return_code = rc)


