r'''Control for boolean word values'''

import wx

class BaseCtrl(wx.Panel):
    def __init__(self, parent, question, answer, label='True or False?'):
        super(BaseCtrl, self).__init__(parent)

        self.parent = parent
        self.question = question
        self.answer = answer
        self.label = label

        self.makeControl()

    def makeControl(self):
        msg = None
        if self.question.is_optional():
            msg = "<%s %s>: can't do optional questions yet" % \
              (self.question.__class__.__name__, self.question.name)
        elif self.question.is_repeatable():
            msg = "<%s %s>: can't do repeatable questions yet" % \
              (self.question.__class__.__name__, self.question.name)
            if self.question.is_orderable():
                pass
        if msg:
            print msg
            wx.StaticText(self, wx.ID_ANY, msg)
        else:
            self.paintControl(self)

class BoolCtrl(BaseCtrl):
    def paintControl(self, parent):
        cb = wx.CheckBox(parent, wx.ID_ANY, self.label)
        cb.SetValue(self.answer.get_value())
        self.Bind(wx.EVT_CHECKBOX, self.checked, cb)
    
    def checked(self, event):
        self.answer.value = repr(event.IsChecked())
        print "IsChecked", self.answer.value

