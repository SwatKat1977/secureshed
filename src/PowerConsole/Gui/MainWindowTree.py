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
import enum
import wx

class TreeElementType(enum.Enum):
    DoNotProcess = 0
    CentralCtrlConfig = 1
    CentralCtrlLogs = 2
    KeypadCtrlConfig = 3
    KeypadCtrlLogs = 4

class MainWindowTree(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)

        sizer = wx.BoxSizer(wx.VERTICAL)

        treeSize = (-1, -1)
        treeStyle = wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS
        self._tree = wx.TreeCtrl(parent=self, size=treeSize, style=treeStyle)

        treeRoot = self._tree.AddRoot('Component')

        centralCtrl = self._tree.AppendItem(treeRoot, 'Central Controller',
                                            data=TreeElementType.DoNotProcess)
        self._tree.AppendItem(centralCtrl, 'Configuration',
                              data=TreeElementType.CentralCtrlConfig)
        self._tree.AppendItem(centralCtrl, 'Console Logs',
                              data=TreeElementType.CentralCtrlLogs)
        keypadCtrl = self._tree.AppendItem(treeRoot, 'Keypad Controller',
                                           data=TreeElementType.DoNotProcess)
        self._tree.AppendItem(keypadCtrl, 'Configuration',
                              data=TreeElementType.KeypadCtrlConfig)
        self._tree.AppendItem(keypadCtrl, 'Console Logs',
                              data=TreeElementType.KeypadCtrlLogs)

        sizer.Add(self._tree, 1, wx.EXPAND)

        self.SetSizer(sizer)

        self._tree.Bind(wx.EVT_TREE_SEL_CHANGED, self._OnSelChanged)


    def _OnSelChanged(self, event):
        item = event.GetItem()
        itemData = self._tree.GetItemData(item)
        print(f'OnPageChanged() {itemData}')
