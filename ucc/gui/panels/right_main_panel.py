# right_main_panel.py

r'''Main GUI panel for creating and answering questions.'''

import os
import wx
import wx.lib.scrolledpanel as scrolled

from ucc.gui import registry
from ucc.gui import controls
from ucc.gui import debug
from ucc.gui.controls.bottom_text_ctrl import BottomTextCtrl

class RightMainPanel(wx.Panel):
    def __init__(self, parent, id, style):
        super(RightMainPanel, self).__init__(parent, id, style=style)
        
        # setup ui
        
        splitter = wx.SplitterWindow(self, -1, style=wx.SP_LIVE_UPDATE)
        
        self.topPanel = scrolled.ScrolledPanel(splitter, -1, \
                                               style=wx.BORDER_SUNKEN)
        self.topSizer = wx.FlexGridSizer(cols=2, hgap=2, vgap=2)
        self.topSizer.SetFlexibleDirection(wx.HORIZONTAL)
        self.topSizer.AddGrowableCol(1, 1)
        
        self.topPanel.SetSizer(self.topSizer)
        self.topPanel.SetupScrolling(scroll_x = False)
        
        self.bottomText = BottomTextCtrl(splitter, -1, \
                                      style=wx.TE_MULTILINE|wx.BORDER_SUNKEN)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        topHeight = registry.config.getint('gui', 'question-panel-height')
        splitter.SetMinimumPaneSize(200)
        splitter.SetSashGravity(0.0)
        splitter.SplitHorizontally(self.topPanel, self.bottomText, topHeight)
        debug.trace("Height configuration value: {}".format(topHeight))
        
        sizer.Add(splitter, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Fit()
        
        debug.trace("RightMainPanel height: {}" \
                      .format(self.GetClientSize().GetHeight()))
    
    def paint(self):
        self.topSizer.Clear(True)
        self.buildWord()
        self.topSizer.Layout()
    
    def buildWord(self):
        debug.trace("RightMainPanel.buildWord")
        
        # setup word controls
        
        if registry.currentWord:
            for question in registry.currentWord.kind_obj.questions or ():
                self.topSizer.Add(wx.StaticText(self.topPanel, -1, \
                                                "{}: ".format(question.label))
                if not hasattr(question, 'control'):
                    msg = "<{} {}> has no control" \
                            .format(question.__class__.__name__, question.name)
                    debug.warn(msg)
                    self.topSizer.Add(wx.StaticText(self.topPanel, -1, msg))
                else:
                    cls = getattr(controls, question.control)
                    debug.trace('{} is being renderd as {}'
                                  .format(question.name, cls.__name__))
                    self.topSizer.Add(
                      cls.makeControl(
                        self.topPanel,
                        question,
                        lambda question=question:
                            registry.currentWord.get_answer(question.name),
                        lambda new_ans, question=question:
                            registry.currentWord.set_answer(question.name,
                                                            new_ans)))

            
            # setup bottom text
            
            self.bottomText.ClearAll()
            source_filename = registry.currentWord.get_filename()
            if source_filename and os.path.exists(source_filename):
                if registry.currentWord.source_text:
                    self.bottomText.SetText(registry.currentWord.source_text)
                    debug.trace('loaded from source_text')
                else:
                    self.bottomText.LoadFile(source_filename)
                    debug.trace('loaded from file')
        else:
            debug.notice('No word currently selected')
        
    
