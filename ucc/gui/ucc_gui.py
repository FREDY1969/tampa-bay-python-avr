#!/usr/bin/python

import os

import sqlite3

import wx
import wx.aui

#from print_r import print_r

# globals

global db_conn
global leftTreePanel


class UccApp(wx.App):
	def OnInit(self):
		frame = MainWindow(None, wx.ID_ANY, u"\xb5CC Databse Editor")
		self.SetTopWindow(frame)
		return True


class MainWindow(wx.Frame):
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, id, title,
			size = (970, 720),
			style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
		)
		self.SetMinSize((970,720))
		
		# setup status bar
		
		self.CreateStatusBar()
		
		# setup menu bar
		
		self.menubar = MainMenuBar(self)
		self.SetMenuBar(self.menubar)
		
		# setup toolbar
		
		toolbar = self.CreateToolBar(style= wx.TB_HORIZONTAL)
		toolbar.AddLabelTool(self.menubar.ID_OPEN, '', wx.Bitmap('images/icons/folder-horizontal-open.png'))
		toolbar.Realize()
		
		self.Bind(wx.EVT_TOOL, self.menubar.OnOpen, id=self.menubar.ID_OPEN)
		
		# setup splitter/sizers
		
		splitter = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3D)
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		# setup panels
		
		global leftTreePanel
		leftTreePanel = LeftTreePanel(splitter, wx.ID_ANY, style=wx.BORDER_SUNKEN | wx.WANTS_CHARS)
		rightMainPanel = RightMainPanel(splitter, wx.ID_ANY, style=wx.BORDER_SUNKEN)
		
		# setup splitter/sizers
		
		splitter.SetMinimumPaneSize(200)
		splitter.SplitVertically(leftTreePanel, rightMainPanel, 250)
		
		sizer.Add(toolbar, 0, wx.EXPAND)
		sizer.Add(splitter, 1, wx.EXPAND)
		
		self.SetSizer(sizer)
		sizer.Fit(self)
		self.Fit()
		
		# show frame
		
		self.Show(True)


class MainMenuBar(wx.MenuBar):
	def __init__(self, parent):
		wx.MenuBar.__init__(self)
		self.parent = parent
		
		# setup menu
		
		self.ID_OPEN  = wx.NewId()
		self.ID_EXIT  = wx.NewId()
		self.ID_ABOUT = wx.NewId()
		
		filemenu = wx.Menu()
		filemenu.Append(self.ID_OPEN, "&Open Database", "Open a database.")
		filemenu.AppendSeparator()
		filemenu.Append(self.ID_EXIT, "E&xit", "Terminate this program.")
		
		helpmenu = wx.Menu()
		helpmenu.Append(self.ID_ABOUT, "&About")
		
		self.Append(filemenu, "&File")
		self.Append(helpmenu, "&Help")
		
		self.SetupEventHandlers()
		
	def SetupEventHandlers(self):
		wx.EVT_MENU(self.parent, self.ID_OPEN, self.OnOpen)
		wx.EVT_MENU(self.parent, self.ID_EXIT, self.OnExit)
		wx.EVT_MENU(self.parent, self.ID_ABOUT, self.OnAbout)
		
	def OnOpen(self, event):
		dirname = ''
		dlg = wx.FileDialog(self, "Choose a database file", dirname, "", "*.db", wx.OPEN)
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetFilename()
			dirname = dlg.GetDirectory()
			fullFilePath = os.path.join(dirname, filename)
			
			global db_conn
			db_conn = sqlite3.connect(fullFilePath)
			leftTreePanel.DrawTree(filename)
			
		dlg.Destroy()
		
	def OnAbout(self, event):
		d = wx.MessageDialog(
			self,
			u"Database editing GUI for \xb5CC project.",
			"About",
			wx.OK
		)
		d.ShowModal()
		d.Destroy()
		
	def OnExit(self, event):
		self.parent.Close(True)


class LeftTreePanel(wx.Panel):
	def __init__(self, parent, id, style):
		wx.Panel.__init__(self, parent, id, style=style)
		
		# setup components
		
		label = wx.StaticText(self, wx.ID_ANY, "Words", style=wx.ALIGN_CENTER)
		tree = self.tree = WordTreeCtrl(self, wx.ID_ANY, wx.DefaultPosition, (300,300), wx.TR_DEFAULT_STYLE)
		tree.SetBackgroundColour(wx.WHITE)
		
		# setup sizer
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(label, 0, wx.EXPAND)
		sizer.Add(tree, 1, wx.EXPAND)
		
		self.SetSizer(sizer)
		sizer.Fit(self)
		self.Fit()
		
		self.DrawTree()
		
	def DrawTree(self, dbFilename='Undefined Database'):
		
		try:
			self.tree.DeleteAllItems()
			tree = self.tree
		except:
			pass
			
		root = tree.AddRoot(dbFilename)
		tree.UpdateWordTree()


class RightMainPanel(wx.Panel):
	def __init__(self, parent, id, style):
		wx.Panel.__init__(self, parent, id, style=style)
		
		# setup panels
		
		topPanel = wx.Panel(self, wx.ID_ANY)
		
		# setup controls
		
		topSizer = wx.BoxSizer(wx.VERTICAL)
		topSizer.Add(wx.StaticText(topPanel, wx.ID_ANY, "TopPanel"))
		topSizer.Add(wx.RadioButton(topPanel, -1, 'Value A', style=wx.RB_GROUP))
		topSizer.Add(wx.RadioButton(topPanel, -1, 'Value B'))
		topSizer.Add(wx.RadioButton(topPanel, -1, 'Value C'))
		topSizer.Add(wx.CheckBox(topPanel, wx.ID_ANY, 'CheckBox'))
		topSizer.Add(wx.Slider(topPanel, wx.ID_ANY, style=wx.SL_HORIZONTAL))
		topSizer.Add(wx.TextCtrl(topPanel, wx.ID_ANY))
		topSizer.Add(wx.BitmapButton(topPanel, wx.ID_ANY, wx.Bitmap('images/icons/arrow-090.png')))
		topSizer.Add(wx.BitmapButton(topPanel, wx.ID_ANY, wx.Bitmap('images/icons/arrow-270.png')))
		topSizer.Add(wx.ComboBox(topPanel, wx.ID_ANY, choices=['Option 1','Option 2']))
		topPanel.SetSizer(topSizer)
		
		bottomText = wx.TextCtrl(self, wx.ID_ANY, "Optional Code Goes Here", style=wx.TE_MULTILINE)
		
		# setup sizer
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(topPanel, 1, wx.EXPAND)
		sizer.Add(bottomText, 1, wx.EXPAND)
		
		self.SetSizer(sizer)
		sizer.Fit(self)
		self.Fit()


class WordTreeCtrl(wx.TreeCtrl):
	def __init__(self, parent, id, pos, size, style):
		wx.TreeCtrl.__init__(self, parent, id, pos, size, style)
	
	def UpdateWordTree(self):
		root = self.root = self.GetRootItem()
		words = self.words = []
		self.expandThese = [root]
		
		try:
			db_cur = db_conn.cursor()
			db_cur.execute("SELECT * FROM word")
			
			for word in db_cur:
				if word[0] == word[2]:
					words.append({
						'record': word,
						'children': []
					})
			for word in words:
				self.GetChildWords(word)
		except:
			pass
		
		self.BuildWordTree(words, root)
		self.ExpandThem()
	
	def GetChildWords(self, word):
		db_cur = db_conn.cursor()
		db_cur2 = db_conn.cursor()
		
		db_cur.execute("SELECT * FROM word WHERE kind = %d" % word['record'][0])
		for childWordRecord in db_cur:
			if (childWordRecord[0] != childWordRecord[2]):
				childWord = {
					'record': childWordRecord,
					'children': []
				}
				word['children'].append(childWord)
				db_cur2.execute("SELECT * FROM word WHERE kind = %d" % childWord['record'][0])
				for i in db_cur2:
					self.GetChildWords(childWord)
					break
	
	def BuildWordTree(self, words, parent):
		for word in words:
			wordNode = self.AppendItem(parent, word['record'][1])
			if (parent == self.root):
				self.expandThese.append(wordNode)
			self.BuildWordTree(word['children'], wordNode)
			
	def ExpandThem(self):
		for node in self.expandThese:
			self.Expand(node)


def run():
	app = UccApp()
	app.MainLoop()

if __name__ == '__main__':
	run()