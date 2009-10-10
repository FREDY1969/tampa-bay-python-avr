'''
'''

import setpath
setpath.setpath(__file__)

import wx, wx.py
import wx.lib.scrolledpanel as scrolled

from ucc.gui.Registry import Registry

class RightMainPanel(wx.Panel):
    def __init__(self, parent, id, style):
        wx.Panel.__init__(self, parent, id, style=style)
        
        # setup splitter
        
        splitter = self.splitter = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3D)

        # setup panels
        
        topPanel = self.topPanel = scrolled.ScrolledPanel(splitter, wx.ID_ANY)
        topSizer = self.topSizer = wx.BoxSizer(wx.VERTICAL)
        topPanel.SetSizer(topSizer)
        topPanel.SetAutoLayout(1)
        topPanel.SetupScrolling()
        bottomText = self.bottomText = wx.py.editwindow.EditWindow(splitter, wx.ID_ANY,
                                                      style=wx.TE_MULTILINE)
        self.bottomText.setDisplayLineNumbers(True)
        
        # setup sizer
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        # add top and bottom stuff

        splitter.SetMinimumPaneSize(200)
        splitter.SetSashGravity(1)
        splitter.SplitHorizontally(topPanel, bottomText, 300)

        sizer.Add(splitter, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Fit()
        
        self.test = None
        
        
    def paint(self):
        print "painting rightMainPanel"
        self.buildWord()
        
    def buildWord(self):
        
        # setup controls
        
        self.topSizer.Clear(True)
        
        for question in Registry.currentWord.questions:
            question.paint()
        
        self.topSizer.Layout()
        
        # bottom text
        
        self.bottomText.ClearAll()
        if Registry.currentWordPath:
            self.bottomText.LoadFile(Registry.currentWordPath)
