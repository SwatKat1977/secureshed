"""
Copyright 2019-2024 Secure Shed Project Dev Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin


class ConsoleLogsPanelListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent, style=0):
        wx.ListCtrl.__init__(self, parent, style=style)
        ListCtrlAutoWidthMixin.__init__(self)

        self.InsertColumn(0, 'Log Level', width=150)
        self.InsertColumn(1, 'Message')

        self.setResizeColumn('LAST')
