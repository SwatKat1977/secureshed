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
from common.Version import VERSION, COPYRIGHT
from Gui.MainWindowTree import MainWindowTree
from Gui.ConsoleLogsPanel import ConsoleLogsPanel
from Gui.CentralControllerPanel import CentralControllerPanel
from Gui.KeypadControllerPanel import KeypadControllerPanel


ID_toolbarKeypadCtrl = 1001
ID_toolbarCentralCtrl = 1002

KeypadCtrlToolbarImg = 'art/icons8-ctrl-48.png'
CentralCtrlToolbarImg = 'art/icons8-motherboard-48.png'


class MainWindow(wx.Frame):

    ## MainWindow class constructor.
    #  @param self The object pointer.
    def __init__(self, config):
        windowWidth = 800
        windowHeight = 600
        title = f"Secure Shed Power Console (Core {VERSION})"
        frameSize = (windowWidth, windowHeight)
        super().__init__(None, title=title, size=frameSize)

        self._config = config

        self._keypadClient = APIEndpointClient(config.keypadController.endpoint)
        self._controllerClient = APIEndpointClient(config.centralController.endpoint)

        self._statusBar = None
        self._toolbar = None

        self.BuildStatusBar()
        self.BuildToolbar()

		# Create Sizer for layout
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)

        # Central Controller Panel
        self._centralControllerPanel = CentralControllerPanel(self)
        self._sizer.Add(self._centralControllerPanel, 1, wx.GROW)

        # Keypad Controller Panel
        self._keypadControllerPanel = KeypadControllerPanel(self)
        self._sizer.Add(self._keypadControllerPanel, 1, wx.GROW)
        self._keypadControllerPanel.Hide()


    def BuildStatusBar(self):
        self._statusBar = self.CreateStatusBar()
        self._statusBar.SetFieldsCount(2)

        keypadStatus = "Keypad: DISCONNECTED"
        self._statusBar.SetStatusText(keypadStatus, 0)

        controllerStatus = "Controller: DISCONNECTED"
        self._statusBar.SetStatusText(controllerStatus, 1)


    def BuildToolbar(self):
        self._toolbar = self.CreateToolBar(wx.TB_HORIZONTAL)
        self._toolbar.SetToolBitmapSize(wx.Size( 48, 48 ))

        keypadCtrlIcon = wx.Bitmap(KeypadCtrlToolbarImg, wx.BITMAP_TYPE_PNG)
        btnKeypad = self._toolbar.AddTool(ID_toolbarKeypadCtrl,
                                          "Keypad Controller", keypadCtrlIcon)

        CentralCtrlIcon = wx.Bitmap(CentralCtrlToolbarImg, wx.BITMAP_TYPE_PNG)
        btnCentral = self._toolbar.AddTool(ID_toolbarCentralCtrl,
                                           "Central Controller",
                                           CentralCtrlIcon)

        self._toolbar.Realize()
