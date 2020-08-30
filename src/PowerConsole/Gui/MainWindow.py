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
#pylint: disable=unused-argument
import enum
import wx
from common.Version import VERSION, COPYRIGHT
from Gui.ConsoleLogsPanel import ConsoleLogsPanel
from Gui.CentralControllerPanel import CentralControllerPanel
from Gui.KeypadControllerPanel import KeypadControllerPanel


ID_toolbarKeypadCtrl = 1001
ID_toolbarCentralCtrl = 1002

KeypadCtrlToolbarImg = 'art/icons8-ctrl-48.png'
CentralCtrlToolbarImg = 'art/icons8-motherboard-48.png'


class MainWindow(wx.Frame):

    # Event ID's for main dialog.
    EventID_updateTimer = 0x100

    # Update timer interval.
    UpdateTimerInterval = 2000

    ## Enumeration for current page selected.
    class PageSelection(enum.Enum):
        CentralControllerPanel = 0
        KeypadControllerPanel = 1


    ## MainWindow class constructor.
    #  @param self The object pointer.
    #  @param config Instance of a configuration object.
    def __init__(self, config):
        windowWidth = 800
        windowHeight = 600
        title = f"Secure Shed Power Console (Core {VERSION})"
        frameSize = (windowWidth, windowHeight)
        super().__init__(None, title=title, size=frameSize)

        self._config = config
        self._currPage = self.PageSelection.CentralControllerPanel

        self._statusBar = None
        self._toolbar = None

        self.BuildStatusBar()
        self.BuildToolbar()

        # Create Sizer for layout
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)

        # Central Controller Panel
        self._centralControllerPanel = CentralControllerPanel(self, config)
        self._sizer.Add(self._centralControllerPanel, 1, wx.GROW)

        # Keypad Controller Panel
        self._keypadControllerPanel = KeypadControllerPanel(self, config)
        self._keypadControllerPanel.Hide()

        # Create update timer
        self._updateTimer = wx.Timer(self, id = self.EventID_updateTimer)
        self._updateTimer.Start(self.UpdateTimerInterval, wx.TIMER_CONTINUOUS)

        # ----------------
        #  Bind events to functions
        #  ----------------
        self.Bind(wx.EVT_TIMER, self.OnTimerTick)
        self.Bind(wx.EVT_CLOSE, self.OnCloseApplication)


    #  @param self The object pointer.
    def BuildStatusBar(self):
        self._statusBar = self.CreateStatusBar()
        self._statusBar.SetFieldsCount(2)

        keypadStatus = "Keypad: DISCONNECTED"
        self._statusBar.SetStatusText(keypadStatus, 0)

        controllerStatus = "Controller: DISCONNECTED"
        self._statusBar.SetStatusText(controllerStatus, 1)


    #  @param self The object pointer.
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

        # Bind toolbar events
        self.Bind(wx.EVT_TOOL, self.OnCentralControllerClick, btnCentral)
        self.Bind(wx.EVT_TOOL, self.OnKeypadControllerClick, btnKeypad)

        self._toolbar.Realize()


    #  @param self The object pointer.
    #  @param event Unused.
    def OnCentralControllerClick(self, event):

        #  If current page is same as what is selected then do nothing.
        if self._currPage == self.PageSelection.CentralControllerPanel:
            return

        # Detach current page.
        self._sizer.Detach(0)

        # If the current page is 'Keypad' then hide it.
        if self._currPage == self.PageSelection.KeypadControllerPanel:
            self._keypadControllerPanel.Hide()

        # Add the Test Plan panel to the sizer control.
        self._sizer.Prepend(self._centralControllerPanel, 1, wx.GROW)

        # Set the Central Controller Panel to be displayed.
        self._centralControllerPanel.Show()

        # Set the current activate page
        self._currPage = self.PageSelection.CentralControllerPanel

        # Update the sizer control and refresh.
        self._sizer.Layout()
        self._centralControllerPanel.Refresh()


    #  @param self The object pointer.
    #  @param event Unused.
    def OnKeypadControllerClick(self, event):

        #  If current page is same as what is selected then do nothing.
        if self._currPage == self.PageSelection.KeypadControllerPanel:
            return

        # Detach current page.
        self._sizer.Detach(0)

        # If the current page is 'Central Controller' then hide it.
        if self._currPage == self.PageSelection.CentralControllerPanel:
            self._centralControllerPanel.Hide()

        # Add the Keypad Controller panel to the sizer control.
        self._sizer.Prepend(self._keypadControllerPanel, 1, wx.GROW)

        # Set the Keypad Controller Panel to be displayed.
        self._keypadControllerPanel.Show()

        # Set the current activate page
        self._currPage = self.PageSelection.KeypadControllerPanel

        # Update the sizer control and refresh.
        self._sizer.Layout()
        self._keypadControllerPanel.Refresh()


    # Event when the timer ticks, the panels are updated.
    #  @param self The object pointer.
    #  @param event Required, but not used.
    def OnTimerTick(self, event):
        self._keypadControllerPanel.GetLogs()
        self._centralControllerPanel.GetLogs()


    # Event when the main dialog is closed.  Ensure that the update timer is
    # stopped.
    #  @param self The object pointer.
    #  @param event Required, but not used.
    def OnCloseApplication(self, event):
        self._updateTimer.Stop()
        self.Destroy()
