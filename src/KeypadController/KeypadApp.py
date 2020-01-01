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
import wx
from ConfigurationManager import ConfigurationManager
from ControlPanelFrame import ControlPanelFrame


class KeypadApp:
    __slots__ = ['__configMgr']

    def __init__(self):
        self.__configMgr = None


    def StartApp(self):

        self.__configMgr = ConfigurationManager()
        config = self.__configMgr.ParseConfigFile('configuration.json')

        if not config:
            print(f'[ERROR] {self.__configMgr.lastErrorMsg}')
            return

        guiApp = wx.App(False)

        windowSize = (config.gui.windowWidth, config.gui.windowHeight)
        frame = ControlPanelFrame(config, windowSize)
        frame.Show()

        guiApp.MainLoop()


    def StopApp(self):
        print('Keypad application stopped')
        self.__configMgr = None
