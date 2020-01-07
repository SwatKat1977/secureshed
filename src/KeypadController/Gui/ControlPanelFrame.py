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
import multiprocessing
import queue
import wx
from KeypadController.Gui.KeypadPanel import KeypadPanel
from KeypadController.Gui.LockedPanel import LockedPanel
from KeypadController.Gui.CommsLostPanel import CommsLostPanel
from KeypadController.KeypadStateObject import KeypadStateObject


class ControlPanelFrame(wx.Frame):
    # pylint: disable=R0901
    # pylint: disable=R0903


    #  @param self The object pointer.
    def __init__(self, configuration, frameSize, processingQueue):
        # pylint: disable=W0612
        super().__init__(None, title="", size=frameSize)

        self.__processingQueue = processingQueue

        self.__currentPanelSel = self.__processingQueue.get(timeout=0.05)

        self.__keypadPanel = KeypadPanel(self, configuration)
        self.__keypadPanel.Hide()

        self.__keypadLockedPanel = LockedPanel(self)
        self.__keypadLockedPanel.Hide()

        self.__commsLostPanel = CommsLostPanel(self)
        self.__commsLostPanel.Hide()

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.__sizer.Add(self.__keypadPanel, 1, wx.EXPAND)
        self.__sizer.Add(self.__keypadLockedPanel, 1, wx.EXPAND)
        self.__sizer.Add(self.__commsLostPanel, 1, wx.EXPAND)
        self.SetSizer(self.__sizer)

        self.__DisplayPanel()

        if configuration.gui.fullscreen:
            self.ShowFullScreen(True)
            self.Maximize(True)

        self.__panelCheckimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.__CheckPanel, self.__panelCheckimer)
        self.__panelCheckimer.Start(1000)


    #  @param self The object pointer.
    def __CheckPanel(self, event):
        # pylint: disable=W0613

        try:
            retrievedCurPanel = self.__processingQueue.get(timeout=0.05)

        except queue.Empty:
            return

        if self.__currentPanelSel != retrievedCurPanel:
            self.__currentPanelSel = retrievedCurPanel
            self.__DisplayPanel()


    #  @param self The object pointer.
    def __DisplayPanel(self):
        self.__commsLostPanel.Hide()
        self.__keypadPanel.Hide()
        self.__keypadLockedPanel.Hide()

        panel, _ = self.__currentPanelSel
        print(panel)

        if panel == KeypadStateObject.PanelType.KeypadIsLocked:
            self.__keypadLockedPanel.Show()

        elif panel == KeypadStateObject.PanelType.CommunicationsLost:
            self.__commsLostPanel.Show()

        elif panel == KeypadStateObject.PanelType.Keypad:
            self.__keypadPanel.Show()

        self.__sizer.Layout()
