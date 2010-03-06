# string_ctrl.py

'''Control for string questions.'''

import wx
from ucc.gui.controls.base_ctrl import BaseCtrl
from ucc.gui import registry, debug

class StringCtrl(BaseCtrl):
    def setupControl(self):
        self.textCtrl = wx.TextCtrl(self, size=(250, -1))
        self.Bind(wx.EVT_TEXT, self.onChange, self.textCtrl)
    
    def setInitialValue(self):
        debug.trace("%s.setInitialValue %s=%s" % 
                    (self.__class__.__name__,
                     self.question.name,
                     self.ans_getter().value))
        self.textCtrl.ChangeValue(self.ans_getter().value)
    
    def onChange(self, event):
        self.change(event.GetString())
    
