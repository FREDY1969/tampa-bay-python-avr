r'''Control for single choice word values'''

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl
from ucc.gui import debug

class ChoiceCtrl(BaseCtrl):
    def __init__(self, *args, **kwargs):
        super(ChoiceCtrl, self).__init__(*args, **kwargs)
    
    def setupControl(self):
        self.choices = {
            'names': [option[0] for option in self.question.options],
            'values': [option[1] for option in self.question.options],
            'questions': [option[2] for option in self.question.options],
        }
        
        self.ch = wx.Choice(self, choices=self.choices['names'])
        self.Bind(wx.EVT_CHOICE, self.onChange, self.ch)
    
    def setInitialValue(self):
        pass
        # debug.trace("%s.setInitialValue %s=%s" % 
        #             (self.__class__.__name__,
        #              self.question.name,
        #              self.answer_getter().get_value()))
        # self.ch.SetLabel(self.answer_getter().get_value())
    
    def onChange(self, event):
        debug.notice("Choice changed: %s" % self.choices['values'][event.GetSelection()])
        # self.answer_getter().value = event.GetInt()
    
