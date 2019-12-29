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

    def __init__(self):
        pass


    def StartApp(self):

        configMgr = ConfigurationManager()
        config = configMgr.ParseConfigFile('configuration.json')

        if not config:
            print(f'[ERROR] {configMgr.lastErrorMsg}')
            return

        guiApp = wx.App(False)

        frame = ControlPanelFrame(config)
        frame.Show()

        guiApp.MainLoop()
