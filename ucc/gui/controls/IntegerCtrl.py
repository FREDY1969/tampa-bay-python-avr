r'''Control for integer word values'''

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl

class IntegerCtrl(BaseCtrl):
    def paintControl(self, parent):
        self.sc = wx.SpinCtrl(parent, -1, name=self.question.name, pos=(20,0))
        self.sc.SetValue(self.answer.get_value())
        self.Bind(wx.EVT_SPINCTRL, self.OnSpin, self.sc)
    
    def OnSpin(self, event):
        self.answer.value(self.sc.GetValue())
    
