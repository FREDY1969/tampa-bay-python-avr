# OptionalCtrl.py

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl

class OptionalCtrl(BaseCtrl):
    def __init__(self, parent, question, answer_getter, answer_setter, subcls):
        self.subcls = subcls
        super(OptionalCtrl, self).__init__(parent, question, answer_getter,
                                       answer_setter)

    def init2(self):
        print "optional for:", self.question
        self.label1 = "Click to answer"
        self.label2 = "Click to unanswer"
        self.cp = cp = wx.CollapsiblePane(self, label=self.label1,
                                          style=wx.CP_DEFAULT_STYLE
                                              | wx.CP_NO_TLW_RESIZE)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.onPaneChanged, cp)

        subpane = cp.GetPane()
        self.subctrl = self.subcls(subpane, self.question,
                                   self.answer_getter, self.answer_setter)

        pane_sizer = wx.BoxSizer()
        subpane.SetSizer(pane_sizer)
        pane_sizer.Add(self.subctrl, 1, wx.LEFT|wx.EXPAND, 3)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        sizer.Add(cp, 1, wx.ALL|wx.EXPAND, 0)

        if self.answer_getter() is None:
            print "answer is None"
            self.cp.Collapse(True)
        else:
            print "answer is not None"
            self.cp.Collapse(False)

    def setInitialValue(self):
        if self.cp.IsExpanded():
            self.subctrl.setInitialValue()

    def onPaneChanged(self, evt = None):
        print "onPaneChanged: IsExpanded", self.cp.IsExpanded()
        if self.cp.IsExpanded():
            if self.answer_getter() is None:
                self.answer_setter(self.question.make_default_answer())
            self.subctrl.setInitialValue()
            self.cp.SetLabel(self.label2)
        else:
            self.answer_setter(None)
            self.cp.SetLabel(self.label1)
        self.parent.Layout()

