'''Control for rational word values'''

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl
from ucc.gui import debug

class RationalCtrl(BaseCtrl):
    def __init__(self, *args, **kwargs):
        super(RationalCtrl, self).__init__(*args, **kwargs)
    
    def setupControl(self):
        self.textCtrlNum = wx.TextCtrl(self, size=(250, -1))
        self.slash = wx.StaticText(self, label=" / ")
        self.textCtrlDen = wx.TextCtrl(self, size=(250, -1))
        self.Bind(wx.EVT_TEXT, self.onChange, self.textCtrlNum)
        self.Bind(wx.EVT_TEXT, self.onChange, self.textCtrlDen)
    
    def setInitialValue(self):
        debug.trace("%s.setInitialValue %s=%s" % 
                    (self.__class__.__name__,
                     self.question.name,
                     self.answer_getter().get_value()))
        # self.textCtrl.ChangeValue(self.answer_getter().get_value())
    
    def onChange(self, event):
        debug.notice("Text changed: %s" % event.GetString())
        # self.answer_getter().value = event.GetString()
    
