# bottom_text_ctrl.py

r'''Text control for editing word code.'''

import wx, wx.py
from ucc.gui import registry, debug

class BottomTextCtrl(wx.py.editwindow.EditWindow):
    def __init__(self, *args, **kwargs):
        super(BottomTextCtrl, self).__init__(*args, **kwargs)
        
        self.setDisplayLineNumbers(True)
        self.Bind(wx.EVT_KEY_DOWN, self.onBottomTextChange)
    
    def onBottomTextChange(self, event):
        debug.notice('BottomTextCtrlL: Update event!')
        registry.currentWord.source_text = self.GetText()
        registry.currentWord.set_save_state(False)
        event.Skip() # CLEAN not sure if this is needed
    
    def LoadFile(self, source_filename):
        super(BottomTextCtrl, self).LoadFile(source_filename)
        registry.currentWord.source_text = self.GetText()
    
