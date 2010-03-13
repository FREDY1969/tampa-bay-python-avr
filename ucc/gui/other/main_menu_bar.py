# main_menu_bar.py

import wx
from ucc.gui import registry

class MainMenuBar(wx.MenuBar):
    def __init__(self, parent):
        super(MainMenuBar, self).__init__()
        self.parent = parent
        
        # setup menu
        
        filemenu = wx.Menu()
        filemenu.Append(registry.ID_OPEN, "&Open Package\tCtrl+O", "Open a \xb5CC package")
        filemenu.Append(registry.ID_SAVE_WORD, "&Save Word\tCtrl+S", "Save the Current Word")
        filemenu.AppendSeparator()
        filemenu.Append(registry.ID_COMPILE, "&Compile Program\tCtrl+C",
                        "Compile the Program in the current Package")
        filemenu.Append(registry.ID_LOAD, "&Load Program\tCtrl+L",
                        "Load the compiled program onto the microcontroller")
        filemenu.AppendSeparator()
        filemenu.Append(registry.ID_EXIT, "E&xit", "Terminate \xb5CC Package Editor.")
        
        helpmenu = wx.Menu()
        helpmenu.Append(registry.ID_ABOUT, "&About")
        
        self.Append(filemenu, "&File")
        self.Append(helpmenu, "&Help")
        
        self.setupEventHandlers()
        
    def setupEventHandlers(self):
        wx.EVT_MENU(self.parent, registry.ID_OPEN, registry.app.onOpen)
        wx.EVT_MENU(self.parent, registry.ID_SAVE_WORD, registry.app.onSaveWord)
        wx.EVT_MENU(self.parent, registry.ID_COMPILE, registry.app.onCompile)
        wx.EVT_MENU(self.parent, registry.ID_LOAD, registry.app.onLoad)
        wx.EVT_MENU(self.parent, registry.ID_EXIT, registry.app.onExit)
        wx.EVT_MENU(self.parent, registry.ID_ABOUT, registry.app.onAbout)
