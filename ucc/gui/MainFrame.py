# MainFrame.py

r'''
'''

import sys
import wx

from ucc.gui.Registry import Registry
from ucc.gui.MainMenuBar import MainMenuBar
from ucc.gui.LeftTreePanel import LeftTreePanel
from ucc.gui.RightMainPanel import RightMainPanel

class MainFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title,
            size = map(int,
                       Registry.config.get('gui', 'window-size').split('x')),
            style = wx.DEFAULT_FRAME_STYLE # | wx.NO_FULL_REPAINT_ON_RESIZE
        )
        self.SetMinSize((970,720))
        
        # setup status bar
        
        self.CreateStatusBar()
        
        # setup menu bar
        
        Registry.mainMenuBar = MainMenuBar(self)
        self.SetMenuBar(Registry.mainMenuBar)
        
        # setup toolbar
        
        Registry.mainToolbar = self.CreateToolBar(style = wx.TB_HORIZONTAL)
        Registry.mainToolbar.AddLabelTool(Registry.ID_OPEN, '', wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR))
        # Registry.mainToolbar.AddLabelTool(Registry.ID_SAVE_ALL, '', wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR))
        # Registry.mainToolbar.AddSeparator()
        Registry.mainToolbar.AddLabelTool(Registry.ID_SAVE_WORD, '', wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR))
        # Registry.mainToolbar.AddLabelTool(Registry.ID_VERIFY, '', wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_TOOLBAR))
        # Registry.mainToolbar.AddSeparator()
        # Registry.mainToolbar.AddLabelTool(Registry.ID_COMPILE, '', wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE, wx.ART_TOOLBAR))
        # Registry.mainToolbar.AddLabelTool(Registry.ID_PUSH, '', wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR))
        Registry.mainToolbar.Realize()
        
        self.Bind(wx.EVT_TOOL, Registry.app.onOpen, id=Registry.ID_OPEN)
        self.Bind(wx.EVT_TOOL, Registry.app.onSaveWord, id=Registry.ID_SAVE_WORD)
        
        # setup mainPanel
        
        Registry.mainPanel = wx.Panel(self, wx.ID_ANY)
        
        # setup sizer
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(Registry.mainPanel, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        
        # setup splitter
        
        splitter = wx.SplitterWindow(Registry.mainPanel, wx.ID_ANY, style=wx.SP_3D)
        
        # setup panels
        
        Registry.leftTreePanel = LeftTreePanel(splitter, wx.ID_ANY, wx.BORDER_SUNKEN | wx.WANTS_CHARS)
        Registry.rightMainPanel = RightMainPanel(splitter, wx.ID_ANY, wx.BORDER_SUNKEN)
        
        # setup splitter/sizers
        
        splitter.SetMinimumPaneSize(200)
        splitter.SplitVertically(Registry.leftTreePanel,
                                 Registry.rightMainPanel,
                                 Registry.config.getint('gui', 'left-panel-width'))
        
        # setup sizer
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        Registry.mainPanel.SetSizer(sizer)
        
        # paint
        
        self.paint()
        
        # show frame
        
        self.Center()
        self.Show(True)
        
    def paint(self):
        print "painting mainFrame"
        Registry.leftTreePanel.paint()
        Registry.rightMainPanel.paint()
