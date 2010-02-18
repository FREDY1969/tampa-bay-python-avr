# right_main_panel.py

r'''Main GUI panel for creating and answering questions.'''

import os
import wx, wx.py
import wx.lib.scrolledpanel as scrolled

from ucc.gui import registry
from ucc.gui import controls
from ucc.gui import debug

class RightMainPanel(wx.Panel):
    def __init__(self, parent, id, style):
        super(RightMainPanel, self).__init__(parent, id, style=style)
        
        # setup splitter
        
        splitter = self.splitter = \
          wx.SplitterWindow(self, -1, style=wx.SP_LIVE_UPDATE)
        
        # setup panels
        
        topPanel = self.topPanel = \
          scrolled.ScrolledPanel(splitter, -1, style=wx.BORDER_SUNKEN)
        topSizer = self.topSizer = wx.FlexGridSizer(cols=2, hgap=2, vgap=2)
        topSizer.SetFlexibleDirection(wx.HORIZONTAL)
        topSizer.AddGrowableCol(1, 1)
        topPanel.SetSizer(topSizer)
        topPanel.SetupScrolling(scroll_x = False)
        bottomText = self.bottomText = \
          wx.py.editwindow.EditWindow(splitter, -1,
                                      style=wx.TE_MULTILINE|wx.BORDER_SUNKEN)
        bottomText.setDisplayLineNumbers(True)
        
        # setup sizer
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # add top and bottom stuff
        
        splitter.SetMinimumPaneSize(200)
        splitter.SetSashGravity(0.0)
        splitter.SplitHorizontally(topPanel, bottomText,
          registry.config.getint('gui', 'question-panel-height'))
        debug.trace("Height configuration value: %s" %
                    registry.config.getint('gui', 'question-panel-height'))
        
        sizer.Add(splitter, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Fit()
        
        debug.trace("RightMainPanel height: %s" %
                    self.GetClientSize().GetHeight())
    
    def paint(self):
        self.topSizer.Clear(True)
        self.buildWord()
        self.topSizer.Layout()
    
    def buildWord(self):
        debug.trace("RightMainPanel.buildWord")
        
        # setup word controls
        
        if registry.currentWord:
            for question in registry.currentWord.kind_obj.questions or ():
                self.topSizer.Add(wx.StaticText(self.topPanel, -1, 
                                                question.label))
                if not hasattr(question, 'control'):
                    msg = "<%s %s> has no control" % \
                            (question.__class__.__name__, question.name)
                    debug.warn(msg)
                    self.topSizer.Add(wx.StaticText(self.topPanel, -1, msg))
                else:
                    cls = getattr(controls, question.control)
                    debug.trace('%s is being renderd as %s' % (question.name, 
                                                               cls.__name__))
                    self.topSizer.Add(cls.makeControl(
                        self.topPanel,
                        question,
                        registry.currentWord))
            
            # setup bottom text
            
            self.bottomText.ClearAll()
            source_filename = registry.currentWord.get_filename()
            if source_filename and os.path.exists(source_filename):
                self.bottomText.LoadFile(source_filename)
        else:
            debug.notice('No word currently selected')
        
    
