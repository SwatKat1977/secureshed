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
from Gui.MainWindowTab import MainWindowTab


class MainWindowNotebook(wx.Notebook):

    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, id=wx.ID_ANY,
                             style=wx.BK_DEFAULT)

        # Create the first tab and add it to the notebook
        tabOne = MainWindowTab(self)
        tabOne.SetBackgroundColour("Gray")
        self.AddPage(tabOne, "TabOne")

        # Create and add the second tab
        tabTwo = MainWindowTab(self)
        self.AddPage(tabTwo, "TabTwo")

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.OnPageChanging)

    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        print(f'OnPageChanged,  old: {old}, new:{new}, sel:{sel}')
        event.Skip()

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        print(f'OnPageChanging,  old: {old}, new:{new}, sel:{sel}')
        event.Skip()
