'''
'''

from __future__ import with_statement

import os.path

import setpath
setpath.setpath(__file__)

import wx, wx.py
from ucc.gui.Registry import Registry

class RightMainPanel(wx.Panel):
    def __init__(self, parent, id, style):
        wx.Panel.__init__(self, parent, id, style=style)
        
        # setup panels
        
        topPanel = self.topPanel = wx.Panel(self, wx.ID_ANY)
        topSizer = self.topSizer = wx.BoxSizer(wx.VERTICAL)
        topPanel.SetSizer(topSizer)
        self.bottomText = wx.py.editwindow.EditWindow(self, wx.ID_ANY,
                                                      style=wx.TE_MULTILINE)
        self.bottomText.setDisplayLineNumbers(True)
        
        # setup sizer
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(topPanel, 1, wx.EXPAND)
        sizer.Add(self.bottomText, 1, wx.EXPAND)
        
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
        if Registry.currentWord:
            kind_word = Registry.wordDict[Registry.currentWord.kind]
            suffix = kind_word.get_answer('filename_suffix')
            if suffix is not None:
                if suffix:
                    filename = Registry.currentWord.name + '.' + suffix.value
                else:
                    filename = Registry.currentWord.name
                path = os.path.join(Registry.currentPackage, filename)
                if not os.path.exists(path):
                    print "creating", path
                    with open(path, 'w'): pass
                self.bottomText.LoadFile(path)
        #self.bottomText.SaveFile(filename)
