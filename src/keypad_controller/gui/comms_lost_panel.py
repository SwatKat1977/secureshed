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
from twisted.internet import reactor


## Panel that implements an informational pane stating comms has been lost to
#  to the central controller.
class CommsLostPanel(wx.Frame):
    # pylint: disable=too-few-public-methods

    def __init__(self, config):
        frame_size = (config.gui.windowWidth,
                     config.gui.windowHeight)
        super().__init__(None, title="", size=frame_size)

        self._config = config

        panel = wx.Panel(self)

        panel.SetBackgroundColour((215, 220, 24))

        main_sizer = wx.GridSizer(1, 1, 5, 5)

        font = wx.Font(18, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_BOLD)
        panel_text = wx.StaticText(panel, -1, "Comms lost to central controller")
        panel_text.SetFont(font)

        panel_text.CenterOnParent()

        main_sizer.Add(panel_text, 0,
                       wx.ALL | wx.CENTRE | wx.ALIGN_CENTER_HORIZONTAL |\
                       wx.ALIGN_CENTRE_VERTICAL)
        panel.SetSizer(main_sizer)

        # make sure reactor.stop() is used to stop event loop
        self.Bind(wx.EVT_CLOSE, self._on_exit)


    def display(self):
        self.Show()
        if self._config.gui.fullscreen:
            self.ShowFullScreen(True)
            self.Maximize(True)


    ## Exit event function when the application is closed.
    #  @param self The object pointer.
    #  @param event Unused, but required.
    def _on_exit(self, event):
        # pylint: disable=R0201
        # pylint: disable=W0613
        reactor.stop()
