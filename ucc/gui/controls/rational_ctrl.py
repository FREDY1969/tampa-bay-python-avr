# rational_ctrl.py

'''Control for rational questions.'''

import wx
from ucc.gui.controls.number_ctrl import NumberCtrl
from ucc.gui import debug

class RationalCtrl(NumberCtrl):
    pass

# class RationalCtrl(BaseCtrl):
#     def setupControl(self):
#         self.textCtrlNum = wx.TextCtrl(self, size=(250, -1))
#         self.slash = wx.StaticText(self, label=" / ")
#         self.textCtrlDen = wx.TextCtrl(self, size=(250, -1))
#         self.Bind(wx.EVT_TEXT, self.onChange, self.textCtrlNum)
#         self.Bind(wx.EVT_TEXT, self.onChange, self.textCtrlDen)
#     
#     def setInitialValue(self):
#         debug.trace("%s.setInitialValue %s=%s" % 
#                     (self.__class__.__name__,
#                      self.question.name,
#                      self.get_answer()))
#         # self.textCtrl.ChangeValue(self.get_answer())
#     
#     def onChange(self, event):
#         debug.notice("Text changed: %s" % event.GetString())
#         # self.get_answer().value = event.GetString()
#     
