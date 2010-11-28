#!/usr/bin/env python

#  Copyright 2010 Randolph C Voorhies
#  http://ilab.usc.edu/~rand
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
import serial
from threading import Thread
import time

parityMap = {
  'None':  serial.PARITY_NONE,
  'Even':  serial.PARITY_EVEN,
  'Odd':   serial.PARITY_ODD,
  'Mark':  serial.PARITY_MARK,
  'Space': serial.PARITY_SPACE
}

stopMap = {
  '1':   serial.STOPBITS_ONE,
  '1.5': serial.STOPBITS_ONE_POINT_FIVE,
  '2':   serial.STOPBITS_TWO
}

bytesizeMap = {
  '5': serial.FIVEBITS,
  '6': serial.SIXBITS,
  '7': serial.SEVENBITS,
  '8': serial.EIGHTBITS
}


class RandTermFrame(wx.Frame, Thread):
  def __init__(self, parent, title):
    Thread.__init__(self)
    wx.Frame.__init__(self, parent, title=title, size=(600, 400))

    self.cfg = wx.Config('randterm')

    self.rxBuffer = ''

    self.CreateStatusBar()
    # File Menu
    fileMenu = wx.Menu()
    menuAbout = fileMenu.Append(
      wx.ID_ABOUT, "&About", " Information about RandTerm")
    self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
    menuExit = fileMenu.Append(wx.ID_EXIT, "E&xit", " Exit")
    self.Bind(wx.EVT_MENU, self.OnExit, menuExit)

    # Connect Menu
    self.connectMenu = wx.Menu()
    ## Port Selection
    self.setPort = self.connectMenu.Append(wx.ID_ANY, 'Set Port...')
    self.Bind(wx.EVT_MENU, self.OnSetPort, self.setPort)
    self.connectMenu.AppendSeparator()
    self.portName = ""
    ## Baud SubMenu
    self.baudRadios = []
    self.baudMenu = wx.Menu()
    self.baudRadios.append(self.baudMenu.AppendRadioItem(wx.ID_ANY, '2400'))
    self.baudRadios.append(self.baudMenu.AppendRadioItem(wx.ID_ANY, '4800'))
    self.baudRadios.append(self.baudMenu.AppendRadioItem(wx.ID_ANY, '9600'))
    self.baudRadios.append(self.baudMenu.AppendRadioItem(wx.ID_ANY, '19200'))
    self.baudRadios.append(self.baudMenu.AppendRadioItem(wx.ID_ANY, '38400'))
    self.baudRadios.append(self.baudMenu.AppendRadioItem(wx.ID_ANY, '57600'))
    self.baudRadios.append(self.baudMenu.AppendRadioItem(wx.ID_ANY, '115200'))
    self.baudRadios.append(self.baudMenu.AppendRadioItem(wx.ID_ANY, '312500'))
    self.connectMenu.AppendMenu(wx.ID_ANY, 'Baud Rate',     self.baudMenu)
    ## Parity SubMenu
    self.parityRadios = []
    self.parityMenu = wx.Menu()
    for k,v in parityMap.items():
      self.parityRadios.append(self.parityMenu.AppendRadioItem(wx.ID_ANY, k))
    self.connectMenu.AppendMenu(wx.ID_ANY, 'Parity',        self.parityMenu)
    ## Byte Size SubMenu
    self.byteRadios = []
    self.byteMenu = wx.Menu()
    for k,v in bytesizeMap.items():
      self.byteRadios.append(self.byteMenu.AppendRadioItem(wx.ID_ANY, k))
    self.connectMenu.AppendMenu(wx.ID_ANY, 'Byte Size',     self.byteMenu)
    ## Stop Bits SubMenu
    self.stopbitsRadios = []
    self.stopbitsMenu = wx.Menu()
    for k,v in stopMap.items():
      self.stopbitsRadios.append(self.stopbitsMenu.AppendRadioItem(wx.ID_ANY, k))
    self.connectMenu.AppendMenu(wx.ID_ANY, 'Stop Bits',     self.stopbitsMenu)
    ## Flow Control SubMenu
    self.flowMenu = wx.Menu()
    self.xonoffCheck = self.flowMenu.AppendCheckItem(wx.ID_ANY, 'Xon/Xoff')
    self.rtsctsCheck = self.flowMenu.AppendCheckItem(wx.ID_ANY, 'RTS/CTS')
    self.dsrdtrCheck = self.flowMenu.AppendCheckItem(wx.ID_ANY, 'DSR/DTR')
    self.connectMenu.AppendMenu(wx.ID_ANY, 'Flow Control',  self.flowMenu)
    ## Open Connection Item
    self.connectMenu.AppendSeparator()
    openConnection  = self.connectMenu.Append(
      wx.ID_ANY, '&Open Connection', 'Open Connection')
    self.Bind(wx.EVT_MENU, self.OnSetConnection, openConnection)
    closeConnection = self.connectMenu.Append(
      wx.ID_ANY, '&Close Connection', 'Close Connection')
    self.Bind(wx.EVT_MENU, self.OnCloseConnection, closeConnection)
    # Menu Bar
    menuBar = wx.MenuBar()
    menuBar.Append(fileMenu,    "&File")
    menuBar.Append(self.connectMenu, "&Connect")
    self.SetMenuBar(menuBar)

    # Setup the defaults
    self.readDefaults()

    # Main Window
    mainSizer = wx.BoxSizer(wx.VERTICAL)
    # Serial Output Area
    outputSizer = wx.BoxSizer(wx.VERTICAL)
    self.displayTypeRadios = wx.RadioBox(self, wx.ID_ANY,
                                       style=wx.RA_HORIZONTAL, label="Display Type",
                                       choices = ('Ascii', 'Decimal', 'Hex', 'Binary'))
    self.Bind(wx.EVT_RADIOBOX, self.OnChangeDisplay, self.displayTypeRadios)
    outputSizer.Add(self.displayTypeRadios, 0, wx.EXPAND)
    serialFont = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    self.serialOutput = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
    self.serialOutput.SetFont(serialFont)
    outputSizer.Add(self.serialOutput, 1, wx.EXPAND)
    mainSizer.Add(outputSizer, 1, wx.EXPAND)
    # Input Area
    lowerAreaSizer = wx.BoxSizer(wx.HORIZONTAL)
    inputAreasSizer = wx.BoxSizer(wx.VERTICAL)
    self.inputAreas = []
    for i in range(0, 5):
      self.inputAreas.append(
        wx.TextCtrl(self, wx.ID_ANY, '', style=wx.TE_LEFT|wx.TE_PROCESS_ENTER, size=(200,25)))
      self.Bind(wx.EVT_TEXT_ENTER, self.OnSendInput, self.inputAreas[-1])
      inputAreasSizer.Add(self.inputAreas[-1], 4)
    lowerAreaSizer.Add(inputAreasSizer)
    self.inputTypeRadios = wx.RadioBox(self, wx.ID_ANY,
                                       style=wx.RA_VERTICAL, label="Input Type",
                                       choices = ('Ascii', 'Decimal', 'Hex', 'Binary'),
                                       size=(100,25*len(self.inputAreas)))
    lowerAreaSizer.Add(self.inputTypeRadios)
    mainSizer.Add(lowerAreaSizer, 0)

    # Setup and get ready to roll
    self.serialCon = serial.Serial()
    self.SetStatusText('Not Connected...')
    self.SetSizer(mainSizer)
    self.Show(True)

  def OnChangeDisplay(self, event):
    """Gets called when the user changes the display format"""
    print 'changing display'
    self.serialOutput.Clear()
    typeString = self.displayTypeRadios.GetStringSelection()
    self.appendToDisplay(self.rxBuffer)

  def readDefaults(self):
    menumap = {
      'baud'     : self.baudMenu,
      'parity'   : self.parityMenu,
      'bytesize' : self.byteMenu,
      'stopbits' : self.stopbitsMenu
    }
    for k, v in menumap.items():
      if self.cfg.Exists(k):
        default = self.cfg.Read(k)
        for item in v.GetMenuItems():
          if item.GetLabel() == default:
            item.Check(True)

    for item in self.flowMenu.GetMenuItems():
        item.Check(self.cfg.ReadBool(item.GetLabel(), defaultVal=False))

    if self.cfg.Exists('portname'):
      self.portName = self.cfg.Read('portname')

  def run(self):
    """The runtime thread to pull data from the open serial port"""
    while self.running:
      byte = self.serialCon.read()
      self.rxBuffer += byte
      wx.CallAfter(self.appendToDisplay,byte)

  def appendToDisplay(self, newBytes):
    if newBytes == '':
      return

    typeString = self.displayTypeRadios.GetStringSelection()

    if(typeString == 'Ascii'):
      self.serialOutput.AppendText(newBytes)
    else:
      trans = None
      if(typeString   == 'Binary'):
        trans = lambda n: n>0 and trans(n>>1).lstrip('0')+str(n&1) or '0'
      elif(typeString == 'Decimal'):
        trans = str
      elif(typeString == 'Hex'):
        trans = hex
      newStr=''
      for b in newBytes:
        newStr += trans(ord(b)) + ' '
      self.serialOutput.AppendText(newStr)


  def OnSetPort(self, event):
    self.portName = wx.GetTextFromUser('Port: ', 'Select Port Name', self.portName)

  def OnSetConnection(self, event):
    if self.portName == "":
      self.OnSetPort(None)
      return

    baudRadio   = None
    for b in self.baudRadios:   
      if b.IsChecked(): baudRadio   = b
    parityRadio = None
    for p in self.parityRadios:
      if p.IsChecked(): parityRadio = p
    byteRadio   = None
    for b in self.byteRadios:
      if b.IsChecked(): byteRadio   = b
    stopRadio   = None
    for s in self.stopbitsRadios:
      if s.IsChecked(): stopRadio   = s

    self.serialCon = serial.Serial()
    self.serialCon.port     = self.portName
    self.serialCon.baudrate = int(baudRadio.GetLabel())
    self.serialCon.bytesize = bytesizeMap[byteRadio.GetLabel()]
    self.serialCon.parity   = parityMap[parityRadio.GetLabel()]
    self.serialCon.stopbits = stopMap[stopRadio.GetLabel()]
    self.serialCon.xonxoff  = self.xonoffCheck.IsChecked()
    self.serialCon.rtscts   = self.rtsctsCheck.IsChecked()
    self.serialCon.dsrdtr   = self.dsrdtrCheck.IsChecked()
    self.serialCon.timeout  = .3

    self.cfg.Write('portname', self.portName)
    self.cfg.Write('baud',     baudRadio.GetLabel())
    self.cfg.Write('parity',   parityRadio.GetLabel())
    self.cfg.Write('bytesize', byteRadio.GetLabel())
    self.cfg.Write('stopbits', stopRadio.GetLabel())
    for item in self.flowMenu.GetMenuItems():
      self.cfg.WriteBool(item.GetLabel(),item.IsChecked())





    try:
      self.serialCon.open()
    except serial.SerialException as ex:
      wx.MessageDialog(None, str(ex), 'Serial Error', wx.OK | wx.ICON_ERROR).ShowModal()
      self.SetStatusText('Not Connected...')
      return

    self.SetStatusText('Connected to ' + self.portName + ' ' + baudRadio.GetLabel() + 'bps')
    self.running = True
    self.start()

  def OnCloseConnection(self, event):
    self.running = False
    self.join()
    self.serialCon.close()
    self.SetStatusText('Not Connected...')

  def OnSendInput(self, event):
    inputArea = event.GetEventObject()
    inputArea.SetSelection(0,-1)
    inputString = inputArea.GetString(0,-1)

    inputVal = ''
    typeString = self.inputTypeRadios.GetStringSelection()

    if(typeString == 'Ascii'):
      inputVal = str(inputString)
    else:
      base = 0
      if(typeString   == 'Binary'):
        base = 2
      elif(typeString == 'Decimal'):
        base = 10
      elif(typeString == 'Hex'):
        base = 16
      numStrings = inputString.split(" ")
      for numString in numStrings:
        intVal = int(numString, base)
        inputVal += chr(intVal)
      
    if self.serialCon.isOpen():
      self.serialCon.write(inputVal)

  def OnAbout(self, event):
    dlg = wx.MessageDialog(self, "A set of useful serial utilities by "
                                 "Randolph Voorhies (rand.voorhies@gmail.com)",
                                 "About RandTerm", wx.OK)
    dlg.ShowModal()
    dlg.Destroy()

  def OnExit(self, e):
    self.Close(True)


app = wx.App(False)
frame = RandTermFrame(None, "RandTerm")
app.MainLoop()
