r'''Control for string word values'''

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl

class StringCtrl(BaseCtrl):
    def init2(self):
        self.t1 = wx.TextCtrl(self, -1, size=(125, -1), pos=(20,0))
        self.Bind(wx.EVT_TEXT, self.TextChange, self.t1)

    def setInitialValue(self):
        print self.question.name, "StringCtrl.setInitialValue", \
              self.answer_getter(), repr(self.answer_getter().get_value())
        self.t1.SetValue(self.answer_getter().get_value())

    def TextChange(self, event):
        print event.GetString()
        self.answer_getter().value = event.GetString()

