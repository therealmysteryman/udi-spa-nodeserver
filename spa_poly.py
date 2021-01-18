#!/usr/bin/env python3

"""
This is a NodeServer for Balboa Spa written by automationgeek (Jean-Francois Tremblay)
based on the NodeServer template for Polyglot v2 written in Python2/3 by Einstein.42 (James Milne) milne.james@gmail.com
"""

import polyinterface
import pybalboa
import hashlib
import asyncio
import time
import json
import sys
from copy import deepcopy

LOGGER = polyinterface.LOGGER
SERVERDATA = json.load(open('server.json'))
VERSION = SERVERDATA['credits'][0]['version']

def get_profile_info(logger):
    pvf = 'profile/version.txt'
    try:
        with open(pvf) as f:
            pv = f.read().replace('\n', '')
    except Exception as err:
        logger.error('get_profile_info: failed to read  file {0}: {1}'.format(pvf,err), exc_info=True)
        pv = 0
    f.close()
    return { 'version': pv }

class Controller(polyinterface.Controller):

    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'BalboaSpa'
        self.initialized = False
        self.queryON = False
        self.hb = 0
        self.host = ""
        
    def start(self):
        LOGGER.info('Started Balboa SPA for v2 NodeServer version %s', str(VERSION))
        self.setDriver('ST', 1)
        try:
            if 'host' in self.polyConfig['customParams']:
                self.host = self.polyConfig['customParams']['host']
            else:
                self.host = ""
            
            if self.host == "" :
                LOGGER.error('SPA Balboa requires host parameter to be specified in custom configuration.')
                return False
            else:
                self.check_profile()
                self.discover()

        except Exception as ex:
            LOGGER.error('Error starting Balboa NodeServer: %s', str(ex))
           
    def shortPoll(self):
        self.setDriver('ST', 1)
        self.reportDrivers()
        for node in self.nodes:
            if  self.nodes[node].queryON == True :
                self.nodes[node].query()

    def longPoll(self):
        self.heartbeat()
       
    def heartbeat(self):
        LOGGER.debug('heartbeat: hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def discover(self, *args, **kwargs):
        self.addNode(Spa(self,self.address,"spa","spa",self.host ))
    
    def delete(self):
        LOGGER.info('Deleting Balboa Spa')

    def check_profile(self):
        self.profile_info = get_profile_info(LOGGER)
        # Set Default profile version if not Found
        cdata = deepcopy(self.polyConfig['customData'])
        LOGGER.info('check_profile: profile_info={0} customData={1}'.format(self.profile_info,cdata))
        if not 'profile_info' in cdata:
            cdata['profile_info'] = { 'version': 0 }
        if self.profile_info['version'] == cdata['profile_info']['version']:
            self.update_profile = False
        else:
            self.update_profile = True
            self.poly.installprofile()
        LOGGER.info('check_profile: update_profile={}'.format(self.update_profile))
        cdata['profile_info'] = self.profile_info
        self.saveCustomData(cdata)

    def install_profile(self,command):
        LOGGER.info("install_profile:")
        self.poly.installprofile()
       
    id = 'controller'
    commands = {
        'QUERY': shortPoll,
        'DISCOVERY': discover,
        'INSTALL_PROFILE': install_profile
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]

class Spa(polyinterface.Node):

    def __init__(self, controller, primary, address, name, host):

        super(Spa, self).__init__(controller, primary, address, name)
        self.queryON = True
        self.host = host

    def start(self):
        pass

    def setP1(self, command):
        pass
        
    def setP2(self, command):
        pass
    
    def setTemp(self, command):
        pass
    
    def setBlower(self, command):
        pass
        
    def setCirP(self, command):
        pass
    
    def setLight(self, command):
        pass
    
    async def getTemp (self) :
        spa = pybalboa.BalboaSpaWifi(self.host)
        await spa.connect()
        await spa.send_mod_ident_req()
        await spa.send_panel_req(0, 1)
        msg = await spa.read_one_message()
        spa.parse_device_configuration(msg)
        if not spa.config_loaded:
            print('Config not loaded, something is wrong!')
        msg = await spa.read_one_message()
        msg = await spa.read_one_message()
        await spa.parse_status_update(msg)
        self.setDriver('CLITEMP', spa.get_curtemp())
        await spa.disconnect()
        return
    
    def query(self):
        #asyncio.run(self.getTemp())
        self.setDriver('CLITEMP', 90)
        self.reportDrivers()
    
    drivers = [{'driver': 'GV1', 'value': 0, 'uom': 25},
               {'driver': 'GV2', 'value': 0, 'uom': 25},
               {'driver': 'GV3', 'value': 0, 'uom': 78},
               {'driver': 'GV4', 'value': 0, 'uom': 78},
               {'driver': 'GV5', 'value': 0, 'uom': 78},
               {'driver': 'CLITEMP', 'value': 0, 'uom': 4}]

    id = 'spa'
    commands = {
                    'SET_SPEED_P1': setP1,
                    'SET_SPEED_P2': setP2,
                    'SET_TEMP': setTemp,
                    'SET_BLOWER': setBlower,
                    'SET_CIRP': setCirP,
                    'SET_LIGHT': setLight
                }

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('SpaNodeServer')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
