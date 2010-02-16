'''Control for real word values'''

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl
from ucc.gui import debug

class RealCtrl(BaseCtrl):
    def __init__(self, *args, **kwargs):
        super(RealCtrl, self).__init__(*args, **kwargs)
    
    def setupControl(self):
        self.textCtrl = wx.TextCtrl(self, size=(250, -1))
        self.Bind(wx.EVT_TEXT, self.onChange, self.textCtrl)
    
    def setInitialValue(self):
        debug.trace("%s.setInitialValue %s=%s" % 
                    (self.__class__.__name__,
                     self.question.name,
                     self.answer_getter().get_value()))
        self.textCtrl.ChangeValue(self.answer_getter().get_value())
    
    def onChange(self, event):
        debug.notice("Text changed: %s" % event.GetString())
        self.answer_getter().value = event.GetString()
    
