# app.py

r'''The main IDE application.'''

import sys, os
import itertools
import wx

import ucc.config
from ucc.gui import registry
from ucc.gui.frames.main_frame import MainFrame
from ucc.word import top_package, xml_access
from ucc.gui import debug

class App(wx.App):
    def __init__(self, packagePath=None, *args, **kwargs):
        debug.header('Application Started')
        self.packagePath = packagePath
        # init base class which calls self.OnInit()
        super(App, self).__init__(False, *args, **kwargs)
    
    def OnInit(self):
        self.SetAppName('ucc') # used by wx.StandardPaths
        
        # load configuration
        
        registry.config = ucc.config.load()
        debug.trace('Configration loaded')
        
        # setup registry
        
        registry.app = self
        
        # IDs for events
        
        registry.ID_OPEN  = wx.NewId()
        registry.ID_SAVE_ALL = wx.NewId()
        registry.ID_SAVE_WORD = wx.ID_SAVE
        registry.ID_COMPILE = wx.NewId()
        registry.ID_LOAD = wx.NewId()
        registry.ID_VERIFY = wx.NewId()
        registry.ID_PUSH = wx.NewId()
        registry.ID_ABOUT = wx.ID_ABOUT
        registry.ID_EXIT  = wx.ID_EXIT
        
        # standard app controls
        
        registry.mainFrame = None
        registry.mainMenuBar = None
        registry.mainToolbar = None
        registry.mainPanel = None
        registry.leftTreePanel = None
        registry.rightMainPanel = None
        registry.wordTreeCtrl = None
        
        # package information
        
        registry.mode = None           # current mode of operation
        registry.currentPackage = None # full absolute path to package directory
        registry.top_package = None    # ucc.word.top_package.top instance
        registry.currentWord = None    # current word loaded in rightMainPanel
        
        # process input arguments for package/mode, if not ask for package/mode
        
        if not self.packagePath:
            self.packagePath = self.pickMode()
        
        self.processPath(self.packagePath)
        self.initPackage()
        
        # setup the mainFrame to start the app
        
        registry.mainFrame = MainFrame(None, -1, u"\xb5CC Package Editor")
        self.SetTopWindow(registry.mainFrame)
        return True
    
    def pickMode(self):
        
        # TODO implement other modes besides editing package file
        # Shouldn't these just be options on the File menu?  -Bruce
        
        choiceDialog = wx.SingleChoiceDialog(None, 'Choose what mode you wish to be in. Not much of a choice for now but more to come soon. :)', 'Mode Selection', [
            # 'Create New Library',
            # 'Edit Library',
            # 'Create New Program',
            # 'Edit Program',
            # 'Install Program'
            'Edit Package'
        ])
        choiceDialog.ShowModal()
        mode = registry.mode = choiceDialog.GetStringSelection()
        choiceDialog.Destroy()
        
        # ask for file location
        
        if mode == 'Edit Package':
            fileDialog = wx.FileDialog(None, message='Please locate your package.xml file.', defaultDir=sys.path[0], wildcard="package.xml", style=wx.OPEN)
            if fileDialog.ShowModal() == wx.ID_OK:
                dirname = fileDialog.GetDirectory()
            else:
                raise Exception('Invalid file selection.')
            fileDialog.Destroy()
            
        # set information to registry
        
        return dirname
    
    def processPath(self, packagePath):
        
        # process into absolute path
        
        packagePath = os.path.abspath(packagePath)
        
        # process directory into file
        
        if os.path.isdir(packagePath):
            # if os.path.exists(os.path.join(packagePath, 'packages.xml')):
            #     packagePath = os.path.join(packagePath, 'packages.xml')
            if os.path.exists(os.path.join(packagePath, 'package.xml')):
                packagePath = os.path.join(packagePath, 'package.xml')
            else:
                raise Exception('Invalid package path.')
        
        # add into registry
        
        dirname, basename = os.path.split(packagePath)
        if basename == 'packages.xml' or basename == 'package.xml':
            registry.currentPackage = dirname
        else:
            raise Exception('Invalid package path.')
    
    def initPackage(self):
        r'''Read in ucclib.built_in and registry.currentPackage.
        
        Setup top_package.
        
        '''
        
        registry.top_package = top_package.top(registry.currentPackage)
    
    def onOpen(self, event):
        try:
            self.processPath(self.pickMode())
            self.initPackage()
            registry.mainFrame.paint()
        except:
            pass
    
    def onSaveWord(self, event):
        self.saveWord()
    
    def saveWord(self):
        if registry.currentWord and registry.currentWord.top:
            registry.currentWord.save()
            debug.success("Word %s saved" % registry.currentWord.name)
    
    def onAbout(self, event):
        dialog = wx.MessageDialog(
            registry.mainFrame,
            u"Package editing GUI for \xb5CC project.",
            "About",
            wx.OK
        )
        dialog.ShowModal()
        dialog.Destroy()
    
    def onCompile(self, event):
        from ucc.parser import compile
        compile.run(registry.top_package)
    
    def onLoad(self, event):
        from ucc.parser import load
        kw_args = dict((param, registry.config.get('arduino', param))
            for param in (
                'install_dir',
                'avrdude_port',
                'mcu',
                'avr_dude_path',
                'avr_config_path',
                'avrdude_programmer',
                'upload_rate'
            ) if registry.config.has_option('arduino', param)
        )
        load_path = registry.currentPackage
        for memory_type in 'flash', 'eeprom':
            if os.path.exists(os.path.join(load_path, memory_type + '.hex')):
                debug.trace("Loading " + memory_type + '.hex')
                load.run(load_path=load_path, memory_type=memory_type,
                         **kw_args)
    
    def onExit(self, event):
        registry.mainFrame.Close(True)
    
