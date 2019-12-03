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
from centralController.KeypadAPIThread import KeypadApiController
from centralController.IOProcessingThread import IOProcessingThread
from centralController.StatusObject import StatusObject
from centralController.KeypadAPIThread import KeypadApiController


class CentralControllerApp:
    __slots__ = ['__db', '__configFile', '__endpoint', '__ioProcessor',
                 '__logger']


    def __init__(self, endpoint):
        self.__endpoint = endpoint
        self.__configFile = os.getenv('CENCON_CONFIG')
        self.__db = os.getenv('CENCON_DB')
        self.__logger = None
        self.__ioProcessor = None


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

        self.__logger.info(f'Configuration file : {self.__configFile}')
        self.__logger.info(f'Database           : {self.__db}')

        configManger = ConfigurationManager()

        configuration = configManger.ParseConfigFile(self.__configFile)
        if not configuration:
            print(f"Parse failed, last message : {configManger.LastErrorMsg}")
            sys.exit(1)

        statusObject = StatusObject()

        controllerDb = ControllerDBInterface()
        if not controllerDb.Connect(self.__db):
            self.__logger.error("[ERROR] Database '%s' is missing!", self.__db)
            sys.exit(1)
 
        self.__ioProcessor = IOProcessingThread(self.__logger, statusObject,
                                                configuration)
        self.__ioProcessor.start()

        ###     def __init__(self, logger, statusObject, controllerDb, config, endpoint):
        keypadApiController = KeypadApiController(self.__logger, statusObject,
                                                  controllerDb, configuration,
                                                  self.__endpoint)


    def __SignalHandler(self, signum, frame):
        #pylint: disable=unused-argument

        self.__logger.info('Shutting down...')
        self.__Shutdown()
        sys.exit(1)


    def __Shutdown(self):
        self.__ioProcessor.SignalShutdownRequested()

        while not self.__ioProcessor.shutdownCompleted:
            time.sleep(5)
            pass

        self.__logger.info('IO Processor has Shut down')
