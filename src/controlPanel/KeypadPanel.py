'''
Copyright 2019 Secure Shed Project Dev Team

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


class KeypadPanel(wx.Panel):

    def __init__(self, parent):
        super().__init__(parent)
        
        # Key sequence pressed.
        self.__keySequence = ''
 
        self.__CreateUI()


    def __CreateUI(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        font = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL)

        buttons = [['7', '8', '9'],
                   ['4', '5', '6'],
                   ['1', '2', '3'],
                   ['0', 'GO', 'Reset']]

        for label_list in buttons:
            btn_sizer = wx.BoxSizer()
            for label in label_list:
                button = wx.Button(self, label=label)
                btn_sizer.Add(button, 1, wx.ALIGN_CENTER|wx.EXPAND, 0)

                if label == 'GO':
                    button.Bind(wx.EVT_BUTTON, self.__CommitCode)

                elif label == 'Reset':
                    button.Bind(wx.EVT_BUTTON, self.__ClearKeypad)

                else:
                    button.Bind(wx.EVT_BUTTON, self.__PressKey)

            main_sizer.Add(btn_sizer, 1, wx.ALIGN_CENTER|wx.EXPAND)

        self.SetSizer(main_sizer)


    def __PressKey(self, event):
        pressedKey = event.GetEventObject()
        pressedKeyValue = pressedKey.GetLabel()
        
        self.__keySequence = self.__keySequence + pressedKeyValue
        print(f'Pressed key : {pressedKeyValue}')

 
    def __ClearKeypad(self, event):
        self.__keySequence = ''


    def __CommitCode(self, event):
        print(f"Committing code value of '{self.__keySequence}'")
