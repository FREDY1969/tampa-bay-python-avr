# integer_ctrl.py

'''Control for integer questions.'''

import wx
from ucc.gui.controls.base_ctrl import BaseCtrl
from ucc.gui import registry, debug

class IntegerCtrl(BaseCtrl):
    def setupControl(self):
        self.spinCtrl = wx.SpinCtrl(self)
        self.Bind(wx.EVT_SPINCTRL, self.onChange, self.spinCtrl)
    
    def setInitialValue(self):
        debug.trace("{}.setInitialValue {}={}"
                      .format(self.__class__.__name__,
                              self.question.name,
                              self.ans_getter().get_value()))
        self.spinCtrl.SetValue(self.ans_getter().get_value())
    
    def onChange(self, event):
        self.change(event.GetInt())
    
