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
import threading
from threading import Thread
import time


rxStyle = wx.TextAttr(
  colText = wx.Colour(100, 0, 0)
)
txStyle = wx.TextAttr(
  colText = wx.Colour(0, 0, 100)
)

parityMap = {
  'None':  serial.PARITY_NONE,
  'Even':  serial.PARITY_EVEN,
  'Odd':   serial.PARITY_ODD,
}

stopMap = {
  '1':   serial.STOPBITS_ONE,
  '2':   serial.STOPBITS_TWO
}

bytesizeMap = {
  '5': serial.FIVEBITS,
  '6': serial.SIXBITS,
  '7': serial.SEVENBITS,
  '8': serial.EIGHTBITS
}


class randtermFrame(wx.Frame, Thread):
  ##################################################
  def __init__(self, parent, title):
    Thread.__init__(self)
    wx.Frame.__init__(self, parent, title=title, size=(600, 400))

    self.cfg = wx.Config('randterm')

    self.historyLock = threading.Lock()
    self.history = []


    self.CreateStatusBar()
    # File Menu
    fileMenu = wx.Menu()
    menuAbout = fileMenu.Append(
      wx.ID_ABOUT, "&About", " Information about randterm")
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
    ## Output Type
    topSizer = wx.BoxSizer(wx.HORIZONTAL)
    self.displayTypeRadios = wx.RadioBox(self, wx.ID_ANY,
                                       style=wx.RA_HORIZONTAL, label="RX Format",
                                       choices = ('Ascii', 'Decimal', 'Hex', 'Binary'))
    self.Bind(wx.EVT_RADIOBOX, self.OnChangeDisplay, self.displayTypeRadios)
    topSizer.Add(self.displayTypeRadios, 0)
    self.clearOutputButton = wx.Button(self, id=wx.ID_ANY, label="Clear")
    self.Bind(wx.EVT_BUTTON, self.OnClearOutput, self.clearOutputButton)
    topSizer.AddStretchSpacer()
    topSizer.Add(self.clearOutputButton, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT )
    outputSizer.Add(topSizer, flag=wx.EXPAND)
    ## Output Area
    serialFont = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    self.serialOutput = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
    self.serialOutput.SetFont(serialFont)
    outputSizer.Add(self.serialOutput, 1, wx.EXPAND)
    mainSizer.Add(outputSizer, 1, wx.EXPAND)
    # Input Area
    lowerAreaSizer = wx.BoxSizer(wx.VERTICAL)
    ## LiveType
    liveTypeSizer = wx.BoxSizer(wx.HORIZONTAL)
    lowerAreaSizer.Add(liveTypeSizer)
    liveTypeSizer.Add(wx.StaticText(self, wx.ID_ANY, " LiveType: "))
    self.liveType = wx.TextCtrl(self, wx.ID_ANY, '',
                                style=wx.TE_LEFT|wx.TE_MULTILINE, size=(160,25))
    liveTypeSizer.Add(self.liveType)
    self.Bind(wx.EVT_TEXT, self.OnSendLiveType, self.liveType)
    ## Input Array
    lowerAreaSizer2 = wx.BoxSizer(wx.HORIZONTAL)
    lowerAreaSizer.Add(lowerAreaSizer2)
    inputAreasSizer = wx.BoxSizer(wx.VERTICAL)
    lowerAreaSizer2.Add(inputAreasSizer)
    self.inputAreas = []
    for i in range(1, 6):
      inputSizer = wx.BoxSizer(wx.HORIZONTAL)
      self.inputAreas.append(
        wx.TextCtrl(self, wx.ID_ANY, '',
                    style=wx.TE_LEFT|wx.TE_PROCESS_ENTER,
                    size=(200,25)))
      self.Bind(wx.EVT_TEXT_ENTER, self.OnSendInput, self.inputAreas[-1])
      inputSizer.Add(wx.StaticText(self, wx.ID_ANY, " " + str(i)+" : "))
      inputSizer.Add(self.inputAreas[-1], 4)
      inputAreasSizer.Add(inputSizer)
    ## Input Type Radios
    self.inputTypeRadios = wx.RadioBox(self, wx.ID_ANY,
                                       style=wx.RA_VERTICAL, label="TX Format",
                                       choices = ('Ascii', 'Decimal', 'Hex', 'Binary'),
                                       size=(100,25*len(self.inputAreas)))
    lowerAreaSizer2.Add(self.inputTypeRadios)
    # Connect Quick Buttons
    connectButtonSizer = wx.BoxSizer(wx.VERTICAL)
    self.connectButton = wx.Button(self, id=wx.ID_ANY, label="  Disconnect  ")
    self.connectButton.SetBackgroundColour(wx.Colour(255, 0, 0))
    self.Bind(wx.EVT_BUTTON, self.OnToggleConnectButton, self.connectButton)
    connectButtonSizer.Add(self.connectButton)
    lowerAreaSizer2.Add(connectButtonSizer)
    mainSizer.Add(lowerAreaSizer, 0)

    # Setup and get ready to roll
    self.serialCon = serial.Serial()
    self.SetStatusText('Not Connected...')
    self.SetSizer(mainSizer)
    self.Show(True)
    self.connected = False
    self.start()
    self.connectButton.SetLabel("Connect")


  ##################################################
  def OnChangeDisplay(self, event):
    """Gets called when the user changes the display format"""
    self.serialOutput.Clear()
    self.historyLock.acquire()
    self.appendToDisplay(self.history)
    self.historyLock.release()

  ##################################################
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

  ##################################################
  def run(self):
    """The runtime thread to pull data from the open serial port"""
    while True:
      if self.connected:

        try:
          byte = self.serialCon.read()
        except:
          self.connected = False
          self.SetStatusText('Not Connected...')
          continue

        if byte != '':
          historyEntry = {'type':'RX', 'data':byte}
          self.historyLock.acquire()
          self.history.append(historyEntry)
          self.historyLock.release()
          wx.CallAfter(self.appendToDisplay,[historyEntry])
      else:
        time.sleep(.2)


  ##################################################
  def intToBinString(self,n):
    string = ''
    for i in range(0, 8):
      if (n&1): string = '1' + string
      else:     string = '0' + string
      n = n >> 1
    return string

  ##################################################
  def appendToDisplay(self, newEntries):
    if newEntries == None:
      return

    typeString = self.displayTypeRadios.GetStringSelection()

    entryCopies = []

    if typeString == 'Ascii':
      entryCopies = newEntries
    else:
      trans = None
      if(typeString   == 'Binary'):
        trans = self.intToBinString
      elif(typeString == 'Decimal'):
        trans = str
      elif(typeString == 'Hex'):
        trans = hex
      for entry in newEntries:
        entryCopies.append({'type':entry['type'], 'data':trans(ord(entry['data']))})

    for entry in entryCopies:
      # Set the proper output color
      if(entry['type'] == 'RX'):
        self.serialOutput.SetDefaultStyle(rxStyle)
      else:
        self.serialOutput.SetDefaultStyle(txStyle)

      # If the byte to show isn't valid ascii, then just print out ascii 1
      # as a placeholder
      try:
        self.serialOutput.AppendText(entry['data'])
      except:
        self.serialOutput.AppendText(chr(1))

      if typeString != 'Ascii':
        self.serialOutput.AppendText(' ')


  ##################################################
  def OnSetPort(self, event):
    self.portName = wx.GetTextFromUser('Port: ', 'Select Port Name', self.portName)

  ##################################################
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
    self.connected = True
    self.connectButton.SetBackgroundColour(wx.Colour(0, 255, 0))
    self.connectButton.SetLabel("Disconnect")

  ##################################################
  def OnClearOutput(self, event):
    self.historyLock.acquire()
    self.serialOutput.Clear()
    self.history = []
    self.historyLock.release()

  ##################################################
  def OnCloseConnection(self, event):
    self.connected = False

    self.serialCon.close()

    self.SetStatusText('Not Connected...')
    self.connectButton.SetBackgroundColour(wx.Colour(255, 0, 0))
    self.connectButton.SetLabel("Connect")

  ##################################################
  def OnSendLiveType(self, event):
    inputArea = event.GetEventObject()
    inputString = str(inputArea.GetString(0,-1))
    if inputString == "":
      return
    inputArea.Clear()
    if self.serialCon.isOpen():
      newHistoryVals = []
      for c in inputString:
        newHistoryVals.append({'type':'TX', 'data':c})

      self.historyLock.acquire()
      self.history = self.history + newHistoryVals
      self.historyLock.release()
      self.appendToDisplay(newHistoryVals)
      self.serialCon.write(inputString)

  ##################################################
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
        numString = numString.strip()
        if numString == '': continue
        intVal = int(numString, base)
        inputVal += chr(intVal)
      
    if self.serialCon.isOpen():
      newHistoryVals = []
      for c in inputVal:
        newHistoryVals.append({'type':'TX', 'data':c})
      self.historyLock.acquire()
      self.history = self.history + newHistoryVals
      self.historyLock.release()
      self.serialCon.write(inputVal)
      self.appendToDisplay(newHistoryVals)

  ##################################################
  def OnAbout(self, event):
    dlg = wx.MessageDialog(self, "A set of useful serial utilities by "
                                 "Randolph Voorhies (rand.voorhies@gmail.com)\n"
                                 "http://ilab.usc.edu/~rand",
                                 "About randterm", wx.OK)
    dlg.ShowModal()
    dlg.Destroy()

  ##################################################
  def OnExit(self, e):
    self.Close(True)

  ##################################################
  def OnToggleConnectButton(self, event):
    if(self.connected):
      self.OnCloseConnection(None)
    else:
      self.OnSetConnection(None)


app = wx.App(False)
frame = randtermFrame(None, "randterm")
app.MainLoop()
