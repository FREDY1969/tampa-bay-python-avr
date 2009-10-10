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
        
        if self.test == None:
            self.topSizer.Clear(True)
            self.topSizer.Add(wx.StaticText(self.topPanel, wx.ID_ANY, "TopPanel"))
            self.topSizer.Add(wx.RadioButton(self.topPanel, -1, 'Value A', style=wx.RB_GROUP))
            self.topSizer.Add(wx.RadioButton(self.topPanel, -1, 'Value B'))
            self.topSizer.Add(wx.RadioButton(self.topPanel, -1, 'Value C'))
            self.topSizer.Add(wx.CheckBox(self.topPanel, wx.ID_ANY, 'CheckBox'))
            self.topSizer.Add(wx.Slider(self.topPanel, wx.ID_ANY, style=wx.SL_HORIZONTAL))
            self.topSizer.Add(wx.TextCtrl(self.topPanel, wx.ID_ANY))
            self.topSizer.Add(wx.BitmapButton(self.topPanel, wx.ID_ANY, wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_BUTTON)))
            self.topSizer.Add(wx.BitmapButton(self.topPanel, wx.ID_ANY, wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_BUTTON)))
            self.topSizer.Add(wx.ComboBox(self.topPanel, wx.ID_ANY, choices=['Option 1','Option 2']))
            self.test = True
        else:
            self.topSizer.Clear(True)
            self.topSizer.Add(wx.StaticText(self.topPanel, wx.ID_ANY, "TopPanel"))
            self.topSizer.Add(wx.RadioButton(self.topPanel, -1, 'Value A', style=wx.RB_GROUP))
            self.topSizer.Add(wx.RadioButton(self.topPanel, -1, 'Value B'))
            self.topSizer.Add(wx.RadioButton(self.topPanel, -1, 'Value C'))
            self.topSizer.Add(wx.CheckBox(self.topPanel, wx.ID_ANY, 'CheckBox'))
            self.topSizer.Layout()
        self.bottomText.ClearAll()
        if Registry.currentWordPath:
            self.bottomText.LoadFile(Registry.currentWordPath)
