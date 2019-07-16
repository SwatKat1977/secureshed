import wx
from KeypadPanel import KeypadPanel


class CalcFrame(wx.Frame):
 
    def __init__(self):
        super().__init__(None, title = "", size = (350, 375))
        panel = KeypadPanel(self)
        self.Show()

        #self.ShowFullScreen(True)
        #self.Maximize(True)

if __name__ == '__main__':
    app = wx.App(False)
    frame = CalcFrame()
    app.MainLoop()
