# repeatable_ctrl.py

'''Control for repeatable questions.'''

import wx
from ucc.gui.controls.base_ctrl import BaseCtrl
from ucc.gui import debug

class RepeatableCtrl(BaseCtrl):
    def __init__(self, subcls, parent, question, word):
        self.subcls = subcls
        super(RepeatableCtrl, self).__init__(parent, question, word)
    
    def setupControl(self):
        self.answers = self.get_answer()
        
        # import pdb
        # pdb.set_trace()
        
    
    def setInitialValue(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        for answer in self.answers:
            sizer.Add(RepeatableElement(self, answer, self.subcls))
        self.SetSizer(sizer)
        

class RepeatableElement(wx.Panel):
    def __init__(self, parent, answer, cls):
        super(RepeatableElement, self).__init__(parent, -1)
        
        # art = wx.ArtProvider()
        # up_bitmap = art.GetBitmap(wx.ART_GO_UP, wx.ART_FRAME_ICON, (16, 16))
        # down_bitmap = art.GetBitmap(wx.ART_GO_DOWN, wx.ART_FRAME_ICON, (16, 16))
        # new_bitmap = art.GetBitmap(wx.ART_NEW, wx.ART_FRAME_ICON, (16, 16))
        
        upBtn = wx.BitmapButton(self, -1, up_bitmap)
        downBtn = wx.BitmapButton(self, -1, down_bitmap)
        newBtn = wx.BitmapButton(self, -1, new_bitmap)
        
        wx.StaticText(self, -1, answer.value)