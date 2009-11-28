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
        parent = self
        print self.__class__.__name__, "makeControl: question", self.question
        if self.question.is_optional():
            self.label1 = "Click here to answer " + self.question.name
            self.label2 = "Click here to discard " + self.question.name
            self.cp = cp = wx.CollapsiblePane(self, label=self.label1,
                                              style=wx.CP_DEFAULT_STYLE
                                                  | wx.CP_NO_TLW_RESIZE)
            self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED,
                      self.onCollapsiblePaneChanged, cp)
            self.paintControl(cp.GetPane())

            #cp.SetAutoLayout(1)
            #self.SetAutoLayout(1)
            #self.parent.SetAutoLayout(1)

            sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(sizer)
            sizer.Add(cp, 0, wx.RIGHT|wx.LEFT|wx.EXPAND, 0)

            if self.answer is None:
                print "answer is None"
                self.cp.Collapse(False)
                self.cp.Collapse(True)
                #self.onCollapsiblePaneChanged()
            else:
                print "answer is not None"
                self.cp.Collapse(False)
                #self.onCollapsiblePaneChanged()

        elif self.question.is_repeatable():
            msg = "<%s %s>: can't do repeatable questions yet" % \
              (self.question.__class__.__name__, self.question.name)
            if self.question.is_orderable():
                pass
        else:
            self.paintControl(parent)
        if msg:
            print msg
            st = wx.StaticText(self, wx.ID_ANY, msg)
            sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(sizer)
            sizer.Add(st, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 0)

    def onCollapsiblePaneChanged(self, evt = None):
        print "onCollapsiblePaneChanged: IsExpanded", self.cp.IsExpanded()
        self.parent.Layout()
        print "onCollapsiblePaneChanged: after Layout(), IsExpanded", self.cp.IsExpanded()
        if self.cp.IsExpanded():
            self.cp.SetLabel(self.label2)
        else:
            self.cp.SetLabel(self.label1)

    def paintControl(self, parent):
        msg = "<%s %s>: can't do %s yet" % \
          (self.question.__class__.__name__, self.question.name,
           self.__class__.__name__)
        print msg
        st = wx.StaticText(parent, wx.ID_ANY, msg)
        sizer = wx.BoxSizer(wx.VERTICAL)
        parent.SetSizer(sizer)
        sizer.Add(st, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 25)

class BoolCtrl(BaseCtrl):
    def paintControl(self, parent):
        cb = wx.CheckBox(parent, wx.ID_ANY, self.label)
        cb.SetValue(self.answer.get_value())
        self.Bind(wx.EVT_CHECKBOX, self.checked, cb)
    
    def checked(self, event):
        self.answer.value = repr(event.IsChecked())
        print "IsChecked", self.answer.value

