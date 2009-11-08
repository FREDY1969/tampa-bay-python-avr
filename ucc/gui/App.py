# App.py

r'''
'''

import sys
import os.path
import ConfigParser
import wx

from ucc.gui.Registry import Registry
from ucc.gui.MainFrame import MainFrame
from ucc.word import word, xml_access

class App(wx.App):
    def __init__(self):

        # init parent (which calls self.OnInit()...)

        wx.App.__init__(self, False)

    def OnInit(self):

        self.SetAppName('ucc')         # used by wx.StandardPaths

        # load StandardPaths

        Registry.paths = wx.StandardPaths.Get()

        # load configuration

        if sys.platform.startswith('win') or \
           sys.platform in ('os2', 'os2emx', 'riscos', 'atheos'):
            configFile = 'ucc.ini'
        else:
            configFile = '.ucc.ini'
        configPath = os.path.join(Registry.paths.GetUserConfigDir(), configFile)
        print "configPath", configPath
        if not os.path.exists(configPath):
            # This may need to be changed eventually to support zipped
            # installations of this compiler.
            defaultFile = os.path.join(sys.path[0], 'ucc', 'ucc-default.ini')
            from distutils import file_util
            file_util.copy_file(defaultFile, configPath)
        Registry.config = ConfigParser.RawConfigParser()
        Registry.config.read(configPath)
        #Registry.config.get('gui', 'editor')

        # setup registry

        Registry.app = self

        # IDs for events

        Registry.ID_OPEN  = wx.NewId()
        Registry.ID_SAVE_ALL = wx.NewId()
        Registry.ID_SAVE_WORD = wx.NewId()
        Registry.ID_VERIFY = wx.NewId()
        Registry.ID_COMPILE = wx.NewId()
        Registry.ID_PUSH = wx.NewId()
        Registry.ID_ABOUT = wx.NewId()
        Registry.ID_EXIT  = wx.NewId()

        # standard app controls

        Registry.mainFrame = None
        Registry.mainMenuBar = None
        Registry.mainToolbar = None
        Registry.mainPanel = None
        Registry.leftTreePanel = None
        Registry.rightMainPanel = None
        Registry.wordTreeCtrl = None

        # package information

        Registry.mode = None           # current mode of operation
        Registry.currentPackage = None # full absolute path to package directory
        Registry.words = None          # multidimensional list of words
        Registry.wordList = None       # list of words
        Registry.wordDict = None       # {name: word}
        Registry.currentWord = None    # current word loaded in rightMainPanel
        Registry.currentWordPath = None # path to current word text file
        Registry.parentWord = None     # parent word of current word

        # process input arguments for package/mode, if not ask for package/mode

        try:
            packagePath = sys.argv[1]
        except IndexError:
            packagePath = self.pickMode()

        self.processPath(packagePath)
        self.initPackage()

        # setup the mainFrame to start the app

        Registry.mainFrame = MainFrame(None, wx.ID_ANY, u"\xb5CC Package Editor")
        self.SetTopWindow(Registry.mainFrame)
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
        mode = Registry.mode = choiceDialog.GetStringSelection()
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
            Registry.currentPackage = dirname
        else:
            raise Exception('Invalid package path.')

    def initPackage(self):

        # setup wordlist

        Registry.wordList = []
        Registry.wordDict = {}

        def add_words(package_dir):
            words = xml_access.read_word_list(package_dir)[1]
            Registry.wordList.extend(words)
            Registry.wordDict.update((name, word.read_word(name, package_dir))
                                     for name in words)
        add_words(Registry.currentPackage)

    def onOpen(self, event):
        try:
            self.processPath(self.pickMode())
            self.initPackage()
            Registry.mainFrame.paint()
        except:
            pass

    def onSaveWord(self, event):
        self.saveWord()

    def saveWord(self):
        print "saving word"
        if Registry.currentWord:
            Registry.currentWord.write_xml(Registry.currentPackage)
            if Registry.currentWordPath:
                Registry.rightMainPanel.bottomText.SaveFile(
                  Registry.currentWordPath)

    def onAbout(self, event):
        dialog = wx.MessageDialog(
            Registry.mainFrame,
            u"Package editing GUI for \xb5CC project.",
            "About",
            wx.OK
        )
        dialog.ShowModal()
        dialog.Destroy()

    def onExit(self, event):
        Registry.mainFrame.Close(True)

