# string_ctrl.py

'''Control for string questions.'''

import wx
from ucc.gui.controls.base_ctrl import BaseCtrl
from ucc.gui import debug

class StringCtrl(BaseCtrl):
    def setupControl(self):
        self.textCtrl = wx.TextCtrl(self, size=(250, -1))
        self.Bind(wx.EVT_TEXT, self.onChange, self.textCtrl)
    
    def setInitialValue(self):
        debug.trace("%s.setInitialValue %s=%s" % 
                    (self.__class__.__name__,
                     self.question.name,
                     self.get_answer()))
        self.textCtrl.ChangeValue(self.get_answer())
    
    def onChange(self, event):
        debug.notice("Text changed: %s" % event.GetString())
        self.get_answer().value = event.GetString()
    
