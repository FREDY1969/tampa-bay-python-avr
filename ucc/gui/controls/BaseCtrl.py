# BaseCtrl.py

import wx

class BaseCtrl(wx.Panel):
    def __init__(self, parent, question, answer_getter, answer_setter):
        super(BaseCtrl, self).__init__(parent, wx.ID_ANY)
        print self.__class__.__name__, "__init__"

        self.parent = parent
        self.question = question
        self.answer_getter = answer_getter
        self.answer_setter = answer_setter

        self.init2()

    @classmethod
    def makeControl(cls, parent, question, answer_getter, answer_setter):
        r'''Called when question might be optional or repeatable.

        The standard class constructor is only called when the question is not
        optional or repeatable (or these aspects are being handled by another
        control).
        '''
        if question.is_optional():
            return OptionalCtrl(parent, question, answer_getter, answer_setter,
                                cls)
        if question.is_repeatable():
            return RepeatableCtrl(parent, question,
                                  answer_getter, answer_setter,
                                  cls)
        ans = cls(parent, question, answer_getter, answer_setter)
        ans.setInitialValue()
        return ans

from ucc.gui.controls.OptionalCtrl import OptionalCtrl
from ucc.gui.controls.RepeatableCtrl import RepeatableCtrl
