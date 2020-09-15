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
import time
import wx
from common.Version import VERSION
from Gui.central_controller_panel import CentralControllerPanel
from Gui.keypad_controller_panel import KeypadControllerPanel
from worker_thread import WorkerThread


ID_TOOLBAR_KEYPAD_CTRL = 1001
ID_TOOLBAR_CENTRAL_CTRL = 1002

KEYPAD_CTRL_TOOLBAR_IMG = 'art/icons8-ctrl-48.png'
CENTRAL_CTRL_TOOLBAR_IMG = 'art/icons8-motherboard-48.png'


class MainWindow(wx.Frame):
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    ## Enumeration for current page selected.
    class PageSelection(enum.Enum):
        CentralControllerPanel = 0
        KeypadControllerPanel = 1


    ## MainWindow class constructor.
    #  @param self The object pointer.
    #  @param config Instance of a configuration object.
    def __init__(self, config):
        window_width = 800
        window_height = 600
        title = f"Secure Shed Power Console (Core {VERSION})"
        frame_size = (window_width, window_height)
        super().__init__(None, title=title, size=frame_size)

        self._config = config
        self._curr_page = self.PageSelection.CentralControllerPanel

        self._status_bar = None
        self._toolbar = None

        self._build_status_bar()
        self._build_toolbar()

        # Create Sizer for layout
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)

        # Central Controller Panel
        self._central_controller_panel = CentralControllerPanel(self, config)
        self._sizer.Add(self._central_controller_panel, 1, wx.GROW)

        # Keypad Controller Panel
        self._keypad_controller_panel = KeypadControllerPanel(self, config)
        self._keypad_controller_panel.Hide()

        self._worker_thread = WorkerThread(self._keypad_controller_panel,
                                           self._central_controller_panel)
        self._worker_thread.start()

        self.Bind(wx.EVT_CLOSE, self._on_close)


    def update_keypad_status(self, new_state_str):
        keypad_status = f"Keypad: {new_state_str}"
        self._status_bar.SetStatusText(keypad_status, 0)


    #  @param self The object pointer.
    def _build_status_bar(self):
        self._status_bar = self.CreateStatusBar()
        self._status_bar.SetFieldsCount(2)

        keypad_status = "Keypad: DISCONNECTED"
        self._status_bar.SetStatusText(keypad_status, 0)

        controller_status = "Controller: DISCONNECTED"
        self._status_bar.SetStatusText(controller_status, 1)


    #  @param self The object pointer.
    def _build_toolbar(self):
        self._toolbar = self.CreateToolBar(wx.TB_HORIZONTAL)
        self._toolbar.SetToolBitmapSize(wx.Size(48, 48))

        keypad_ctrl_icon = wx.Bitmap(KEYPAD_CTRL_TOOLBAR_IMG, wx.BITMAP_TYPE_PNG)
        btn_keypad = self._toolbar.AddTool(ID_TOOLBAR_KEYPAD_CTRL,
                                           "Keypad Controller", keypad_ctrl_icon)

        central_ctrl_icon = wx.Bitmap(CENTRAL_CTRL_TOOLBAR_IMG, wx.BITMAP_TYPE_PNG)
        btn_central = self._toolbar.AddTool(ID_TOOLBAR_CENTRAL_CTRL,
                                            "Central Controller",
                                            central_ctrl_icon)

        # Bind toolbar events
        self.Bind(wx.EVT_TOOL, self._on_central_controller_click, btn_central)
        self.Bind(wx.EVT_TOOL, self._on_keypad_controller_click, btn_keypad)

        self._toolbar.Realize()


    #  @param self The object pointer.
    #  @param event Unused.
    def _on_central_controller_click(self, event):

        #  If current page is same as what is selected then do nothing.
        if self._curr_page == self.PageSelection.CentralControllerPanel:
            return

        # Detach current page.
        self._sizer.Detach(0)

        # If the current page is 'Keypad' then hide it.
        if self._curr_page == self.PageSelection.KeypadControllerPanel:
            self._keypad_controller_panel.Hide()

        # Add the Test Plan panel to the sizer control.
        self._sizer.Prepend(self._central_controller_panel, 1, wx.GROW)

        # Set the Central Controller Panel to be displayed.
        self._central_controller_panel.Show()

        # Set the current activate page
        self._curr_page = self.PageSelection.CentralControllerPanel

        # Update the sizer control and refresh.
        self._sizer.Layout()
        self._central_controller_panel.Refresh()


    #  @param self The object pointer.
    #  @param event Unused.
    def _on_keypad_controller_click(self, event):

        #  If current page is same as what is selected then do nothing.
        if self._curr_page == self.PageSelection.KeypadControllerPanel:
            return

        # Detach current page.
        self._sizer.Detach(0)

        # If the current page is 'Central Controller' then hide it.
        if self._curr_page == self.PageSelection.CentralControllerPanel:
            self._central_controller_panel.Hide()

        # Add the Keypad Controller panel to the sizer control.
        self._sizer.Prepend(self._keypad_controller_panel, 1, wx.GROW)

        # Set the Keypad Controller Panel to be displayed.
        self._keypad_controller_panel.Show()

        # Set the current activate page
        self._curr_page = self.PageSelection.KeypadControllerPanel

        # Update the sizer control and refresh.
        self._sizer.Layout()
        self._keypad_controller_panel.Refresh()


    # Event when the main dialog is closed.  Ensure that the update timer is
    # stopped.
    #  @param self The object pointer.
    #  @param event Required, but not used.
    def _on_close(self, event):
        self._worker_thread.request_shutdown()

        while not self._worker_thread.shutdown_completed:
            time.sleep(1)

        self.Destroy()
