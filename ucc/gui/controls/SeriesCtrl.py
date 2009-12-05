# SeriesCtrl.py

r'''Control for series word values'''

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl

class SeriesCtrl(BaseCtrl):
    def paintControl(self, parent):
        self.box = wx.StaticBox(parent, -1)
        self.internal_sizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        self.internal_sizer.AddGrowableCol(1)

        self.children = []
        for sub_question in self.question.subquestions:
            self.internal_sizer.Add(wx.StaticText(self.box, wx.ID_ANY,
                                                  sub_question.label))
            if not hasattr(sub_question, 'control'):
                msg = "<%s %s> has no 'control'" % \
                        (sub_question.__class__.__name__, sub_question.name)
                print msg
                self.internal_sizer.Add(wx.StaticText(self.box, wx.ID_ANY, msg))
            else:
                cls = getattr(getattr(controls, sub_question.control),
                              sub_question.control)
                child = \
                  cls(self.box,
                      sub_question,
                      lambda: getattr(self.answer_getter(), sub_question.name),
                      self.error_setter)
                self.internal_sizer.Add(child)
                self.children.append(child)

        border = wx.BoxSizer()
        border.Add(self.internal_sizer, 1, wx.EXPAND | wx.ALL, 25)
        self.SetSizer(border)
        
    def error_setter(self, new_ans):
        raise AssertionError(
                "%s.SeriesCtrl: answer_setter used by subordinate" %
                  self.question.name)

    def setInitialValue(self):
        for child in self.children:
            child.setInitialValue()

