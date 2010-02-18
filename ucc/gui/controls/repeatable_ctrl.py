# repeatable_ctrl.py

'''Control for repeatable questions.'''

import wx
from ucc.gui.controls.base_ctrl import BaseCtrl

class RepeatableCtrl(BaseCtrl):
    def __init__(self, subcls, parent, question, word):
        self.subcls = subcls
        super(RepeatableCtrl, self).__init__(parent, question, word)
    
    def init2(self):
        self.is_orderable = self.question.is_orderable()
        print "repeatable for:", self.question
        self.box = wx.StaticBox(self, -1)
        self.bsizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.bsizer, 1, wx.EXPAND | wx.TOP, -8)
        self.SetSizer(self.sizer)
        
        #msg = "<%s %s>: can't do repeatable questions yet" % \
        #  (self.question.__class__.__name__, self.question.name)
        #if self.is_orderable:
        #    pass
        #print msg
        #wx.StaticText(self, -1, msg)
    
    def setInitialValue(self):
        print "RepeatableCtrl.setInitialValue"
        self.subctrls = [
            self.subcls(self, self.question,
                        index_getter(self.get_answer, i),
                        index_setter(self.get_answer, i))
            for i, answer in enumerate(self.get_answer())]
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
