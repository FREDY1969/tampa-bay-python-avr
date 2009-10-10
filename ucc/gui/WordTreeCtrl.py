'''
'''

import setpath
setpath.setpath(__file__)

import wx

from ucc.gui.Registry import Registry

class WordTreeCtrl(wx.TreeCtrl):
    def __init__(self, parent, id, pos, size, style):
        wx.TreeCtrl.__init__(self, parent, id, pos, size, style | wx.WANTS_CHARS)
        
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.onActivate, self)
        
    def updateWordTree(self):
        root = self.root = self.GetRootItem()
        Registry.words = self.readWordTree()
        
        self.expandThese = [root]
        self.buildWordTree(Registry.words, root)
        self.expandThem()
        
    def readWordTree(self):
        def getChildren(parent=None):
            children = []
            if parent == None:
                for temporaryWord in Registry.wordDict.itervalues():
                    if temporaryWord.name == temporaryWord.kind:
                        children.append({
                            'word': temporaryWord,
                            'children': getChildren(temporaryWord)
                        })
            else:
                for temporaryWord in Registry.wordDict.itervalues():
                    if parent.name == temporaryWord.kind and temporaryWord.name != temporaryWord.kind:
                        children.append({
                            'word': temporaryWord,
                            'children': getChildren(temporaryWord)
                        })
            return children
        return getChildren()
        
    def buildWordTree(self, words, parent):
        for word in words:
            wordNode = self.AppendItem(parent, word['word'].label)
            self.SetPyData(wordNode, word['word'])
            if (parent == self.root):
                self.expandThese.append(wordNode)
            self.buildWordTree(word['children'], wordNode)
            
    def expandThem(self):
        for node in self.expandThese:
            self.Expand(node)
    
    def onActivate(self, e):
        Registry.currentWord = self.GetItemPyData(e.GetItem())
        Registry.rightMainPanel.paint()
