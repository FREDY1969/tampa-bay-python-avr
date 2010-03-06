# bool_ctrl.py

'''Control for boolean questions.'''

import wx
from ucc.gui.controls.base_ctrl import BaseCtrl
from ucc.gui import debug

class BoolCtrl(BaseCtrl):
    def setupControl(self):
        self.checkBox = wx.CheckBox(self)
        self.Bind(wx.EVT_CHECKBOX, self.onChange, self.checkBox)
    
    def setInitialValue(self):
        debug.trace("%s.setInitialValue %s=%s" % 
                    (self.__class__.__name__,
                     self.question.name,
                     self.ans_getter().get_value()))
        self.checkBox.SetValue(self.ans_getter().get_value())
    
    def onChange(self, event):
        self.change(event.IsChecked())
    
