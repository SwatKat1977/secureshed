'''
Copyright 2019 Secure Shed Project Dev Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import logging
import os
import signal
import sys
import time
from centralController.ConfigurationManager import ConfigurationManager
from centralController.ControllerDBInterface import ControllerDBInterface
from centralController.DevicesConfigLoader import DevicesConfigLoader
from centralController.DeviceManager import DeviceManager
from centralController.DeviceTypeManager import DeviceTypeManager
from centralController.KeypadAPIThread import KeypadApiController
import centralController.Events as Evts
from centralController.StateManager import StateManager
from centralController.WorkerThread import WorkerThread
from common.Event import Event
from common.EventManager import EventManager
from common.Version import COPYRIGHT, VERSION


class CentralControllerApp:
    __slots__ = ['__configFile', '__currDevices', '__db', '__deviceMgr',
                 '__endpoint', '__eventManager', '__keypadApiController',
                 '__logger', '__stateMgr', '__workerThread']


    def __init__(self, endpoint):
        self.__configFile = os.getenv('CENCON_CONFIG')
        self.__currDevices = None
        self.__db = os.getenv('CENCON_DB')
        self.__deviceMgr = None
        self.__endpoint = endpoint
        self.__eventManager = None
        self.__keypadApiController = None
        self.__logger = None
        self.__stateMgr = None
        self.__workerThread = None


    def StartApp(self):
        # Configure the logging for the application.
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                      "%Y-%m-%d %H:%M:%S")
        self.__logger = logging.getLogger('system log')
        consoleStream = logging.StreamHandler()
        consoleStream.setFormatter(formatter)
        self.__logger.setLevel(logging.DEBUG)
        self.__logger.addHandler(consoleStream)

        signal.signal(signal.SIGINT, self.__SignalHandler)

        self.__logger.info('Secure Shed Central Controller V%s', VERSION)
        self.__logger.info('Copyright %s Secure Shed Project Dev Team',
                           COPYRIGHT)
        self.__logger.info('Licensed under the Apache License, Version 2.0')

        configManger = ConfigurationManager()

        configuration = configManger.ParseConfigFile(self.__configFile)
        if not configuration:
            self.__logger.error('Parse failed, last message : %s',
                                configManger.lastErrorMsg)
            sys.exit(1)

        self.__logger.info('=== Configuration Parameters ===')
        self.__logger.info('Environment Variables:')
        self.__logger.info('|=> Configuration file : %s', self.__configFile)
        self.__logger.info('|=> Database           : %s', self.__db)
        self.__logger.info('================================')

        self.__eventManager = EventManager()

        controllerDb = ControllerDBInterface()
        if not controllerDb.Connect(self.__db):
            self.__logger.error("Database '%s' is missing!", self.__db)
            sys.exit(1)

        # Build state manager which manages the state of the alarm itself and
        # how states are changed due to hardware device(s) being triggered.
        self.__stateMgr = StateManager(controllerDb, self.__logger, configuration,
                                       self.__eventManager)

        # Attempt to load the device types plug-ins, if a plug-in cannot be
        # found or is invalid then a warning is logged and it's not loaded.
        deviceTypeMgr = DeviceTypeManager(self.__logger)
        deviceTypeMgr.LoadDeviceTypes()

        # Load the devices configuration file which contains the devices
        # attached to the alarm.  The devices are matched to the device types
        # loaded above.
        devicesCfg = configuration.generalSettings.devicesConfigFile
        devicesConfigLoader = DevicesConfigLoader()
        self.__currDevices = devicesConfigLoader.ReadDevicesConfigFile(devicesCfg)
        if not self.__currDevices:
            self.__logger.error(devicesConfigLoader.lastErrorMsg)
            sys.exit(1)

        self.__deviceMgr = DeviceManager(self.__logger, deviceTypeMgr,
                                         self.__eventManager)
        devLst = self.__currDevices[devicesConfigLoader.JsonTopElement.Devices]
        self.__deviceMgr.Load(devLst)
        self.__deviceMgr.InitialiseHardware()

        self.__RegisterEventCallbacks()

        # Create the IO processing thread which handles IO requests from
        # hardware devices.
        self.__workerThread = WorkerThread(self.__logger, configuration,
                                           self.__deviceMgr,
                                           self.__eventManager,
                                           self.__stateMgr)
        self.__workerThread.start()

        self.__keypadApiController = KeypadApiController(self.__logger,
                                                         self.__eventManager,
                                                         controllerDb,
                                                         configuration,
                                                         self.__endpoint)

        sendAlivePingEvt = Event(Evts.EvtType.KeypadApiSendAlivePing)
        self.__eventManager.QueueEvent(sendAlivePingEvt)


    def __RegisterEventCallbacks(self):

        # =============================
        # == Register event : Keypad ==
        # =============================

        # Register event: Receive keypad event.
        self.__eventManager.RegisterEvent(Evts.EvtType.KeypadKeyCodeEntered,
                                          self.__stateMgr.RcvKeypadEvent)

        # Register event: Receive keypad event.
        self.__eventManager.RegisterEvent(Evts.EvtType.SensorDeviceStateChange,
                                          self.__stateMgr.RcvDeviceEvent)

        # ===============================
        # == Register event : Hardware ==
        # ===============================

        # Register event: Activate alarm sirens.
        self.__eventManager.RegisterEvent(Evts.EvtType.ActivateSiren,
                                          self.__deviceMgr.ReceiveEvent)

        # Register event: Deactivate alarm sirens.
        self.__eventManager.RegisterEvent(Evts.EvtType.DeactivateSiren,
                                          self.__deviceMgr.ReceiveEvent)

        # =========================================
        # == Register event : Alarm state change ==
        # =========================================

        # Register event: Alarm activated.
        self.__eventManager.RegisterEvent(Evts.EvtType.AlarmActivated,
                                          self.__deviceMgr.ReceiveEvent)

        # Register event: Alarm activated.
        self.__eventManager.RegisterEvent(Evts.EvtType.AlarmDeactivated,
                                          self.__deviceMgr.ReceiveEvent)


        # ===========================================
        # == Register event : Keypad state changes ==
        # ===========================================

        # Register event: Alarm activated.
        self.__eventManager.RegisterEvent(Evts.EvtType.KeypadApiSendAlivePing,
                                          self.__stateMgr.SendAlivePingEvent)


    def __SignalHandler(self, signum, frame):
        #pylint: disable=unused-argument

        self.__logger.info('Shutting down...')
        self.__Shutdown()
        sys.exit(1)


    def __Shutdown(self):
        self.__workerThread.SignalShutdownRequested()

        while not self.__workerThread.shutdownCompleted:
            time.sleep(1)

        self.__logger.info('Worker thread has Shut down')
