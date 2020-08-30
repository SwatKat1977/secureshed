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
import logging
from twisted.internet import wxreactor
from twisted.internet.task import LoopingCall
wxreactor.install()
from twisted.internet import reactor
from twisted.web import server
import wx
from common.Logger import Logger, LogType
from ConfigurationManager import ConfigurationManager
from KeypadApiController import KeypadApiController
from KeypadStateObject import KeypadStateObject
from LogStore import LogStore


## The main application class for the keypad controller application.
class KeypadApp:
    # pylint: disable=R0903

    ## __slots__ allow us to explicitly declare data members
    __slots__ = ['__configMgr', '_logStore', '__stateObject']


    ## KeypadApp class constructor.
    #  @param self The object pointer.
    def __init__(self):
        ## Instance of a configuration manager class.
        self.__configMgr = None
        self._logStore = LogStore()

        Logger.Instance().WriteToConsole = True
        Logger.Instance().ExternalLogger = self
        Logger.Instance().Initialise()

        ## Instance of the keypad state object.
        self.__stateObject = None


    ## Start the application, this will not exit until both the GUI and the
    #  Twisted reactor have been destroyed.  The only exception is if any
    #  elements of the startup fail (e.g. loading the configuration).
    #  @param self The object pointer.
    def StartApp(self):

        self.__configMgr = ConfigurationManager()
        config = self.__configMgr.ParseConfigFile('configuration.json')

        if not config:
            Logger.Instance().Log(LogType.Error, self.__configMgr.lastErrorMsg)
            return

        wxApp = wx.App()
        reactor.registerWxApp(wxApp)

        self.__stateObject = KeypadStateObject(config)

        keypadApiCtrl = KeypadApiController(config, self.__stateObject,
                                            self._logStore)
        apiServer = server.Site(keypadApiCtrl)
        reactor.listenTCP(config.keypadController.networkPort, apiServer)

        checkPanelLoopingCall = LoopingCall(self.__stateObject.CheckPanel)
        checkPanelLoopingCall.start(0.01, now=False)

        reactor.run()

    ## Stop the application.
    #  @param self The object pointer.
    def StopApp(self):
        Logger.Instance().Log(LogType.Info,
                              'Stopping keypad controller, cleaning up...')


    def AddLogEvent(self, currTime, logLevel, msg):
        self._logStore.AddLogEvent(currTime, logLevel, msg)
