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
from common.Logger import Logger, LogType
from Gui.ConsoleLogsPanelListCtrl import ConsoleLogsPanelListCtrl


class ConsoleLogsPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        topSizer = wx.BoxSizer(wx.HORIZONTAL)

        self._logsList = ConsoleLogsPanelListCtrl(self, style=wx.LC_REPORT)

        topSizer.Add(self._logsList, 1, wx.EXPAND)
        self.SetSizer(topSizer)
        self.Fit()


    def AddLogEntry(self, indexPosition, logLevel, msg):
        logLevelStr = Logger.Instance().LoggerMappings[LogType(logLevel)][0]
        self._logsList.InsertItem(indexPosition, logLevelStr)
        self._logsList.SetItem(indexPosition, 1, msg)
