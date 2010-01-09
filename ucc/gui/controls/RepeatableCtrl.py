# RepeatableCtrl.py

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl

class RepeatableCtrl(BaseCtrl):
    def __init__(self, parent, question, answer_getter, answer_setter, subcls):
        self.subcls = subcls
        super(RepeatableCtrl, self).__init__(parent, question, answer_getter,
                                             answer_setter)

    def init2(self):
        self.is_orderable = self.question.is_orderable()
        print "repeatable for:", self.question
        self.box = wx.StaticBox(self, wx.ID_ANY)
        self.bsizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.bsizer, 1, wx.EXPAND | wx.TOP, -8)
        self.SetSizer(self.sizer)

        #msg = "<%s %s>: can't do repeatable questions yet" % \
        #  (self.question.__class__.__name__, self.question.name)
        #if self.is_orderable:
        #    pass
        #print msg
        #wx.StaticText(self, wx.ID_ANY, msg)

    def setInitialValue(self):
        print "RepeatableCtrl.setInitialValue"
        self.subctrls = [
            self.subcls(self, self.question,
                        index_getter(self.answer_getter, i),
                        index_setter(self.answer_getter, i))
            for i, answer in enumerate(self.answer_getter())]
        print "subctrls", self.subctrls
        for ctrl in self.subctrls:
            self.bsizer.Add(ctrl, 0, wx.ALL|wx.EXPAND, 10)
            ctrl.setInitialValue()
        self.parent.Layout()

def index_getter(getter, i):
    return lambda : getter()[i]

def index_setter(getter, i):
    def foo(x):
        getter()[i] = x
    return foo
