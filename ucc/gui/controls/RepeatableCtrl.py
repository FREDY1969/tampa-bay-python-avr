# RepeatableCtrl.py

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl

class RepeatableCtrl(BaseCtrl):
    def __init__(self, parent, question, answer_getter, answer_setter, subcls):
        self.subcls = subcls
        super(RepeatableCtrl, self).__init__(parent, question, answer_getter,
                                             answer_setter)

    def init2(self):
        print "repeatable for:", self.question
        msg = "<%s %s>: can't do repeatable questions yet" % \
          (self.question.__class__.__name__, self.question.name)
        if self.question.is_orderable():
            pass
        print msg
        wx.StaticText(self, wx.ID_ANY, msg)

