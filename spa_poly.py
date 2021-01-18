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
        'DISCOVER': discover,
        'INSTALL_PROFILE': install_profile
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]

class Spa(polyinterface.Node):

    def __init__(self, controller, primary, address, name, host):

        super(Spa, self).__init__(controller, primary, address, name)
        self.queryON = True
        self.host = host

    def start(self):
        self.query()

    def setP1(self, command):
        asyncio.run(self._setPump(0,int(command.get('value'))))
        
    def setP2(self, command):
        asyncio.run(self._setPump(1,int(command.get('value'))))
    
    def setTemp(self, command):
        asyncio.run(self._setTemp(int(command.get('value'))))
    
    def setBlower(self, command):
        if ( int(command.get('value')) == 100 ) :
            val = 1
        else :
            val = 0
        asyncio.run(self._setBlower(val))
        
    def setCirP(self, command):
        asyncio.run(self._setPump(0,int(command.get('value'))))
    
    def setLight(self, command):
        asyncio.run(self._setLight(0,int(command.get('value'))))
                        
    def query(self):
        asyncio.run(self._getSpaStatus())
        self.reportDrivers()
    
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
    
    async def _getSpaStatus (self) :
        try :
            print ("Begin")
            spa = pybalboa.BalboaSpaWifi(self.host)
            await spa.connect()
            asyncio.ensure_future(spa.listen()) 
            await spa.send_panel_req(0, 1)

            for i in range(0, 30):
                await asyncio.sleep(1)
                if spa.config_loaded:
                    print("Config is loaded:")
                    print('Pump Array: {0}'.format(str(spa.pump_array)))
                    print('Light Array: {0}'.format(str(spa.light_array)))
                    print('Aux Array: {0}'.format(str(spa.aux_array)))
                    print('Circulation Pump: {0}'.format(spa.circ_pump))
                    print('Blower: {0}'.format(spa.blower))
                    print('Mister: {0}'.format(spa.mister))
                    break
            print()

            lastupd = 0
            for i in range(0, 3):
                await asyncio.sleep(1)
                if spa.lastupd != lastupd:
                    lastupd = spa.lastupd
                    print("New data as of {0}".format(spa.lastupd))
                    print("Current Temp: {0}".format(spa.curtemp))
                    print("Tempscale: {0}".format(spa.get_tempscale(text=True)))
                    print("Set Temp: {0}".format(spa.get_settemp()))
                    print("Heat Mode: {0}".format(spa.get_heatmode(True)))
                    print("Heat State: {0}".format(spa.get_heatstate(True)))
                    print("Temp Range: {0}".format(spa.get_temprange(True)))
                    print("Pump Status: {0}".format(str(spa.pump_status)))
                    print("Circulation Pump: {0}".format(spa.get_circ_pump(True)))
                    print("Light Status: {0}".format(str(spa.light_status)))
                    print("Mister Status: {0}".format(spa.get_mister(True)))
                    print("Aux Status: {0}".format(str(spa.aux_status)))
                    print("Blower Status: {0}".format(spa.get_blower(True)))
                    print("Spa Time: {0:02d}:{1:02d} {2}".format(
                        spa.time_hour,
                        spa.time_minute,
                        spa.get_timescale(True)
                    ))
                    print("Filter Mode: {0}".format(spa.get_filtermode(True)))
                    print()

            self.setDriver('CLITEMP', spa.get_curtemp())
            await spa.disconnect()
            print ("End")
            return
        except Exception as ex :
            print ("_setTemp: ", ex )
    
    async def _setTemp(self,temp):
        try:
            spa = pybalboa.BalboaSpaWifi(self.host)
            await spa.connect()
            asyncio.ensure_future(spa.listen())     
            await spa.send_panel_req(0, 1)
            for i in range(0, 30):
                await asyncio.sleep(1)
                if spa.config_loaded:
                    break
            await spa.send_temp_change(temp)
            await spa.disconnect()
        except Exception as ex :
            LOGGER.debug ("_setTemp: ", ex )
        
    async def _setPump(self,pump, setting):
        try:
            spa = pybalboa.BalboaSpaWifi(self.host)
            await spa.connect()
            asyncio.ensure_future(spa.listen())
            await spa.send_panel_req(0, 1)
            for i in range(0, 30):
                await asyncio.sleep(1)
                if spa.config_loaded:
                    break
            await spa.change_pump(pump, setting)
            await spa.disconnect()
        except Exception as ex :
            LOGGER.debug ("_setPump: ", ex )
        return
                        
    async def _setBlower(self,setting):
        try :
            spa = pybalboa.BalboaSpaWifi(self.host)
            await spa.connect()
            asyncio.ensure_future(spa.listen())
            await spa.send_panel_req(0, 1)
            for i in range(0, 30):
                await asyncio.sleep(1)
                if spa.config_loaded:
                    break
            await spa.change_blower(setting)
            await spa.disconnect()
        except Exception as ex :
            LOGGER.debug ("_setBlower: ", ex )
        return
                        
    async def _setLight(self,state):
        spa = pybalboa.BalboaSpaWifi(self.host)
        await spa.connect()
        asyncio.ensure_future(spa.listen())     
        await spa.send_panel_req(0, 1)
        for i in range(0, 30):
            await asyncio.sleep(1)
            if spa.config_loaded:
                break
        await spa.change_light(0,state)
        await spa.disconnect()
                       
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
