'''
Copyright 2019-2020 Secure Shed Project Dev Team

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
import signal
import sys
from KeypadController.ConfigurationManager import ConfigurationManager
from KeypadController.GuiThread import GuiThread
from KeypadController.KeypadApiController import KeypadApiController
from KeypadController.KeypadStateObject import KeypadStateObject


class KeypadApp:
    __slots__ = ['__configMgr', '__guiThread', '__logger', '__stateObject']

    def __init__(self):
        self.__configMgr = None
        self.__guiThread = None

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                      "%Y-%m-%d %H:%M:%S")
        self.__logger = logging.getLogger('system log')
        consoleStream = logging.StreamHandler()
        consoleStream.setFormatter(formatter)
        self.__logger.setLevel(logging.DEBUG)
        self.__logger.addHandler(consoleStream)

        self.__stateObject = KeypadStateObject()


    def StartApp(self, keypadApiEndpoint):

        self.__configMgr = ConfigurationManager()
        config = self.__configMgr.ParseConfigFile('KeypadController/configuration.json')

        if not config:
            print(f'[ERROR] {self.__configMgr.lastErrorMsg}')
            return

        keypadApiController = KeypadApiController(self.__logger, config,
                                                  keypadApiEndpoint,
                                                  self.__stateObject)

        signal.signal(signal.SIGINT, self.__SignalHandler)

        self.__guiThread = GuiThread(self, config, self.__stateObject)


    def __SignalHandler(self, signum, frame):
        #pylint: disable=unused-argument

        self.__logger.info('Keypad application stopped')
        sys.exit(1)
