r'''Control for boolean word values'''

import wx

class BoolCtrl(wx.Window):
    def __init__(self, parent, answer, label='True or False?'):
        wx.Window.__init__(self, parent)
        
        self.parent = parent
        self.anser = answer
        self.label = label
        
        self.paintControl()
    
    def paintControl(self):
        wx.CheckBox(self, wx.ID_ANY, self.label)
    
    def getValue(self):
        return self.value
