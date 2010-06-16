# word_tree_ctrl.py

r'''Tree control who's leaves represent words.'''

import wx
from ucc.gui import registry
from ucc.gui import debug

GRAY = (170, 170, 170, 255)
LIGHT_BLUE = (76, 139, 220, 76)
ALPHA = (255, 255, 255, 0)

class WordTreeCtrl(wx.TreeCtrl):
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
            word.tree_node = wordNode
            if not word.top:
                self.SetItemTextColour(wordNode, GRAY)
            self.SetPyData(wordNode, word)
            if (parent == self.root):
                self.expandThese.append(wordNode)
            self.buildWordTree(word.subclasses, wordNode)
            self.buildWordTree(word.instances, wordNode)

    def expandThem(self):
        for node in self.expandThese:
            self.Expand(node)

    def onActivate(self, e):
        
        # open/paint new word
        
        if registry.currentWord:
            if registry.rightMainPanel.bottomText.GetText():
                registry.currentWord.source_text = \
                                 registry.rightMainPanel.bottomText.GetText()
            self.SetItemBackgroundColour(registry.currentWord.tree_node, ALPHA)
        registry.currentWord = self.GetItemPyData(e.GetItem())
        self.SetItemBackgroundColour(registry.currentWord.tree_node, LIGHT_BLUE)
        debug.header("New word selected: {}".format(registry.currentWord.name))
        registry.rightMainPanel.paint()
    

