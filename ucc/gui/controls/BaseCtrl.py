# BaseCtrl.py

import wx
from ucc.gui import debug

class BaseCtrl(wx.Panel):
    def __init__(self, parent, question, answer_getter, answer_setter):
        super(BaseCtrl, self).__init__(parent)
        debug.trace("%s.__init__" % self.__class__.__name__)
        
        self.parent = parent
        self.question = question
        self.answer_getter = answer_getter
        self.answer_setter = answer_setter
        
        self.setupControl()
        self.setInitialValue()
    
    @classmethod
    def makeControl(cls, parent, question, answer_getter, answer_setter):
        r'''Called when question might be optional or repeatable.
        
        The standard class constructor is only called when the question is not
        optional or repeatable (or these aspects are being handled by another
        control).
        '''
        if question.is_optional():
            return OptionalCtrl(cls, parent, question, \
                                answer_getter, answer_setter)
        if question.is_repeatable():
            return RepeatableCtrl(cls, parent, question, \
                                  answer_getter, answer_setter)
        return cls(parent, question, answer_getter, answer_setter)
    
from ucc.gui.controls.OptionalCtrl import OptionalCtrl
# from ucc.gui.controls.RepeatableCtrl import RepeatableCtrl
