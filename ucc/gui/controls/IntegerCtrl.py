r'''Control for integer word values'''

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl
from ucc.gui import debug

class IntegerCtrl(BaseCtrl):
    def __init__(self, *args, **kwargs):
        super(IntegerCtrl, self).__init__(*args, **kwargs)
    
    def setupControl(self):
        self.spinCtrl = wx.SpinCtrl(self)
        self.Bind(wx.EVT_SPINCTRL, self.onChange, self.spinCtrl)
    
    def setInitialValue(self):
        debug.trace("%s.setInitialValue %s=%s" % 
                    (self.__class__.__name__,
                     self.question.name,
                     self.answer_getter().get_value()))
        self.spinCtrl.SetValue(self.answer_getter().get_value())
    
    def onChange(self, event):
        debug.notice("Int changed: %s" % event.GetInt())
        self.answer_getter().value = str(event.GetInt())
    
