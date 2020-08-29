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
import wx
from common.APIClient.APIEndpointClient import APIEndpointClient
from Gui.ConsoleLogsPanel import ConsoleLogsPanel
from Gui.KeypadControllerConfigPanel import KeypadControllerConfigPanel


class KeypadControllerPanel(wx.Panel):

    def __init__(self, parent, config):
        wx.Panel.__init__(self, parent)

        self._config = config
        self._apiClient = APIEndpointClient(config.keypadController.endpoint)

        topSplitter = wx.SplitterWindow(self)
        self._configPanel = KeypadControllerConfigPanel(topSplitter)
        self._logsPanel = ConsoleLogsPanel(topSplitter)
        topSplitter.SplitHorizontally(self._configPanel, self._logsPanel)
        topSplitter.SetSashGravity(0.5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(topSplitter, 1, wx.EXPAND)
        self.SetSizer(sizer)
