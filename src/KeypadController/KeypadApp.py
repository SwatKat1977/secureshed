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
# pylint: disable=C0413
from twisted.internet import wxreactor
from twisted.internet.task import LoopingCall
wxreactor.install()
from twisted.internet import reactor
from twisted.web import server
import wx
from common.Logger import Logger, LogType
from configuration_manager import ConfigurationManager
from KeypadApiController import KeypadApiController
from keypad_state_object import KeypadStateObject
from log_store import LogStore


## The main application class for the keypad controller application.
class KeypadApp:
    # pylint: disable=R0903

    ## __slots__ allow us to explicitly declare data members
    __slots__ = ['_config_mgr', '_logger', '_log_store', '_state_object']


    ## KeypadApp class constructor.
    #  @param self The object pointer.
    def __init__(self):
        ## Instance of a configuration manager class.
        self._config_mgr = None
        self._logger = Logger()
        self._log_store = LogStore()

        self._logger.WriteToConsole = True
        self._logger.ExternalLogger = self
        self._logger.Initialise()

        ## Instance of the keypad state object.
        self._state_object = None


    ## Start the application, this will not exit until both the GUI and the
    #  Twisted reactor have been destroyed.  The only exception is if any
    #  elements of the startup fail (e.g. loading the configuration).
    #  @param self The object pointer.
    def start_app(self):

        self._config_mgr = ConfigurationManager()
        config = self._config_mgr.parse_config_file('configuration.json')

        if not config:
            self._logger.Log(LogType.Error, self._config_mgr.last_error_msg)
            return

        wx_app = wx.App()
        reactor.registerWxApp(wx_app)

        self._state_object = KeypadStateObject(config, self._logger)

        keypad_api_ctrl = KeypadApiController(config, self._state_object,
                                              self._log_store, self._logger)
        api_server = server.Site(keypad_api_ctrl)
        reactor.listenTCP(config.keypadController.networkPort, api_server)

        check_panel_loop = LoopingCall(self._state_object.check_panel)
        check_panel_loop.start(0.01, now=False)

        reactor.run()


    ## Stop the application.
    #  @param self The object pointer.
    def stop_app(self):
        self._logger.Log(LogType.Info,
                         'Stopping keypad controller, cleaning up...')


    def AddLogEvent(self, current_time, log_level, msg):
        self._log_store.AddLogEvent(current_time, log_level, msg)
