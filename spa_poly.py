#!/usr/bin/env python3

"""
This is a NodeServer for August written by automationgeek (Jean-Francois Tremblay)
based on the NodeServer template for Polyglot v2 written in Python2/3 by Einstein.42 (James Milne) milne.james@gmail.com
"""

import polyinterface
import hashlib
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
        
    def start(self):
        LOGGER.info('Started August for v2 NodeServer version %s', str(VERSION))
        self.setDriver('ST', 1)
        try:
            if 'email' in self.polyConfig['customParams']:
                self.email = self.polyConfig['customParams']['email']
            else:
                self.email = ""
                
            if 'password' in self.polyConfig['customParams']:
                self.password = self.polyConfig['customParams']['password']
            else:
                self.password = ""
            
            # Generate a UUID ( 11111111-1111-1111-1111-111111111111 )
            if 'install_id' in self.polyConfig['customParams']:
                self.install_id = self.polyConfig['customParams']['install_id']
            else:
                self.install_id = str(uuid.uuid4())
                self.saveCustomData({ 'install_id': self.install_id })
                LOGGER.debug('UUID Generated: {}'.format(self.install_id))

            if self.email == "" or self.password == "" or self.install_id == "":
                LOGGER.error('August requires email,password,install_id parameters to be specified in custom configuration.')
                return False
            else:
                self.check_profile()
                self.discover()

        except Exception as ex:
            LOGGER.error('Error starting August NodeServer: %s', str(ex))
           
    def shortPoll(self):
        self.setDriver('ST', 1)
        self.reportDrivers()
        for node in self.nodes:
            if  self.nodes[node].queryON == True :
                self.nodes[node].query()

    def longPoll(self):
        self.heartbeat()
        
        # Refresh Token
        self.authenticator.refresh_access_token()

    def heartbeat(self):
        LOGGER.debug('heartbeat: hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def discover(self, *args, **kwargs):
        count = 1
        
        self.api = Api(timeout=20)
        self.authenticator = Authenticator(self.api, "email", self.email, self.password, install_id=self.install_id, access_token_cache_file="/var/polyglot/nodeservers/AugustLock/augustToken.txt")
        self.authentication = self.authenticator.authenticate()
        if ( self.authentication.state is AuthenticationState.AUTHENTICATED ) :
            locks = self.api.get_locks(self.authentication.access_token)
            for lock in locks:
                myhash =  str(int(hashlib.md5(lock.device_id.encode('utf8')).hexdigest(), 16) % (10 ** 8))
                self.addNode(AugustLock(self,self.address,myhash,  "lock_" + str(count),self.api, self.authentication, lock ))
                count = count + 1
        else :
            self.authenticator.send_verification_code()
            LOGGER.error('August requires validation, please send your authentification code')
        
    def delete(self):
        LOGGER.info('Deleting August')

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
        
    def send_validation_code(self,command) :
        LOGGER.info("Send Validation Code")
        val = int(command.get('value'))
        validation_result = self.authenticator.validate_verification_code(val)
        self.authentication = authenticator.authenticate()
        if ( self.authentication.state is not AuthenticationState.AUTHENTICATED ) :
            LOGGER.info("Invalid Authentication Code")
        else :
            LOGGER.info("Successfully Authentificated")

    id = 'controller'
    commands = {
        'QUERY': shortPoll,
        'DISCOVER': discover,
        'INSTALL_PROFILE': install_profile,
        'VALIDATE_CODE': send_validation_code,
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}, 
               {'driver': 'GV3', 'value': 0, 'uom': 56}]

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
    
    def setLightself, command):
        pass
    
    def query(self):
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
