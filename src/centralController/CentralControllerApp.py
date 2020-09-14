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
import os
import signal
import sys
import time
from centralController.ApiController import ApiController
from centralController.ConfigurationManager import ConfigurationManager
from centralController.ControllerDBInterface import ControllerDBInterface
from centralController.DevicesConfigLoader import DevicesConfigLoader
from centralController.DeviceManager import DeviceManager
from centralController.DeviceTypeManager import DeviceTypeManager
import centralController.Events as Evts
from centralController.LogStore import LogStore
from centralController.StateManager import StateManager
from centralController.WorkerThread import WorkerThread
from common.Event import Event
from common.EventManager import EventManager
from common.Version import COPYRIGHT, VERSION
from common.Logger import Logger, LogType

class CentralControllerApp:
    __slots__ = ['__configFile', '__currDevices', '__db', '__deviceMgr',
                 '__endpoint', '__eventManager', '_logger', '_logStore',
                 '__stateMgr', '__workerThread']


    def __init__(self, endpoint):
        self.__configFile = os.getenv('CENCON_CONFIG')
        self.__currDevices = None
        self.__db = os.getenv('CENCON_DB')
        self.__deviceMgr = None
        self.__endpoint = endpoint
        self.__eventManager = None
        self._logStore = LogStore()
        self.__stateMgr = None
        self.__workerThread = None
        self._logger = Logger()


    def StartApp(self):
        self._logger.WriteToConsole = True
        self._logger.ExternalLogger = self
        self._logger.Initialise()

        signal.signal(signal.SIGINT, self.__SignalHandler)

        self._logger.Log(LogType.Info, 'Secure Shed Central Controller V%s',
                         VERSION)
        self._logger.Log(LogType.Info,
                         'Copyright %s Secure Shed Project Dev Team',
                         COPYRIGHT)
        self._logger.Log(LogType.Info,
                              'Licensed under the Apache License, Version 2.0')

        configManger = ConfigurationManager()

        configuration = configManger.ParseConfigFile(self.__configFile)
        if not configuration:
            self._logger.Log(LogType.Error,
                                  'Parse failed, last message : %s',
                                  configManger.lastErrorMsg)
            sys.exit(1)

        self._logger.Log(LogType.Info, '=== Configuration Parameters ===')
        self._logger.Log(LogType.Info, 'Environment Variables:')
        self._logger.Log(LogType.Info, '|=> Configuration file       : %s',
                              self.__configFile)
        self._logger.Log(LogType.Info, '|=> Database                 : %s',
                              self.__db)
        self._logger.Log(LogType.Info, '===================================')
        self._logger.Log(LogType.Info, '=== Configuration File Settings ===')
        self._logger.Log(LogType.Info, 'General Settings:')
        self._logger.Log(LogType.Info, '|=> Devices Config File      : %s',
                         configuration.generalSettings.devicesConfigFile)
        self._logger.Log(LogType.Info, '|=> Device Types Config File : %s',
                         configuration.generalSettings.deviceTypesConfigFile)
        self._logger.Log(LogType.Info, 'Keypad Controller Settings:')
        self._logger.Log(LogType.Info, '|=> Authentication Key       : %s',
                         configuration.keypadController.authKey)
        self._logger.Log(LogType.Info, '|=> Endpoint                 : %s',
                         configuration.keypadController.endpoint)
        self._logger.Log(LogType.Info, 'Central Controller Settings:')
        self._logger.Log(LogType.Info, '|=> Authentication Key       : %s',
                         configuration.centralControllerApi.authKey)
        self._logger.Log(LogType.Info, '|=> Network Port             : %s',
                         configuration.centralControllerApi.networkPort)
        self._logger.Log(LogType.Info, '================================')

        self.__eventManager = EventManager()

        controllerDb = ControllerDBInterface()
        if not controllerDb.Connect(self.__db):
            self._logger.Log(LogType.Error, "Database '%s' is missing!",
                             self.__db)
            sys.exit(1)

        # Build state manager which manages the state of the alarm itself and
        # how states are changed due to hardware device(s) being triggered.
        self.__stateMgr = StateManager(controllerDb, configuration,
                                       self.__eventManager, self._logger)

        # Attempt to load the device types plug-ins, if a plug-in cannot be
        # found or is invalid then a warning is logged and it's not loaded.
        deviceTypeMgr = DeviceTypeManager(self._logger)
        deviceTypesCfg = deviceTypeMgr.ReadDeviceTypesConfig(
            configuration.generalSettings.deviceTypesConfigFile)
        if not deviceTypesCfg:
            self._logger.Log(LogType.Error, deviceTypeMgr.lastErrorMsg)
            sys.exit(1)

        deviceTypeMgr.LoadDeviceTypes()

        # Load the devices configuration file which contains the devices
        # attached to the alarm.  The devices are matched to the device types
        # loaded above.
        devicesCfg = configuration.generalSettings.devicesConfigFile
        devicesConfigLoader = DevicesConfigLoader()
        self.__currDevices = devicesConfigLoader.ReadDevicesConfigFile(devicesCfg)
        if not self.__currDevices:
            self._logger.Log(LogType.Error, devicesConfigLoader.lastErrorMsg)
            sys.exit(1)

        self.__deviceMgr = DeviceManager(deviceTypeMgr, self.__eventManager,
                                         self._logger)
        devLst = self.__currDevices[devicesConfigLoader.JsonTopElement.Devices]
        self.__deviceMgr.Load(devLst)
        self.__deviceMgr.InitialiseHardware()

        self.__RegisterEventCallbacks()

        # Create the IO processing thread which handles IO requests from
        # hardware devices.
        self.__workerThread = WorkerThread(configuration,
                                           self.__deviceMgr,
                                           self.__eventManager,
                                           self.__stateMgr,
                                           self._logger)
        self.__workerThread.start()

        apiController = ApiController(self.__eventManager,
                                      controllerDb,
                                      configuration,
                                      self.__endpoint,
                                      self._logStore,
                                      self._logger)

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


        # =================================
        # == Register event : Keypad Api ==
        # =================================

        # Register event: Request sending of 'Alive Ping' message.
        self.__eventManager.RegisterEvent(Evts.EvtType.KeypadApiSendAlivePing,
                                          self.__stateMgr.SendAlivePingMsg)

        # Register event: Request sending of 'Keypad Locked' message.
        self.__eventManager.RegisterEvent(Evts.EvtType.KeypadApiSendKeypadLock,
                                          self.__stateMgr.SendKeypadLockedMsg)


    def __SignalHandler(self, signum, frame):
        #pylint: disable=unused-argument

        self._logger.Log(LogType.Info, 'Shutting down...')
        self.__Shutdown()
        sys.exit(1)


    def __Shutdown(self):
        self.__workerThread.SignalShutdownRequested()

        while not self.__workerThread.shutdownCompleted:
            time.sleep(1)

        self._logger.Log(LogType.Info, 'Worker thread has Shut down')


    def AddLogEvent(self, currTime, logLevel, msg):
        self._logStore.AddLogEvent(currTime, logLevel, msg)
