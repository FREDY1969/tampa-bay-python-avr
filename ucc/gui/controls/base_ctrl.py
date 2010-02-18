# base_ctrl.py

'''Base class for question controls.'''

import wx
from ucc.gui import debug

class BaseCtrl(wx.Panel):
    def __init__(self, parent, question, word):
        super(BaseCtrl, self).__init__(parent)
        debug.trace("%s.__init__" % self.__class__.__name__)
        
        self.parent = parent
        self.question = question
        self.word = word
        self.get_answer = lambda: word.get_value(question.name)
        self.set_answer = lambda ans: word.set_answer(question.name, ans)
        
        self.setupControl()
        self.setInitialValue()
        
    def setupControl():
        raise NotImplementedError("Derived control class must implement " \
                                  "setupControl method.")
    
    def setInitialValue():
        raise NotImplementedError("Derived control class must implement " \
                                  "setInitialValue method.")
    
    @classmethod
    def makeControl(cls, parent, question, word):
        r'''Called when question might be optional or repeatable.
        
        The standard class constructor is only called when the question is not
        optional or repeatable (or these aspects are being handled by another
        control).
        
        '''
        
        if question.is_optional():
            return OptionalCtrl(cls, parent, question, word)
        if question.is_repeatable():
            return RepeatableCtrl(cls, parent, question, word)
        return cls(parent, question, word)
    

from ucc.gui.controls.optional_ctrl import OptionalCtrl
from ucc.gui.controls.repeatable_ctrl import RepeatableCtrl
