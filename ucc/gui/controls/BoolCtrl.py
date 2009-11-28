r'''Control for boolean word values'''

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl

class BoolCtrl(BaseCtrl):
    def paintControl(self, parent):
        cb = wx.CheckBox(parent, wx.ID_ANY, self.label)
        cb.SetValue(self.answer.get_value())
        self.Bind(wx.EVT_CHECKBOX, self.checked, cb)
    
    def checked(self, event):
        self.answer.value = repr(event.IsChecked())
        print "IsChecked", self.answer.value

