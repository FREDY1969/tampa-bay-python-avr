# base_ctrl.py

'''Base class for question controls.'''

import wx
from ucc.gui import registry, debug

class BaseCtrl(wx.Panel):
    def __init__(self, parent, question, ans_getter, ans_setter):
        super(BaseCtrl, self).__init__(parent)
        debug.trace("{}.__init__".format(self.__class__.__name__))
        
        self.parent = parent
        self.question = question
        self.ans_getter = ans_getter
        self.ans_setter = ans_setter
        
        self.setupControl()
    
    def setupControl(self):
        raise NotImplementedError("Derived control class must implement " \
                                  "setupControl method.")
    
    def setInitialValue(self):
        raise NotImplementedError("Derived control class must implement " \
                                  "setInitialValue method.")
    
    def change(self, value):
        registry.currentWord.set_save_state(False)
        self.ans_getter().value = str(value)
        debug.notice("{} changed: {}".format(self.__class__.__name__, value))
    
    @classmethod
    def makeControl(cls, parent, question, ans_getter, ans_setter):
        r'''Called when question might be optional or repeatable.
        
        The standard class constructor is only called when the question is not
        optional or repeatable (or these aspects are being handled by another
        control).
        
        '''
        
        if question.is_optional():
            ctrl = OptionalCtrl(cls, parent, question, ans_getter,
                                ans_setter)
        elif question.is_repeatable():
            ctrl = RepeatableCtrl(cls, parent, question, ans_getter, 
                                  ans_setter)
        else:
            ctrl = cls(parent, question, ans_getter, ans_setter)
        ctrl.setInitialValue()
        return ctrl
    

from ucc.gui.controls.optional_ctrl import OptionalCtrl
from ucc.gui.controls.repeatable_ctrl import RepeatableCtrl
