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
from Gui.console_logs_panel_list_ctrl import ConsoleLogsPanelListCtrl


class ConsoleLogsPanel(wx.Panel):
    # pylint: disable=too-few-public-methods

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        top_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._logs_list = ConsoleLogsPanelListCtrl(self, style=wx.LC_REPORT)

        top_sizer.Add(self._logs_list, 1, wx.EXPAND)
        self.SetSizer(top_sizer)
        self.Fit()


    def add_log_entry(self, index_position, log_level, msg):
        log_level_str = Logger.LoggerMappings[LogType(log_level)][0]
        self._logs_list.InsertItem(index_position, log_level_str)
        self._logs_list.SetItem(index_position, 1, msg)
