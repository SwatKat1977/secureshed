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
from common.Version import VERSION, COPYRIGHT
from Gui.MainWindowTree import MainWindowTree
from Gui.ConsoleLogsPanel import ConsoleLogsPanel


class MainWindow(wx.Frame):

    ## MainWindow class constructor.
    #  @param self The object pointer.
    def __init__(self):
        windowWidth = 800
        windowHeight = 600

        title = f"Secure Shed Power Console (Core {VERSION})"
        frameSize = (windowWidth, windowHeight)
        super().__init__(None, title=title, size=frameSize)

        splitter = wx.SplitterWindow(self)
        leftP = MainWindowTree(splitter)
        rightP = ConsoleLogsPanel(splitter)

        # split the window
        splitter.SplitVertically(leftP, rightP)
        splitter.SetMinimumPaneSize(20)
        self.Centre()
