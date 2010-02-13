r'''Control for single choice word values'''

from pprint import pprint
import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl

class ChoiceCtrl(BaseCtrl):
    def paintControl(self, parent):
        self.choices = {
            'names': [option[0] for option in self.question.options],
            'values': [option[1] for option in self.question.options],
            'questions': [option[2] for option in self.question.options],
        }
        
        self.ch = wx.Choice(parent, wx.ID_ANY, (0,0), choices=self.choices['names'])
        self.Bind(wx.EVT_CHOICE, self.changed, self.ch)
        
    def setInitialValue(self):
        print 'initial value: %s' % self.answer_getter().get_value()
        # self.ch.SetLabel(self.answer_getter().get_value())
        
    def changed(self, event):
        print self.choices['values'][event.GetInt()]
        # self.answer_getter().value = repr(event.IsChecked())
        # print "IsChecked", self.answer_getter().value