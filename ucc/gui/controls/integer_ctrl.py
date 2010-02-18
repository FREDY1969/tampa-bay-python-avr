# integer_ctrl.py

'''Control for integer questions.'''

import wx
from ucc.gui.controls.base_ctrl import BaseCtrl
from ucc.gui import debug

class IntegerCtrl(BaseCtrl):
    def setupControl(self):
        self.spinCtrl = wx.SpinCtrl(self)
        self.Bind(wx.EVT_SPINCTRL, self.onChange, self.spinCtrl)
    
    def setInitialValue(self):
        debug.trace("%s.setInitialValue %s=%s" % 
                    (self.__class__.__name__,
                     self.question.name,
                     self.get_answer()))
        self.spinCtrl.SetValue(self.get_answer())
    
    def onChange(self, event):
        debug.notice("Int changed: %s" % event.GetInt())
        self.set_answer(event.GetInt())
    
