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
import os
import sys
import wx
from ConfigurationManager import ConfigurationManager
from Gui.MainWindow import MainWindow


## The main application class for the keypad controller application.
class PowerConsoleApp:
    # pylint: disable=R0903

    ## __slots__ allow us to explicitly declare data members
    __slots__ = ['_configMgr', '_logger']

    ## KeypadApp class constructor.
    #  @param self The object pointer.
    def __init__(self):
        ## Instance of a configuration manager class.
        self._configMgr = None

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                      "%Y-%m-%d %H:%M:%S")

        ## Instance of a logger.
        self._logger = logging.getLogger('system log')
        consoleStream = logging.StreamHandler()
        consoleStream.setFormatter(formatter)
        self._logger.setLevel(logging.DEBUG)
        self._logger.addHandler(consoleStream)


    ## Start the application, this will not exit until both the GUI and the
    #  Twisted reactor have been destroyed.  The only exception is if any
    #  elements of the startup fail (e.g. loading the configuration).
    #  @param self The object pointer.
    def StartApp(self):

        if not os.getenv('PWRCON_CONFIG'):
            self._logger.error('PWRCON_CONFIG environment variable missing!')
            sys.exit(1)

        configFile = os.getenv('PWRCON_CONFIG')
        self._configMgr = ConfigurationManager()
        config = self._configMgr.ParseConfigFile(configFile)

        if not config:
            print(f"ERROR: {self._configMgr.lastErrorMsg}")
            return

        wxApp = wx.App()

        mainWindow = MainWindow(config)
        mainWindow.Show()

        wxApp.MainLoop()


    ## Stop the application.
    #  @param self The object pointer.
    def StopApp(self):
        self._logger.info('Stopping power console, cleaning up...')

