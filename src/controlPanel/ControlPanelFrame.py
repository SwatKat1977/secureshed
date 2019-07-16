import wx
from KeypadPanel import KeypadPanel


class ControlPanelFrame(wx.Frame):
 
    def __init__(self):
        super().__init__(None, title = "", size = (350, 375))
        panel = KeypadPanel(self)
        self.Show()

        #self.ShowFullScreen(True)
        #self.Maximize(True)
