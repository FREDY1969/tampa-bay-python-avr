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
                     self.get_answer()))
        self.checkBox.SetValue(self.get_answer())
    
    def onChange(self, event):
        debug.notice("Checkbox clicked: %s" % event.IsChecked())
        self.get_answer().value = repr(event.IsChecked())
    
