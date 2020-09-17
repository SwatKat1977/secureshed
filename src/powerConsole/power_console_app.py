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
from configuration_manager import ConfigurationManager
from Gui.main_window import MainWindow


## The main application class for the keypad controller application.
class PowerConsoleApp:
    # pylint: disable=R0903

    ## __slots__ allow us to explicitly declare data members
    __slots__ = ['_config_mgr', '_logger']

    ## KeypadApp class constructor.
    #  @param self The object pointer.
    def __init__(self):
        ## Instance of a configuration manager class.
        self._config_mgr = None

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                      "%Y-%m-%d %H:%M:%S")

        ## Instance of a logger.
        self._logger = logging.getLogger('system log')
        console_stream = logging.StreamHandler()
        console_stream.setFormatter(formatter)
        self._logger.setLevel(logging.DEBUG)
        self._logger.addHandler(console_stream)


    ## Start the application, this will not exit until both the GUI and the
    #  Twisted reactor have been destroyed.  The only exception is if any
    #  elements of the startup fail (e.g. loading the configuration).
    #  @param self The object pointer.
    def start_app(self):

        if not os.getenv('PWRCON_CONFIG'):
            self._logger.error('PWRCON_CONFIG environment variable missing!')
            sys.exit(1)

        config_file = os.getenv('PWRCON_CONFIG')

        self._config_mgr = ConfigurationManager()
        config = self._config_mgr.parse_config_file(config_file)

        if not config:
            print(f"ERROR: {self._config_mgr.last_error_msg}")
            return

        wx_app = wx.App()

        main_window = MainWindow(config)
        main_window.Show()

        wx_app.MainLoop()


    ## Stop the application.
    #  @param self The object pointer.
    def stop_app(self):
        self._logger.info('Stopping power console, cleaning up...')
