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
from central_controller.api_controller import ApiController
from central_controller.configuration_manager import ConfigurationManager
from central_controller.controller_db_interface import ControllerDBInterface
from central_controller.devices_config_loader import DevicesConfigLoader
from central_controller.device_manager import DeviceManager
from central_controller.device_type_manager import DeviceTypeManager
import central_controller.events as Evts
from central_controller.log_store import LogStore
from central_controller.state_manager import StateManager
from central_controller.worker_thread import WorkerThread
from common.Event import Event
from common.EventManager import EventManager
from common.Version import COPYRIGHT, VERSION
from common.Logger import Logger, LogType

class CentralControllerApp:
    # pylint: disable=too-many-instance-attributes

    __slots__ = ['_config_file', '_curr_devices', '__db', '_device_mgr',
                 '_endpoint', '_event_manager', '_logger', '_log_store',
                 '_state_mgr', '_worker_thread']


    def __init__(self, endpoint):
        self._config_file = os.getenv('CENCON_CONFIG')
        self._curr_devices = None
        self.__db = os.getenv('CENCON_DB')
        self._device_mgr = None
        self._endpoint = endpoint
        self._event_manager = None
        self._log_store = LogStore()
        self._state_mgr = None
        self._worker_thread = None
        self._logger = Logger()


    def start_app(self):
        # pylint: disable=too-many-statements
        self._logger.WriteToConsole = True
        self._logger.ExternalLogger = self
        self._logger.Initialise()

        signal.signal(signal.SIGINT, self._signal_handler)

        self._logger.Log(LogType.Info, 'Secure Shed Central Controller V%s',
                         VERSION)
        self._logger.Log(LogType.Info,
                         'Copyright %s Secure Shed Project Dev Team',
                         COPYRIGHT)
        self._logger.Log(LogType.Info,
                         'Licensed under the Apache License, Version 2.0')

        config_manger = ConfigurationManager()

        configuration = config_manger.parse_config_file(self._config_file)
        if not configuration:
            self._logger.Log(LogType.Error,
                             'Parse failed, last message : %s',
                             config_manger.last_error_msg)
            sys.exit(1)

        self._logger.Log(LogType.Info, '=== Configuration Parameters ===')
        self._logger.Log(LogType.Info, 'Environment Variables:')
        self._logger.Log(LogType.Info, '|=> Configuration file       : %s',
                         self._config_file)
        self._logger.Log(LogType.Info, '|=> Database                 : %s',
                         self.__db)
        self._logger.Log(LogType.Info, '===================================')
        self._logger.Log(LogType.Info, '=== Configuration File Settings ===')
        self._logger.Log(LogType.Info, 'General Settings:')
        self._logger.Log(LogType.Info, '|=> Devices Config File      : %s',
                         configuration.general_settings.devicesConfigFile)
        self._logger.Log(LogType.Info, '|=> Device Types Config File : %s',
                         configuration.general_settings.deviceTypesConfigFile)
        self._logger.Log(LogType.Info, 'Keypad Controller Settings:')
        self._logger.Log(LogType.Info, '|=> Authentication Key       : %s',
                         configuration.keypad_controller.authKey)
        self._logger.Log(LogType.Info, '|=> Endpoint                 : %s',
                         configuration.keypad_controller.endpoint)
        self._logger.Log(LogType.Info, 'Central Controller Settings:')
        self._logger.Log(LogType.Info, '|=> Authentication Key       : %s',
                         configuration.central_controller_api.authKey)
        self._logger.Log(LogType.Info, '|=> Network Port             : %s',
                         configuration.central_controller_api.networkPort)
        self._logger.Log(LogType.Info, '================================')

        self._event_manager = EventManager()

        controller_db = ControllerDBInterface()
        if not controller_db.connect(self.__db):
            self._logger.Log(LogType.Error, "Database '%s' is missing!",
                             self.__db)
            sys.exit(1)

        # Build state manager which manages the state of the alarm itself and
        # how states are changed due to hardware device(s) being triggered.
        self._state_mgr = StateManager(controller_db, configuration,
                                       self._event_manager, self._logger)

        # Attempt to load the device types plug-ins, if a plug-in cannot be
        # found or is invalid then a warning is logged and it's not loaded.
        device_type_mgr = DeviceTypeManager(self._logger)
        device_types_cfg = device_type_mgr.read_device_types_config(
            configuration.general_settings.deviceTypesConfigFile)
        if not device_types_cfg:
            self._logger.Log(LogType.Error, device_type_mgr.last_error_msg)
            sys.exit(1)

        device_type_mgr.load_device_types()

        # Load the devices configuration file which contains the devices
        # attached to the alarm.  The devices are matched to the device types
        # loaded above.
        devices_cfg = configuration.general_settings.devicesConfigFile
        devices_cfg_loader = DevicesConfigLoader()
        self._curr_devices = devices_cfg_loader.read_devices_config_file(devices_cfg)
        if not self._curr_devices:
            self._logger.Log(LogType.Error, devices_cfg_loader.last_error_msg)
            sys.exit(1)

        self._device_mgr = DeviceManager(device_type_mgr, self._event_manager,
                                         self._logger)
        dev_lst = self._curr_devices[devices_cfg_loader.JsonTopElement.Devices]
        self._device_mgr.load(dev_lst)
        self._device_mgr.initialise_hardware()

        self._register_event_callbacks()

        # Create the IO processing thread which handles IO requests from
        # hardware devices.
        self._worker_thread = WorkerThread(configuration,
                                           self._device_mgr,
                                           self._event_manager,
                                           self._state_mgr,
                                           self._logger)
        self._worker_thread.start()

        # pylint: disable=unused-variable
        api_controller = ApiController(self._event_manager,
                                       controller_db,
                                       configuration,
                                       self._endpoint,
                                       self._log_store,
                                       self._logger)

        send_alive_ping_evt = Event(Evts.EvtType.KeypadApiSendAlivePing)
        self._event_manager.QueueEvent(send_alive_ping_evt)


    def add_log_event(self, curr_time, log_level, msg):
        self._log_store.add_log_event(curr_time, log_level, msg)


    def _register_event_callbacks(self):

        # =============================
        # == Register event : Keypad ==
        # =============================

        # Register event: Receive keypad event.
        self._event_manager.RegisterEvent(Evts.EvtType.KeypadKeyCodeEntered,
                                          self._state_mgr.rcv_keypad_event)

        # Register event: Receive keypad event.
        self._event_manager.RegisterEvent(Evts.EvtType.SensorDeviceStateChange,
                                          self._state_mgr.rcv_device_event)

        # ===============================
        # == Register event : Hardware ==
        # ===============================

        # Register event: Activate alarm sirens.
        self._event_manager.RegisterEvent(Evts.EvtType.ActivateSiren,
                                          self._device_mgr.receive_event)

        # Register event: Deactivate alarm sirens.
        self._event_manager.RegisterEvent(Evts.EvtType.DeactivateSiren,
                                          self._device_mgr.receive_event)

        # =========================================
        # == Register event : Alarm state change ==
        # =========================================

        # Register event: Alarm activated.
        self._event_manager.RegisterEvent(Evts.EvtType.AlarmActivated,
                                          self._device_mgr.receive_event)

        # Register event: Alarm activated.
        self._event_manager.RegisterEvent(Evts.EvtType.AlarmDeactivated,
                                          self._device_mgr.receive_event)


        # =================================
        # == Register event : Keypad Api ==
        # =================================

        # Register event: Request sending of 'Alive Ping' message.
        self._event_manager.RegisterEvent(Evts.EvtType.KeypadApiSendAlivePing,
                                          self._state_mgr.send_alive_ping_msg)

        # Register event: Request sending of 'Keypad Locked' message.
        self._event_manager.RegisterEvent(Evts.EvtType.KeypadApiSendKeypadLock,
                                          self._state_mgr.send_keypad_locked_msg)


    def _signal_handler(self, signum, frame):
        #pylint: disable=unused-argument

        self._logger.Log(LogType.Info, 'Shutting down...')
        self._shutdown()
        sys.exit(1)


    def _shutdown(self):
        self._worker_thread.signal_shutdown_requested()

        while not self._worker_thread.shutdown_completed:
            time.sleep(1)

        self._logger.Log(LogType.Info, 'Worker thread has Shut down')
