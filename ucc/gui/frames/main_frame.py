# main_frame.py

r'''Primary frame (window) for the IDE.'''

import sys
import wx

from ucc.gui import registry
from ucc.gui.other.main_menu_bar import MainMenuBar
from ucc.gui.panels.left_tree_panel import LeftTreePanel
from ucc.gui.panels.right_main_panel import RightMainPanel
from ucc.gui import debug

class MainFrame(wx.Frame):
    def __init__(self, parent, id, title):
        super(MainFrame, self).__init__(parent, id, title,
            size = list(map(int,
                       registry.config.get('gui', 'window-size').split('x'))),
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
        self.Bind(wx.EVT_CLOSE, self.onExit)
        
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
    
    def onExit(self, event):
        
        # make sure all words are saved
        
        opened_words = [word for word in \
                        list(registry.top_package.word_dict.values()) \
                        if word.save_state == False]
        if len(opened_words):
            dlg = ConfirmSaveDialog(None, -1, "Do you want to save the " \
                                    "currently opened words?", \
                                    size=(350, 200))
            val = dlg.ShowModal()
            if val == wx.ID_SAVE:
                debug.notice("Saving Words")
                for word in opened_words:
                    word.save()
            elif val == wx.ID_NO:
                debug.notice("Not Saving Words")
            else:
                dlg.Destroy()
                return
            
            dlg.Destroy()
        
        event.Skip()
    

class ConfirmSaveDialog(wx.Dialog):
    def __init__(self, parent, id, title, *args, **kwargs):
        super(ConfirmSaveDialog, self).__init__(parent, id, title ,*args, **kwargs)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(self, -1, "Do you want to save the currently open words?")
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)
        
        btnsizer = wx.StdDialogButtonSizer()
        
        btn = wx.Button(self, wx.ID_SAVE)
        btn.Bind(wx.EVT_BUTTON, lambda event: self.EndModal(wx.ID_SAVE))
        btn.SetDefault()
        btnsizer.AddButton(btn)
        
        btn = wx.Button(self, wx.ID_NO)
        btn.Bind(wx.EVT_BUTTON, lambda event: self.EndModal(wx.ID_NO))
        btnsizer.AddButton(btn)
        
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        
        btnsizer.Realize()
        
        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
        self.SetSizer(sizer)
        sizer.Fit(self)
        
        self.CenterOnScreen()
    
