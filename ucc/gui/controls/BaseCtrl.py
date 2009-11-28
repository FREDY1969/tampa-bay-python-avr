
import wx

class BaseCtrl(wx.Panel):
    def __init__(self, parent, question, answer_getter, answer_setter):
        super(BaseCtrl, self).__init__(parent)

        self.parent = parent
        self.question = question
        self.answer_getter = answer_getter
        self.answer_setter = answer_setter

        self.makeControl()

    def makeControl(self):
        msg = None
        parent = self
        print self.__class__.__name__, "makeControl: question", self.question
        if self.question.is_optional():
            self.label1 = "Click here to answer"
            self.label2 = "Click here not to answer"
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

            if self.answer_getter() is None:
                print "answer is None"
                self.cp.Collapse(False)
                self.cp.Collapse(True)
            else:
                print "answer is not None"
                self.setInitialValue()
                self.cp.Collapse(False)

        elif self.question.is_repeatable():
            msg = "<%s %s>: can't do repeatable questions yet" % \
              (self.question.__class__.__name__, self.question.name)
            if self.question.is_orderable():
                pass
        else:
            self.paintControl(parent)
            self.setInitialValue()
        if msg:
            print msg
            wx.StaticText(self, wx.ID_ANY, msg)

    def onCollapsiblePaneChanged(self, evt = None):
        print "onCollapsiblePaneChanged: IsExpanded", self.cp.IsExpanded()
        self.parent.Layout()
        print "onCollapsiblePaneChanged: after Layout(), IsExpanded", self.cp.IsExpanded()
        if self.cp.IsExpanded():
            if self.answer_getter() is None:
                self.answer_setter(self.question.make_default_answer())
            self.setInitialValue()
            self.cp.SetLabel(self.label2)
        else:
            self.answer_setter(None)
            self.cp.SetLabel(self.label1)

    def paintControl(self, parent):
        msg = "<%s %s>: can't do %s yet" % \
          (self.question.__class__.__name__, self.question.name,
           self.__class__.__name__)
        print msg
        wx.StaticText(parent, wx.ID_ANY, msg)
