import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin


class ConsoleLogsPanelListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent, style=0):
        wx.ListCtrl.__init__(self, parent, style=style)
        ListCtrlAutoWidthMixin.__init__(self)

        self.InsertColumn(0, 'Log Level', width=150)
        self.InsertColumn(1, 'Message')

        self.setResizeColumn('LAST')
