r'''Control for boolean word values'''

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl

class BoolCtrl(BaseCtrl):
    def init2(self):
        self.cb = wx.CheckBox(self, wx.ID_ANY, self.label)
        self.Bind(wx.EVT_CHECKBOX, self.checked, self.cb)
    
    def setInitialValue(self):
        self.cb.SetValue(self.answer_getter().get_value())

    def checked(self, event):
        self.answer_getter().value = repr(event.IsChecked())
        print "IsChecked", self.answer_getter().value

