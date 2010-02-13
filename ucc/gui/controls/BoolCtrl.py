r'''Control for boolean word values'''

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl
from ucc.gui import debug

class BoolCtrl(BaseCtrl):
    def __init__(self, *args, **kwargs):
        super(BoolCtrl, self).__init__(*args, **kwargs)
    
    def setupControl(self):
        self.checkBox = wx.CheckBox(self)
        self.Bind(wx.EVT_CHECKBOX, self.onChange, self.checkBox)
    
    def setInitialValue(self):
        debug.trace("%s.setInitialValue %s=%s" % 
                    (self.__class__.__name__,
                     self.question.name,
                     self.answer_getter().get_value()))
        self.checkBox.SetValue(self.answer_getter().get_value())
    
    def onChange(self, event):
        debug.notice("Checkbox clicked: %s" % event.IsChecked())
        self.answer_getter().value = repr(event.IsChecked())
    
