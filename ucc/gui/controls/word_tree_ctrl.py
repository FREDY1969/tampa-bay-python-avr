# word_tree_ctrl.py

r'''Tree control who's leaves represent words.'''

from __future__ import with_statement

import wx
from ucc.gui import registry
from ucc.gui import debug

class WordTreeCtrl(wx.TreeCtrl):
    gray = (170, 170, 170, 255)
    def __init__(self, parent, id, pos, size, style):
        super(WordTreeCtrl, self).__init__(parent, id, pos, size,
                             style | wx.TR_HIDE_ROOT)

        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.onActivate, self)

    def updateWordTree(self):
        self.DeleteAllItems()
        root = self.root = self.AddRoot('hidden')
        self.SetPyData(root, None)

        self.expandThese = []
        self.buildWordTree(registry.top_package.roots, root)
        self.expandThem()

    def buildWordTree(self, words, parent):
        for word in words:
            wordNode = self.AppendItem(parent, word.label)
            if not word.top:
                self.SetItemTextColour(wordNode, self.gray)
            self.SetPyData(wordNode, word)
            if (parent == self.root):
                self.expandThese.append(wordNode)
            self.buildWordTree(word.subclasses, wordNode)
            self.buildWordTree(word.instances, wordNode)

    def expandThem(self):
        for node in self.expandThese:
            self.Expand(node)

    def onActivate(self, e):
        
        # check state of word to see if it needs to be saved
        
        if registry.currentWord:
            dlg = ConfirmSaveDialog(self, -1, "Save Word?", size=(350, 200))
            val = dlg.ShowModal()
            
            if val == wx.ID_SAVE:
                debug.notice("Saving Word")
                registry.app.saveWord()
            elif val == wx.ID_NO:
                debug.notice("Not Saving Word")
            else:
                dlg.Destroy()
                return
            
            dlg.Destroy()
            
        # open/paint new word
        
        registry.currentWord = self.GetItemPyData(e.GetItem())
        debug.header("New word selected: %s" % registry.currentWord.name)
        registry.rightMainPanel.paint()
    

class ConfirmSaveDialog(wx.Dialog):
    def __init__(self, parent, id, title, *args, **kwargs):
        super(ConfirmSaveDialog, self).__init__(parent, id, title ,*args, **kwargs)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(self, -1, "Do you want to save the currently open word?")
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
    
