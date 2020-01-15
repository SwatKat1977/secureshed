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


## Panel that implements an informational pane stating comms has been lost to
#  to the central controller.
class CommsLostPanel(wx.Frame):

    def __init__(self, config):
        frameSize = (config.gui.windowWidth,
                     config.gui.windowHeight)
        super().__init__(None, title="", size=frameSize)

        self.__config = config

        panel = wx.Panel(self)

        panel.SetBackgroundColour((215, 220, 24))

        mainSizer = wx.GridSizer(1, 1, 5, 5)

        font = wx.Font(18, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_BOLD)
        panelText = wx.StaticText(panel, -1, "Comms lost to central controller")
        panelText.SetFont(font)

        panelText.CenterOnParent()

        mainSizer.Add(panelText, 0,
                      wx.ALL | wx.CENTRE | wx.ALIGN_CENTER_HORIZONTAL |\
                      wx.ALIGN_CENTRE_VERTICAL)
        panel.SetSizer(mainSizer)
