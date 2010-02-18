# optional_ctrl.py

'''Control for optional questions.'''

import wx
from ucc.gui.controls.base_ctrl import BaseCtrl
from ucc.gui import debug

class OptionalCtrl(BaseCtrl):
    def __init__(self, subcls, *args, **kwargs):
        self.subcls = subcls
        super(OptionalCtrl, self).__init__(*args, **kwargs)
    
    def setupControl(self):
        self.labelEnable = "Click to answer"
        self.labelDisable = "Click to unanswer"
        self.cp = cp = wx.CollapsiblePane(self, label=self.labelEnable)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.onChange, cp)
        
        subpane = cp.GetPane()
        self.subctrl = self.subcls(subpane, self.question, self.word)
        
        pane_sizer = wx.BoxSizer()
        subpane.SetSizer(pane_sizer)
        pane_sizer.Add(self.subctrl)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        sizer.Add(cp, 1, wx.ALL|wx.EXPAND, 0)
    
    def setInitialValue(self):
        debug.trace("%s.setInitialValue" % self.__class__.__name__)
        
        if self.get_answer() is None:
            debug.trace("Answer is None")
            self.cp.Collapse(True)
        else:
            debug.trace("Answer is not None")
            self.cp.Expand()
        
        if self.cp.IsExpanded():
            self.subctrl.setInitialValue()
    
    def onChange(self, event):
        # self.get_answer().value = str(event.GetInt())
        
        debug.trace("Optional pane changed: %s" % self.cp.IsExpanded())
        if self.cp.IsExpanded():
            if self.get_answer() is None:
                self.set_answer(self.question.make_default_answer())
            self.subctrl.setInitialValue()
            self.cp.SetLabel(self.label2)
        else:
            self.set_answer(None)
            self.cp.SetLabel(self.label1)
        self.parent.Layout()
    
