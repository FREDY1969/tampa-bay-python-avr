# left_tree_panel.py

r'''Panel that contains the WordTreeCtrl'''

import os.path
import wx

from ucc.gui.controls.word_tree_ctrl import WordTreeCtrl
from ucc.gui import registry
from ucc.gui import debug

class LeftTreePanel(wx.Panel):
    def __init__(self, parent, id, style):
        super(LeftTreePanel, self).__init__(parent, id, style=style)
        
        # setup components
        
        label = wx.StaticText(self, -1, "Words", style=wx.ALIGN_CENTER)
        registry.wordTreeCtrl = WordTreeCtrl(self, -1, wx.DefaultPosition, (300,300), wx.TR_DEFAULT_STYLE)
        registry.wordTreeCtrl.SetBackgroundColour(wx.WHITE)
        
        # setup sizer
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(label, 0, wx.EXPAND)
        sizer.Add(registry.wordTreeCtrl, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        
    def paint(self):
        debug.trace("Painting leftTreePanel")
        self.drawTree()
        
    def drawTree(self):
        registry.wordTreeCtrl.updateWordTree()
    
