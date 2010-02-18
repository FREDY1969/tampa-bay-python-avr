# main_frame.py

r'''Primary frame (window) for the IDE.'''

import sys
import wx

from ucc.gui import registry
from ucc.gui.main_menu_bar import MainMenuBar
from ucc.gui.panels.left_tree_panel import LeftTreePanel
from ucc.gui.panels.right_main_panel import RightMainPanel
from ucc.gui import debug

class MainFrame(wx.Frame):
    def __init__(self, parent, id, title):
        super(MainFrame, self).__init__(parent, id, title,
            size = map(int,
                       registry.config.get('gui', 'window-size').split('x')),
            style = wx.DEFAULT_FRAME_STYLE # | wx.NO_FULL_REPAINT_ON_RESIZE
        )
        self.SetMinSize((970,720))
        
        # setup status bar
        
        self.CreateStatusBar()
        
        # setup menu bar
        
        registry.mainMenuBar = MainMenuBar(self)
        self.SetMenuBar(registry.mainMenuBar)
        
        # setup toolbar
        
        registry.mainToolbar = self.CreateToolBar(style = wx.TB_HORIZONTAL)
        registry.mainToolbar.AddLabelTool(registry.ID_OPEN, '', wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR))
        # registry.mainToolbar.AddLabelTool(registry.ID_SAVE_ALL, '', wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR))
        # registry.mainToolbar.AddSeparator()
        registry.mainToolbar.AddLabelTool(registry.ID_SAVE_WORD, '', wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR))
        # registry.mainToolbar.AddLabelTool(registry.ID_VERIFY, '', wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_TOOLBAR))
        # registry.mainToolbar.AddSeparator()
        registry.mainToolbar.AddLabelTool(registry.ID_COMPILE, '', wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE, wx.ART_TOOLBAR))
        registry.mainToolbar.AddLabelTool(registry.ID_LOAD, '', wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR))
        registry.mainToolbar.Realize()
        
        self.Bind(wx.EVT_TOOL, registry.app.onOpen, id=registry.ID_OPEN)
        self.Bind(wx.EVT_TOOL, registry.app.onSaveWord, id=registry.ID_SAVE_WORD)
        self.Bind(wx.EVT_TOOL, registry.app.onCompile, id=registry.ID_COMPILE)
        self.Bind(wx.EVT_TOOL, registry.app.onLoad, id=registry.ID_LOAD)
        
        # setup mainPanel
        
        registry.mainPanel = wx.Panel(self, -1)
        
        # setup sizer
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(registry.mainPanel, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        
        # setup splitter
        
        splitter = wx.SplitterWindow(registry.mainPanel, -1, style=wx.SP_3D)
        
        # setup panels
        
        registry.leftTreePanel = LeftTreePanel(splitter, -1, wx.BORDER_SUNKEN | wx.WANTS_CHARS)
        registry.rightMainPanel = RightMainPanel(splitter, -1, wx.BORDER_SUNKEN)
        
        # setup splitter/sizers
        
        splitter.SetMinimumPaneSize(200)
        splitter.SplitVertically(registry.leftTreePanel,
                                 registry.rightMainPanel,
                                 registry.config.getint('gui', 'left-panel-width'))
        
        # setup sizer
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        registry.mainPanel.SetSizer(sizer)
        
        # paint
        
        self.paint()
        
        # show frame
        
        self.Center()
        self.Show(True)
    
    def paint(self):
        debug.trace("Painting mainFrame")
        registry.leftTreePanel.paint()
        registry.rightMainPanel.paint()
    
