import wx

## https://www.blog.pythonlibrary.org/2019/02/12/creating-a-calculator-with-wxpython/


class CalcPanel(wx.Panel):

    KeySize = 4

    def __init__(self, parent):
        super().__init__(parent)
        self.last_button_pressed = None
        self.create_ui()

        self.__sequence = ''


    def create_ui(self):
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
        
        self.__sequence = self.__sequence + pressedKeyValue

 
    def __ClearKeypad(self, event):
        self.__sequence = ''


    def __CommitCode(self, event):
        print(f"Committing code value of '{self.__sequence}'")


class CalcFrame(wx.Frame):
 
    def __init__(self):
        super().__init__(None, title = "", size = (350, 375))
        panel = CalcPanel(self)
        self.Show()

        #self.ShowFullScreen(True)
        self.Maximize(True)

if __name__ == '__main__':
    app = wx.App(False)
    frame = CalcFrame()
    app.MainLoop()
