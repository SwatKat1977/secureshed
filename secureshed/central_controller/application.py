"""
Copyright 2019-2024 Secure Shed Project Dev Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import asyncio
import json
import logging
import os
import signal
import sys
import time
import jsonschema
import quart
from base_application import BaseApplication
from version import (COPYRIGHT_DATE, VERSION_MAJOR, VERSION_MINOR,
                     VERSION_PATCH, VERSION_LABEL)
from event import Event
from event_manager import EventManager
from failed_attempts_responses_schema import FAILED_ATTEMPT_RESPONSES_SCHEMA
from api_controller import ApiController
from controller_db_interface import ControllerDBInterface
from devices_config_loader import DevicesConfigLoader
from device_manager import DeviceManager
from device_type_manager import DeviceTypeManager
import events as Evts
from state_manager import StateManager
from worker_thread import WorkerThread
from configuration import Configuration
from configuration_layout import CONFIGURATION_LAYOUT

CONFIG_FILE_ENV_VAR: str = "SECURESHED_CONTROLLER_CONFIG"
CONFIG_FILE_REQUIRED_ENV_VAR: str = "SECURESHED_CONTROLLER_CONFIG_REQUIRED"
DB_FILE_ENV_VAR: str = "SECURESHED_CONTROLLER_DB"

class Application(BaseApplication):
    """ Main gateway service application class """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, quart_instance : quart.Quart) -> None:
        super().__init__()
        self._quart: quart.Quart = quart_instance
        self._config_file: str | None = None
        self._database_file: str = ""
        self._database: ControllerDBInterface = None
        self._event_manager: EventManager | None = None
        self._curr_devices = None
        self._device_mgr: DeviceManager | None = None
        self._state_mgr: StateManager | None = None

        self._logger = logging.getLogger(__name__)
        log_format = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                       "%Y-%m-%d %H:%M:%S")
        console_stream = logging.StreamHandler()
        console_stream.setFormatter(log_format)
        self._logger.addHandler(console_stream)
        self._logger.setLevel("INFO")

    def _initialise(self) -> bool:
        """
        Method for the application initialisation.  It should return a boolean
        (True => Successful, False => Unsuccessful).

        returns:
            Boolean: True => Successful, False => Unsuccessful.
        """

        label = "" if VERSION_LABEL == "" else f"-({VERSION_LABEL})"
        version_txt = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}{label}"

        self._logger.info("Secure Shed Central Controller V%s",
                          version_txt)
        self._logger.info("Copyright %s Secure Shed Project Dev Team",
                          COPYRIGHT_DATE)
        self._logger.info("Licensed under the Apache License, Version 2.0")

        self._logger.info("Loading configuration...")
        if not self._load_configuration():
            return False

        self._logger.info("Creating event manager...")
        self._event_manager = EventManager()

        # Load the central controller database.
        if not self._load_database():
            return False

        # Create a state manager which manages the state of the alarm itself
        # and how states are changed due to hardware device(s) being triggered.
        self._logger.info("Creating state manager...")
        self._state_mgr = StateManager(self._database, self._event_manager,
                                       self._logger)

        if not self._load_devices():
            return False

        self._register_event_callbacks()

        return True

    async def _main_loop(self):
        self._state_mgr.update_transitory_events()
        self._device_mgr.check_hardware_devices()
        self._event_manager.ProcessNextEvent()

        await asyncio.sleep(0.1)

    def _load_database(self) -> bool:
        self._database_file = os.getenv(DB_FILE_ENV_VAR)
        if not self._database_file:
            self._logger.error("%s environment variable missing!",
                               DB_FILE_ENV_VAR)
            return False

        if not os.path.isfile(self._database_file):
            self._logger.error("Database file '%s' is inaccessible!",
                               self._database_file)
            return False

        self._logger.info("Opening database...")
        self._database = ControllerDBInterface(self._logger)
        if not self._database.connect(self._database_file):
            return False

        return True

    def _load_configuration(self) -> bool:
        """
        Load the configuration file and parse it.

        :return:
            Load status : True = success, False = failed
        """
        self._config_file = os.getenv(CONFIG_FILE_ENV_VAR, None)
        config_file_required = os.getenv(CONFIG_FILE_REQUIRED_ENV_VAR, None)
        config_file_required = False if not config_file_required \
            else config_file_required

        if not self._config_file and config_file_required:
            self._logger.error("Configuration file missing and is required!")
            return False

        if self._config_file is not None and not os.path.isfile(self._config_file):
            self._logger.error("Config file '%s' is inaccessible!",
                               self._config_file)
            return False

        Configuration().configure(CONFIGURATION_LAYOUT, self._config_file,
                                  config_file_required)
        try:
            Configuration().process_config()

        except ValueError as ex:
            self._logger.critical("Configuration error : %s", ex)
            return False

        raw: str = Configuration().general_failed_attempt_responses.strip()

        try:
            raw_json = json.loads(raw)

        except json.JSONDecodeError as ex:
            self._logger.critical(
                "general::failed_attempt_responses json is invalid : %s",
                ex)
            return False

        try:
            jsonschema.validate(raw_json, schema=FAILED_ATTEMPT_RESPONSES_SCHEMA)

        except jsonschema.SchemaError:
            self._logger.critical(
                "general::failed_attempt_responses json validation failed!")
            return False

        for entry in raw_json:
            Configuration().add_failed_attempt_response(entry)

        self._logger.info("=== Configuration Parameters ===")
        self._logger.info("Environment Variables:")
        self._logger.info("|=> Configuration file : %s",
                         self._config_file)
        self._logger.info("|=> Database           : %s", self._database_file)
        self._logger.info("===================================")
        self._logger.info("=== Configuration File Settings ===")
        self._logger.info("General Settings:")
        self._logger.info("|=> Devices Config File      : %s",
                          Configuration().general_devices_config_file)
        self._logger.info("|=> Device Types Config File : %s",
                          Configuration().general_device_types_config_file)
        self._logger.info("|=> Authentication Key       : <REDACTED>")
        self._logger.info("|=> Failed Attempt Responses :")
        failed_responses = Configuration().get_failed_attempt_responses()
        for response_entry in failed_responses:
            self._logger.info("|===> [Attempt %d] Actions : %s",
                              response_entry['attemptNo'],
                              response_entry['actions'])
        self._logger.info("Keypad Controller Settings:")
        self._logger.info('|=> Endpoint                 : %s',
                          Configuration().keypad_controller_endpoint)
        self._logger.info("================================")

        return True

    def _load_devices(self) -> bool:
        # Attempt to load the device types plug-ins, if a plug-in cannot be
        # found or is invalid then a warning is logged and it's not loaded.
        device_type_mgr = DeviceTypeManager(self._logger)
        device_types_cfg = device_type_mgr.read_device_types_config(
            Configuration().general_device_types_config_file)
        if not device_types_cfg:
            self._logger.error(device_type_mgr.last_error_msg)
            return False

        device_type_mgr.load_device_types()

        # Load the devices configuration file which contains the devices
        # attached to the alarm.  The devices are matched to the device types
        # loaded above.
        devices_cfg = Configuration().general_devices_config_file
        devices_cfg_loader = DevicesConfigLoader()
        self._curr_devices = devices_cfg_loader.read_devices_config_file(devices_cfg)
        if not self._curr_devices:
            self._logger.error(devices_cfg_loader.last_error_msg)
            return False

        self._device_mgr = DeviceManager(device_type_mgr, self._event_manager,
                                         self._logger)
        dev_lst = self._curr_devices[devices_cfg_loader.JsonTopElement.Devices]
        self._device_mgr.load(dev_lst)
        self._device_mgr.initialise_hardware()

        return True

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

        """
        self._logger.Log(LogType.Info, 'Secure Shed Central Controller V%s',
                         VERSION_MAJOR)
        self._logger.Log(LogType.Info,
                         'Copyright %s Secure Shed Project Dev Team',
                         COPYRIGHT_DATE)
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
        """

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
