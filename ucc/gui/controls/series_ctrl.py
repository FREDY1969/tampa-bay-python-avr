# series_ctrl.py

r'''Control for queston series.'''

import wx
from ucc.gui.controls.base_ctrl import BaseCtrl
import ucc.gui.controls

class SeriesCtrl(BaseCtrl):
    def init2(self):
        self.box = wx.StaticBox(self, -1)
        self.bsizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)

        self.gridsizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        self.gridsizer.SetFlexibleDirection(wx.HORIZONTAL)
        self.gridsizer.AddGrowableCol(1, 1)
        self.bsizer.Add(self.gridsizer, 1, wx.TOP|wx.EXPAND, 3)

        self.children = []
        for sub_question in self.question.subquestions:
            labelText = wx.StaticText(self, -1, sub_question.label)
            self.gridsizer.Add(labelText, flag=wx.TOP, border=6)
            if not hasattr(sub_question, 'control'):
                msg = "<%s %s> has no 'control'" % \
                        (sub_question.__class__.__name__, sub_question.name)
                print(msg)
                self.gridsizer.Add(wx.StaticText(self, -1, msg))
            else:
                cls = getattr(getattr(ucc.gui.controls, sub_question.control),
                              sub_question.control)
                child = \
                  cls.makeControl(self,
                      sub_question,
                      lambda sub_question=sub_question:
                          getattr(self.get_answer(), sub_question.name),
                      self.error_setter)
                self.gridsizer.Add(child)
                self.children.append(child)

        border = wx.BoxSizer()
        border.Add(self.bsizer, 1, wx.EXPAND | wx.TOP, -8)
        self.SetSizer(border)

    def error_setter(self, new_ans):
        raise AssertionError(
                "%s.SeriesCtrl: set_answer used by subordinate" %
                  self.question.name)

    def setInitialValue(self):
        for child in self.children:
            child.setInitialValue()

