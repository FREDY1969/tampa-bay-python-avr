# WordTreeCtrl.py

r'''
'''

from __future__ import with_statement

import os.path

import wx

from ucc.gui import Registry
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
        self.buildWordTree(Registry.top_package.roots, root)
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
        
        Registry.app.saveWord()
        
        # open/paint new word
        
        Registry.currentWord = self.GetItemPyData(e.GetItem())
        debug.header("New word selected: %s" % Registry.currentWord.name)
        Registry.rightMainPanel.paint()
