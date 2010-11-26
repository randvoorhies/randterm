#!/usr/bin/env python

#  Copyright 2010 Randolph C Voorhies
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import wx



class RandTermFrame(wx.Frame):
  def __init__(self, parent, title):

    wx.Frame.__init__(self, parent, title=title, size=(200, 400))
    
    self.control = wx.TextVtrl(self, style=wx.TE_MULTILINE)

    self.CreateStatusBar()

    # File Menu
    fileMenu = wx.Menu()
    menuAbout = fileMenu.Append(
      wx.ID_ABOUT, "&About", " Information about RandTerm")
    menuExit = fileMenu.Append(wx.ID_EXIT, "E&xit", " Exit")

    # Connect Menu
    self.connectMenu = wx.Menu()
    ## Port SubMenu
    self.portMenu = wxMenu()
    self.portMenu.Append(wx_IDANY, 'Reload Port List')
    self.portMenu.AppendSeparator()
    ## Baud SubMenu
    self.baudMenu = wxMenu()
    self.baudMenu.AppendRadioItem(wx_IDANY, '2400')
    self.baudMenu.AppendRadioItem(wx_IDANY, '4800')
    self.baudMenu.AppendRadioItem(wx_IDANY, '9600')
    self.baudMenu.AppendRadioItem(wx_IDANY, '19200')
    self.baudMenu.AppendRadioItem(wx_IDANY, '38400')
    self.baudMenu.AppendRadioItem(wx_IDANY, '57600')
    self.baudMenu.AppendRadioItem(wx_IDANY, '115200')
    self.baudMenu.AppendRadioItem(wx_IDANY, '31250')
    ## Flow Control SubMenu
    self.flowMenu.AppendRadioItem(wx_IDANY, 'Hard')
    self.flowMenu.AppendRadioItem(wx_IDANY, 'Soft')
    self.flowMenu.AppendRadioItem(wx_IDANY, 'None')
    ## Parity SubMenu
    self.parityMenu.AppendRadioItem(wx_IDANY, 'Odd')
    self.parityMenu.AppendRadioItem(wx_IDANY, 'Even')
    self.parityMenu.AppendRadioItem(wx_IDANY, 'None')
    ## Byte Size SubMenu
    self.byteMenu.AppendRadioItem(wx_IDANY, '7')
    self.byteMenu.AppendRadioItem(wx_IDANY, '8')
    self.byteMenu.AppendRadioItem(wx_IDANY, '9')
    # Connect Menu Setup
    self.connectMenu.Append(portMenu,   "Port")
    self.connectMenu.Append(baudMenu,   "Baud Rate")
    self.connectMenu.Append(flowMenu,   "Flow Control")
    self.connectMenu.Append(parityMenu, "Parity")
    self.connectMenu.Append(byteMenu,   "Byte Size")

    # Menu Bar
    menuBar = wx.MenuBar()
    menuBar.Append(fileMenu,    "&File")
    menuBar.Append(connectMenu, "&Connect")
    self.SetMenuBar(menuBar)

    # Bind Events
    self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
    self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
    
    self.Show(True)

  def OnAbout(self, even):
    dlg = wx.MessageDialog(self, "A set of useful serial utilities.", "About RandTerm", wx.OK)
    dlg.ShowModal()
    dlg.Destroy()

  def OnExit(self, e):
    self.Close(True)


app = wx.App(False)
frame = wx.MainFrame(None, "RandTerm")
app.MainLoop()
