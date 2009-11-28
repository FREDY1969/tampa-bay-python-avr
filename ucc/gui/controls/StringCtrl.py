r'''Control for string word values'''

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl

class StringCtrl(BaseCtrl):
    def paintControl(self, parent):
        self.t1 = wx.TextCtrl(self, -1, size=(125, -1))
        self.Bind(wx.EVT_TEXT, self.TextChange, self.t1)
        
    def setInitialValue():
        self.t1.SetValue(self.answer_getter())
    
    def TextChange(self, event):
        print event.GetString()
        self.answer_setter(event.GetString())