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
        
        self.cp = cp = wx.CollapsiblePane(self)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.onChange, cp)
        
        subpane = cp.GetPane()
        self.subctrl = self.subcls(subpane, self.question, self.ans_getter, 
                                   self.ans_setter)
        
        pane_sizer = wx.BoxSizer()
        subpane.SetSizer(pane_sizer)
        pane_sizer.Add(self.subctrl, 1, wx.ALL|wx.EXPAND, 0)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        sizer.Add(cp, 1, wx.ALL|wx.EXPAND, 0)
    
    def setInitialValue(self):
        debug.trace("{}.setInitialValue".format(self.__class__.__name__))
        
        if self.ans_getter() is None:
            debug.trace("Answer is None")
            self.cp.SetLabel(self.labelEnable)
            self.cp.Collapse(True)
        else:
            debug.trace("Answer is not None")
            self.cp.SetLabel(self.labelDisable)
            self.cp.Expand()
        
        if self.cp.IsExpanded():
            self.subctrl.setInitialValue()
    
    def onChange(self, event):
        debug.trace("Optional pane changed: {}".format(self.cp.IsExpanded()))
        
        if self.cp.IsExpanded():
            if self.ans_getter() is None:
                self.ans_setter(self.question.make_default_answer())
            self.subctrl.setInitialValue()
            self.cp.SetLabel(self.labelDisable)
        else:
            self.ans_setter(None)
            self.cp.SetLabel(self.labelEnable)
        self.parent.Layout()
    
