r'''Control for integer word values'''

import wx
from ucc.gui.controls import BaseCtrl

class IntegerCtrl(BaseCtrl.BaseCtrl):
    def paintControl(self, parent):
        self.sc = wx.SpinCtrl(self, -1, "", (30, 50))
        self.sc.SetValue(self.answer.get_value())
        self.Bind(wx.EVT_SPINCTRL, self.OnSpin, self.sc)
    
    def OnSpin(self, event):
        self.answer.value(self.sc.GetValue())
    
