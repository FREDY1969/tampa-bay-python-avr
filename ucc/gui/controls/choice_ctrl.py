# choice_ctrl.py

'''Control for single choice questions.'''

import wx
from ucc.gui.controls.base_ctrl import BaseCtrl
from ucc.gui import debug

class ChoiceCtrl(BaseCtrl):
    def setupControl(self):
        self.choices = {
            'names': [option[0] for option in self.question.options],
            'values': [option[1] for option in self.question.options],
            'questions': [option[2] for option in self.question.options],
        }
        
        self.ch = wx.Choice(self, choices=self.choices['names'])
        self.Bind(wx.EVT_CHOICE, self.onChange, self.ch)
    
    def setInitialValue(self):
        debug.trace("%s.setInitialValue %s=%s" % 
                    (self.__class__.__name__,
                     self.question.name,
                     self.get_value()))
        self.ch.SetLabel(self.get_value())
    
    def onChange(self, event):
        debug.notice("Choice changed: %s" % self.choices['values'][event.GetSelection()])
        self.set_value(str(event.GetInt()))
    
