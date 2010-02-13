# LeftTreePanel.py

r'''
'''

import os.path
import wx

from ucc.gui.WordTreeCtrl import WordTreeCtrl
from ucc.gui import Registry

class LeftTreePanel(wx.Panel):
    def __init__(self, parent, id, style):
        wx.Panel.__init__(self, parent, id, style=style)

        # setup components

        label = wx.StaticText(self, wx.ID_ANY, "Words", style=wx.ALIGN_CENTER)
        Registry.wordTreeCtrl = WordTreeCtrl(self, wx.ID_ANY, wx.DefaultPosition, (300,300), wx.TR_DEFAULT_STYLE)
        Registry.wordTreeCtrl.SetBackgroundColour(wx.WHITE)

        # setup sizer

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(label, 0, wx.EXPAND)
        sizer.Add(Registry.wordTreeCtrl, 1, wx.EXPAND)

        self.SetSizer(sizer)

    def paint(self):
        print "painting leftTreePanel"
        self.drawTree()

    def drawTree(self):
        Registry.wordTreeCtrl.updateWordTree()
