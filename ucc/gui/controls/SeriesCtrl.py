# SeriesCtrl.py

r'''Control for series word values'''

import wx
from ucc.gui.controls.BaseCtrl import BaseCtrl
import ucc.gui.controls

class SeriesCtrl(BaseCtrl):
    def paintControl(self, parent):
        self.box = wx.StaticBox(parent, -1)
        self.internal_sizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        self.internal_sizer.AddGrowableCol(1)

        self.children = []
        for sub_question in self.question.subquestions:
            labelText = wx.StaticText(parent, wx.ID_ANY, sub_question.label)
            self.internal_sizer.Add(labelText)
            if not hasattr(sub_question, 'control'):
                msg = "<%s %s> has no 'control'" % \
                        (sub_question.__class__.__name__, sub_question.name)
                print msg
                self.internal_sizer.Add(wx.StaticText(parent, wx.ID_ANY, msg))
            else:
                cls = getattr(getattr(ucc.gui.controls, sub_question.control),
                              sub_question.control)
                child = \
                  cls(parent,
                      sub_question,
                      lambda sub_question=sub_question:
                          getattr(self.answer_getter(), sub_question.name),
                      self.error_setter)
                self.internal_sizer.Add(child)
                self.children.append(child)

        border = wx.BoxSizer()
        border.Add(self.internal_sizer, 1, wx.EXPAND | wx.ALL, 25)
        parent.SetSizer(border)

    def error_setter(self, new_ans):
        raise AssertionError(
                "%s.SeriesCtrl: answer_setter used by subordinate" %
                  self.question.name)

    def setInitialValue(self):
        for child in self.children:
            child.setInitialValue()

