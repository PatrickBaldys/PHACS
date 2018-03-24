#######################
#IMPORTS

# imports for SPI / Thermostats and General
from os import system


import time

system("sudo pigpiod -s 10") #make sure pigpio daemon is started
import pigpio


import get_temp3 as Temps
import PID 


# imports for pyqtgui
from PyQt4 import QtGui, QtCore # Import the PyQt4 module
#from functools import partial
import sys # We need sys so that we can pass argv to QApplication
import brewgui3_0 as brewgui # This file holds our MainWindow and all design related things
              # it also keeps events etc that we defined in Qt Designer

#imports for database
import mysql.connector as Db

# Imports for pyqtgraph
import numpy as np  
import pyqtgraph as pg

# Imports configparser
import configparser


    
################################
#Config Loader

#Load Config file into global variables

config = configparser.ConfigParser() #intitate configParser for configs
config2 = configparser.ConfigParser() #initiate second configParser object for saving/loading
config.read("/home/pi/PHACS/config.ini")

#Temperature Sensor Pins
TEMP_PINS = []
hlt_temp_pin = config.getint("temp_pins", "hlt_temp_pin")
mash_temp_pin = config.getint("temp_pins", "mash_temp_pin")
boil_temp_pin = config.getint("temp_pins", "boil_temp_pin")
hex_temp_pin = config.getint("temp_pins", "hex_temp_pin")
ferm_temp_pin = config.getint("temp_pins", "ferm_temp_pin")

TEMP_PINS = [hlt_temp_pin, mash_temp_pin, boil_temp_pin, hex_temp_pin, ferm_temp_pin]

#Relay Pins
black_relay_pin = config.getint("relay_pins", "black_relay_pin")
red_relay_pin = config.getint("relay_pins", "red_relay_pin")
orange_relay_pin = config.getint("relay_pins", "orange_relay_pin")
yellow_relay_pin = config.getint("relay_pins", "yellow_relay_pin")
green_relay_pin = config.getint("relay_pins", "green_relay_pin")
blue_relay_pin = config.getint("relay_pins", "blue_relay_pin")
purple_relay_pin = config.getint("relay_pins", "purple_relay_pin")
white_relay_pin = config.getint("relay_pins", "white_relay_pin")
hlt_relay_pin = config.getint("relay_pins", "hlt_relay_pin")
boil_relay_pin = config.getint("relay_pins", "boil_relay_pin")
pump1_relay_pin = config.getint("relay_pins", "pump1_relay_pin")
pump2_relay_pin = config.getint("relay_pins", "pump2_relay_pin")
pump3_relay_pin = config.getint("relay_pins", "pump3_relay_pin")

relay_on_value = config.getint("relay_pins", "relay_on_value")
if relay_on_value == 1:
    relay_off_value = 0
elif relay_on_value == 0:
    relay_off_value = 1
else:
    relay_on_value = 0
    relay_off_value = 1


#PID Control parameters
hlt_sample_time = config.getfloat("pid_parameters", "hlt_sample_time")
hlt_p = config.getfloat("pid_parameters", "hlt_p")
hlt_i = config.getfloat("pid_parameters", "hlt_i")
hlt_d = config.getfloat("pid_parameters", "boil_d")
hlt_windup_guard = config.getfloat("pid_parameters", "hlt_windup_guard")

mash_sample_time = config.getfloat("pid_parameters", "mash_sample_time")
mash_p = config.getfloat("pid_parameters", "mash_p")
mash_i = config.getfloat("pid_parameters", "mash_i")
mash_d = config.getfloat("pid_parameters", "mash_d")
mash_windup_guard = config.getfloat("pid_parameters", "mash_windup_guard")

boil_sample_time = config.getfloat("pid_parameters", "boil_sample_time")
boil_p = config.getfloat("pid_parameters", "boil_p")
boil_i = config.getfloat("pid_parameters", "boil_i")
boil_d = config.getfloat("pid_parameters", "boil_d")
boil_windup_guard = config.getfloat("pid_parameters", "boil_windup_guard")

relaydict = {}
relaydict["checkbox_BlackValve"] = black_relay_pin
relaydict["checkbox_RedValve"] = red_relay_pin
relaydict["checkbox_OrangeValve"] = orange_relay_pin
relaydict["checkbox_YellowValve"] = yellow_relay_pin
relaydict["checkbox_GreenValve"] = green_relay_pin
relaydict["checkbox_BlueValve"] = blue_relay_pin
relaydict["checkbox_PurpleValve"] = purple_relay_pin
relaydict["checkbox_WhiteValve"] = white_relay_pin
relaydict["checkbox_HLTpump"] = pump1_relay_pin
relaydict["checkbox_MashPump2"] = pump2_relay_pin
relaydict["checkbox_BoilPump3"] = pump3_relay_pin

#################################
#Setup GPIO connection
GPIO = pigpio.pi()
if not GPIO.connected:
    exit(0)

#SSR relay setup
GPIO.set_PWM_frequency(hlt_relay_pin, 5)
GPIO.set_PWM_frequency(boil_relay_pin, 5)
GPIO.set_PWM_range(hlt_relay_pin, 100)
GPIO.set_PWM_range(boil_relay_pin, 100)
GPIO.set_PWM_dutycycle(hlt_relay_pin, 0)
GPIO.set_PWM_dutycycle(boil_relay_pin, 0) 

#################################
#Setup PIDs

HLTPID = PID.PID(hlt_p, hlt_i, hlt_d)
HLTPID.setWindup(hlt_windup_guard)
HLTPID.setSampleTime(hlt_sample_time)

MASHPID = PID.PID(mash_p, mash_i, mash_d)
MASHPID.setWindup(mash_windup_guard)
MASHPID.setSampleTime(mash_sample_time)

BOILPID = PID.PID(boil_p, boil_i, boil_d)
BOILPID.setWindup(boil_windup_guard)
BOILPID.setSampleTime(boil_sample_time)

##################################
#Checkbox Dict
checkboxdict = {
  '0': 'checkbox_HLTpump',
  '1': 'checkbox_MashPump2',
  '2': 'checkbox_BoilPump3',
  '3': 'checkbox_BlackValve',
  '4': 'checkbox_RedValve',
  '5': 'checkbox_OrangeValve',
  '6': 'checkbox_YellowValve',
  '7': 'checkbox_GreenValve',
  '8': 'checkbox_BlueValve',
  '9': 'checkbox_PurpleValve',
  '10': 'checkbox_WhiteValve',
  '11': 'checkbox_HLTPID',
  '12': 'checkbox_MashPID',
  '13': 'checkbox_BoilPID',
  '14': 'checkbox_Select'}

recipeStatesLoaded=0
stateNames = []
stateNamedict={'0':0}
stateTabledict={'0':0}

#################################
# Global Variables


#################################
#Functions


def shutdown(*args, **kwargs):
    #Function to shutdown any connections
    #which could cause errors if left open on application exit
    #and close all valves turn off all relays
    GPIO.set_PWM_dutycycle(hlt_relay_pin, 0)
    GPIO.set_PWM_dutycycle(boil_relay_pin, 0) 
    GPIO.stop() #close pigpio connection
    


class MainApp(QtGui.QMainWindow, brewgui.Ui_MainWindow):
 
 ########
 # Object Specific Variables
 DOWN  = 1
 UP    = -1
 movingrows = False
 ########
 # Methods
 def __init__(self):
 
  super(self.__class__, self).__init__()
  self.setupUi(self)
  self.threadPool = []
  #self.testButton = QtGui.QPushButton("test")
  #self.connect(self.testButton, QtCore.SIGNAL("released()"), self.test)
  #self.listwidget = QtGui.QListWidget(self)
 
  #self.layout.addWidget(self.testButton)
  #self.layout.addWidget(self.listwidget)
  
  #connect checkbox changed SIGNALs to the relayChanged SLOT for all checkboxes
  self.checkbox_BlackValve.stateChanged.connect(self.relayChanged)
  self.checkbox_RedValve.stateChanged.connect(self.relayChanged)
  self.checkbox_OrangeValve.stateChanged.connect(self.relayChanged)
  self.checkbox_YellowValve.stateChanged.connect(self.relayChanged)
  self.checkbox_GreenValve.stateChanged.connect(self.relayChanged)
  self.checkbox_BlueValve.stateChanged.connect(self.relayChanged)
  self.checkbox_PurpleValve.stateChanged.connect(self.relayChanged)
  self.checkbox_WhiteValve.stateChanged.connect(self.relayChanged)
  self.checkbox_HLTpump.stateChanged.connect(self.relayChanged)
  self.checkbox_MashPump2.stateChanged.connect(self.relayChanged)
  self.checkbox_BoilPump3.stateChanged.connect(self.relayChanged)
  
  self.connect(self, QtCore.SIGNAL("relayCheck"), self.relayChange)
  
  self.loadStateTable("/home/pi/PHACS/State Tables/default.phs")
  self.getStateTable()
  self.refreshRecipeStates(0, 0)
  
  # setup QTimer function onTimeout contains the calls to start threads for periodic background tasks
  timer = QtCore.QTimer(self)
  timer.timeout.connect(self.onTimeout)
  timer.start(10000) 
 
 def relayChanged(self, state):
  #SLOT for stateChange SIGNAL on relay on checkboxes
  #identifies which box was changed and looks up pin and value
  #then sends SIGNAL that is caught by connection above in __init__
     
  sender = self.sender()
  print(sender.objectName())
  relay_pin = relaydict[str(sender.objectName())]
  print("State:", state)
  if state == 2:
      self.emit(QtCore.SIGNAL("relayCheck"), relay_pin, relay_on_value)
  else:
      self.emit(QtCore.SIGNAL("relayCheck"), relay_pin, relay_off_value)  
  
 def closeEvent(self,event):
  #Redefine the Window Close behavior to prompt and then call shutdown() function
     
  result = QtGui.QMessageBox.question(self,
    "Confirm Exit...",
    "Are you sure you want to exit ?",
    QtGui.QMessageBox.No | QtGui.QMessageBox.Yes) 
  
  if result == QtGui.QMessageBox.Yes:
    shutdown()
    event.accept()
  else:
    event.ignore()
 
 
 def updateStatus(self):
     #Update value of timer and temperature sensors
     #This is run as a Qthread to not hang the GUI during the updates
     self.lcdHLTread.setProperty("value", Temps.getTempsensor(hlt_temp_pin, TEMP_PINS))
     self.lcdMASHread.setProperty("value", Temps.getTempsensor(mash_temp_pin, TEMP_PINS))
     self.lcdBOILread.setProperty("value", Temps.getTempsensor(boil_temp_pin, TEMP_PINS))
     self.lcdHEXread.setProperty("value", Temps.getTempsensor(hex_temp_pin, TEMP_PINS))
     self.lcdFermread.setProperty("value", Temps.getTempsensor(ferm_temp_pin, TEMP_PINS))                          
     self.CurrentTime.setDateTime(QtCore.QDateTime.currentDateTime())
     self.elementControl()
 
 def elementControl(self): 
     if self.checkbox_BoilPID.checkState() > 0:
         BOILPID.SetPoint = self.spinBOILset.value()
         ''' #Testing/calibration  print PID values
         print("Boil PID set point:", BOILPID.SetPoint)
         print("Boil PID P:", BOILPID.PTerm)
         print("Boil PID I:", BOILPID.ITerm)
         print("Boil PID D:", BOILPID.DTerm)
         '''
         BOILPID.update(self.lcdBOILread.value())
         if BOILPID.output > 20:
             dutycycle = 100
         elif BOILPID.output > 0:
             dutycycle = int(BOILPID.output *5)
         else:
             dutycycle = 0
         x = self.pwmUpdate(boil_relay_pin, dutycycle)
         # print("pwmUpdate returned:", x)
     elif self.checkbox_MashPID.checkState() > 0:   
         MASHPID.SetPoint = self.spinMASHset.value()
         ''' #Testing/calibration  print PID values
         print("Mash PID set point:", MASHPID.SetPoint)
         print("Mash PID P:", MASHPID.PTerm)
         print("Mash PID I:", MASHPID.ITerm)
         print("Mash PID D:", MASHPID.DTerm)
         '''
         MASHPID.update(self.lcdMASHread.value())
         if MASHPID.output > 20:
             dutycycle = 100
         elif MASHPID.output > 0:
             dutycycle = int(MASHPID.output *5)
         else:
             dutycycle = 0
         x = self.pwmUpdate(hlt_relay_pin, dutycycle)
         # print("pwmUpdate returned:", x)
     elif self.checkbox_HLTPID.checkState() > 0:   
         HLTPID.SetPoint = self.spinHLTset.value()
         ''' #Testing/calibration  print PID values
         print("HLT PID set point:", HLTPID.SetPoint)
         print("HLT PID P:", HLTPID.PTerm)
         print("HLT PID I:", HLTPID.ITerm)
         print("HLT PID D:", HLTPID.DTerm)
         '''
         HLTPID.update(self.lcdHLTread.value())
         if HLTPID.output > 20:
             dutycycle = 100
         elif HLTPID.output > 0:
             dutycycle = int(HLTPID.output *5)
         else:
             dutycycle = 0
         x = self.pwmUpdate(hlt_relay_pin, dutycycle)
         # print("pwmUpdate returned:", x)

 def pwmUpdate(self, relayPin, dutycycle):
     print("Pin #", relayPin, "Duty Cycle:", dutycycle)
     if relayPin == hlt_relay_pin:
         GPIO.set_PWM_dutycycle(boil_relay_pin, 0)
         GPIO.set_PWM_dutycycle(hlt_relay_pin, dutycycle)
         return 0
     elif relayPin == boil_relay_pin:
         GPIO.set_PWM_dutycycle(hlt_relay_pin, 0)
         GPIO.set_PWM_dutycycle(boil_relay_pin, dutycycle)
         return 0
     else:
         return 1
 
 def relayChange(self, relayPin, state):
     print(self)
     print("relay pin:", relayPin)
     if state == relay_on_value:
         GPIO.write(relayPin, relay_on_value)
         print("Relay", relayPin, "on")
         return 1
     
     else:
         GPIO.write(relayPin, relay_off_value)
         print("Relay", relayPin, "off")
         return 0
     
 
 def add(self, text):
  """ Add item to list widget """
  print ("Add: " + text)
  self.comboBox_curentstep.addItem(text)
  #self.combobox_currentstep.listwidget.sortItems()
 
 def addBatch(self,text="test",iters=6,delay=0.3):
  """ Add several items to list widget """
  for i in range(iters):
   time.sleep(delay) # artificial time delay
   self.add(text+" "+str(i))
 
 def addBatch2(self,text="test",iters=6,delay=0.3):
  for i in range(iters):
   time.sleep(delay) # artificial time delay
   self.emit( QtCore.SIGNAL('add(QString)'), text+" "+str(i) )
 
 def startTimer(self):
  print("Placeholder for Start Step Code")
  self.getStateTable()
  
 def loadStateTable(self, openfile=0):
  #!TODO add code to enumerate state table from config file
  #Then delete the code in brewgui that hardcodes the state table settings.
  global loadingStates
  loadingStates = True
  if openfile == 0:
   self.opendialog = QtGui.QFileDialog()
   self.opendialog.setAcceptMode(0)
   self.opendialog.setFileMode(1)
   self.opendialog.setDefaultSuffix("phs")
   openfile = self.opendialog.getOpenFileName(self, "Select State Table to Load", "/home/pi/PHACS/State Tables", "PHACS State Table Files (*.phs);; All Files (*.*)")
  config2.read(openfile)
  if openfile == 0:
   return
  #print(config2.sections())
  #print([option for option in config2['StateName'].values()])
  self.tableWidget.setRowCount(0)
  for option in config2['StateName']:
   self.tableWidget.insertRow(int(option))
  for option in config2['StateName']:
   x = config2['StateName'][option]
   item = QtGui.QTableWidgetItem()
   self.tableWidget.setItem(int(option), 0, item)
   self.tableWidget.item(int(option),0).setText(x)
   y = config2['StateTable'][option]
   y = format(int(y), '015b')
   i = 1 
   for z in y:
    item = QtGui.QTableWidgetItem()
    self.tableWidget.setItem(int(option), i, item)
    self.tableWidget.item(int(option), i).setText(z)
    i += 1
  loadingStates = False
  self.refreshRecipeStates()
   
                                   
 
 def getStateTable(self):

  stateTabledict.clear()
  stateNamedict.clear()
  allRows = self.tableWidget.rowCount()
  allColumns = self.tableWidget.columnCount()
  for extraRow in range(allRows+1,len(stateTabledict)):
   stateTabledict.pop(extraRow)
  for extraRow in range(allRows+1,len(stateNamedict)):
   stateTabledict.pop(extraRow)
  for row in range(0,allRows):
   value = 0
   for column in range(0,allColumns):
    twi0 = self.tableWidget.item(row,column)
    if twi0 == None:
     twi0t = 0
    else:
     twi0t=twi0.text()
    if column == 0:
     header = twi0t
    else:
     try:
      twi0i = int(twi0t)
     except:
      twi0i = 0
      print("Invalid Type: Substituting Zero")
     value = (value*2)+int(twi0i)
   stateNamedict[row] = header
   stateTabledict[row] = value
  return stateNamedict, stateTabledict
   #print(key, bin(stateTabledict[key]))
  # !TODO delete this next line once done testing - we will call this code 
  #self.statusFromStateTable(stateNamedict, stateTabledict, 4)
 
 def saveStateTable(self):
  self.savedialog = QtGui.QFileDialog()
  self.savedialog.setAcceptMode(1)
  self.savedialog.setFileMode(0)
  savefile = self.savedialog.getSaveFileName(self, "Save State Table As", "/home/pi/PHACS/State Tables", "PHACS State Table Files (*.Phs)")
  print(len(savefile))
  if len(savefile) == 0:
       return
  stateNamedict, stateTabledict = self.getStateTable()
  saveStatedict = {'StateName':stateNamedict, 'StateTable':stateTabledict}
  #print(saveStatedict)
  config2.read_dict(saveStatedict)
  with open(savefile, 'w') as configfile:
   config2.write(configfile)
   
   
  
 def statusFromStateTable(self, stateNamedictx, stateTabledictx, stateNum): 
  # !TODO need to populate this box elsewhere and not clear here
  # so that user can select state from combo box manually
  # this will also require selcting the state from the list
  # instead of adding it here
  self.comboBox_curentstep.clear
  self.comboBox_curentstep.addItem(stateNamedictx[stateNum])
  v = stateTabledictx[stateNum]
  v = format(int(v), '016b')
  print("v", v)
  
  for key in range(0, len(checkboxdict)):
   x = int(v[key+1])*2 
   evalText = str('self.' + str(checkboxdict[str(key)]) + '.setCheckState(' + str(x) + ')')
   print(key, evalText)
   eval(evalText)
   
 def refreshRecipeStates(self, ignoredPassedRow=0, ignoredPassedColumn=0):
  if loadingStates:
   return
  print(self)
  if recipeStatesLoaded == 0:
   global stateNames
   stateNames = []
   for row in range(0, self.tableWidget.rowCount()):
    twi0 = self.tableWidget.item(row, 0)
    if twi0 == None:
     twi0t = "No Name"
    else:
     twi0t=twi0.text()
    stateNames.append(twi0t)
   
   for row in range(0, self.tableWidget_2.rowCount()):
    combobox = self.tableWidget_2.cellWidget(row, 1)
    ilist = []
    xlist = []
    for i in range(0,combobox.count()):
     xlist.append(combobox.itemText(i))
     if combobox.itemText(i) not in stateNames:
      ilist.append(i)
    count = combobox.count()
    for i in ilist:
     combobox.removeItem(i)
    for z in range(0, (len(stateNames) - combobox.count())):
     ilist.append(count+z)
    ilist.reverse()
    #print(ilist)
    for x in range(0, len(stateNames)):
     if stateNames[x] not in xlist:
      combobox.insertItem(ilist.pop(), stateNames[x])
      #print('afterpop', ilist)
 
 def recipeStepSelect(self, row, column):
  # function to populate recipe tab boxes based on selecetd step in qtable
  # !TODO add code for this function
  print(self.movingrows)
  if self.movingrows:
      return
  
  self.recipe_stepnumber.setValue(row+1)
  
  try:
   self.recipe_name.setText(self.tableWidget_2.item(row, 0).text())
  except:
   self.recipe_name.setText("Step Name")
   
  self.recipe_state.clear()
  items = []
  for i in range(0, self.tableWidget_2.cellWidget(row, 1).count()):
   item = self.tableWidget_2.cellWidget(row, 1).itemText(i)
   items.append(item)
  self.recipe_state.addItems(items)
  selectedstate = self.tableWidget_2.cellWidget(row, 1).currentText()
  x = self.recipe_state.findText(selectedstate)
  self.recipe_state.setCurrentIndex(x)
  
  try:
   self.recipe_time.setValue(int(self.tableWidget_2.item(row, 2).text()))
  except:
   self.recipe_time.setValue(0)
  
  try:
   self.recipe_temp.setValue(int(self.tableWidget_2.item(row, 3).text()))
  except:
   self.recipe_temp.setValue(32)

 def recipeChangeField(self, column):
   sender = self.sender()
   if column == 0:
    try:
     self.tableWidget_2.item((self.recipe_stepnumber.value()-1),column).setText(sender.toPlainText())
    except:
     item =  QtGui.QTableWidgetItem()
     self.tableWidget_2.setItem((self.recipe_stepnumber.value()-1), column, item)
     self.tableWidget_2.item((self.recipe_stepnumber.value()-1),column).setText(sender.toPlainText())
   else:
    try:
     self.tableWidget_2.item((self.recipe_stepnumber.value()-1),column).setText(sender.text())
    except:
     item =  QtGui.QTableWidgetItem()
     self.tableWidget_2.setItem((self.recipe_stepnumber.value()-1), column, item)
     self.tableWidget_2.item((self.recipe_stepnumber.value()-1),column).setText(sender.text())   
   
 def recipeAddRow(self): 
  x = self.tableWidget_2.rowCount()+1
  self.tableWidget_2.setRowCount(x)
  item = QtGui.QComboBox()
  self.tableWidget_2.setCellWidget(x-1, 1, item)
  self.tableWidget_2.cellWidget(x-1, 1).addItems(stateNames)
  
 def recipeDeleteRow(self):
  x = self.tableWidget_2.currentRow()
    
  result = QtGui.QMessageBox.question(self,
    "Confirm Row Deletion...",
    "Are you sure you want to delete row #" + str(x+1) + " ?",
    QtGui.QMessageBox.No | QtGui.QMessageBox.Yes) 
  
  if result == QtGui.QMessageBox.Yes:
   self.tableWidget_2.removeRow(x)
  else:
    pass

 '''
 def recipeMoveRowUp(self):
  x = self.tableWidget_2.currentRow()
  if x > 0 and x < self.tableWidget_2.rowCount():
   self.tableWidget_2.rowMoved(x, x, x-1)
   print("row", x , "moved")
 '''
 
 def moveCurrentRow(self, direction=DOWN):

  self.movingrows = True
  self.tableWidget_2.selectRow(self.tableWidget_2.currentRow())
  if direction not in (self.DOWN, self.UP):
     self.movingrows = False
     return
  table = self.tableWidget_2
  selModel = self.tableWidget_2.selectionModel()

  selected = selModel.selectedRows()
  if not selected:
   self.movingrows = False
   return
  
  if len(selected) != 1:
   result = QtGui.QMessageBox.information(self,
   "Error Moving Rows...",
   "Only single rows may be moved, but " + str(len(selected)) + " rows were selected. Select a single row and try again",
   QtGui.QMessageBox.Ok) 
   self.movingrows = False
   return
  
   
  
  
  x = selected[0]
  minRow = min(selected)
  maxRow = max(selected)

  minRowint = minRow.row()
  maxRowint = maxRow.row()
 
  items = []
  z = 0
  for row in selected:
   y = row.row()
   z = z+1
   for col in range(0, table.columnCount()):
    if col ==1:
     item = table.cellWidget(y,col)
    else:
     try:
      item = table.item(y,col).text()
     except:
      try:
       item = table.item(y,col).value()
      except:
       item = ""
    items.append(item)
    #itemsstr.append(item)
    
  if direction == self.UP:
   a=0
   for rowToAdd in range(0, z):
    table.insertRow(minRowint-1)
    for col in range(0,table.columnCount()):
     if col == 1:
      table.setCellWidget(minRowint-1,col,items[a])
     else:
      item = QtGui.QTableWidgetItem()
      table.setItem(minRowint-1,col,item)
      newItem = table.item(minRowint-1,col)
      if type(items[a]) == type("teststring"):
       newItem.setText(items[a])
      else:
       newItem.setValue(items[a])
     a += 1
    table.removeRow(minRowint+1)       
  if direction == self.DOWN:
   a=0
   for rowToAdd in range(0, z):
    table.insertRow(maxRowint+2)
    for col in range(0,table.columnCount()):
     if col == 1:
      print(items[a])
      table.setCellWidget(maxRowint+2,col,items[a])
     else:
      item = QtGui.QTableWidgetItem()
      table.setItem(maxRowint+2,col,item)
      newItem = table.item(maxRowint+2,col)
      if type(items[a]) == type("teststring"):
       newItem.setText(items[a])
      else:
       newItem.setValue(items[a])
     a += 1
    table.removeRow(maxRowint)

  self.movingrows = False
  self.recipeStepSelect(minRowint+direction,0)
  self.tableWidget_2.selectRow(minRowint+direction)
 '''   
  indexes = sorted(selected, key=lambda x: x.row(), reverse=(direction==self.DOWN))

  for idx in indexes:
   items.append(model.data(idx))
   rowNum = idx.row()
   newRow = rowNum+direction
   if not (0 <= newRow < model.rowCount()):
    continue

   rowItems = model.rowAt(rowNum)
   model.insertRow(newRow, rowItems)

  selModel.clear()
  for item in items:
   selModel.select(item.index(), selModel.Select|selModel.Rows)
 '''
 
 def onTimeout(self):
  #starts a new thread to run code in updateStatus function in another thread
  #so as to not hang the UI during the periodic updates
  self.threadPool.append( GenericThread(self.updateStatus) )
  self.disconnect( self, QtCore.SIGNAL("add(QString)"), self.add )
  self.connect( self, QtCore.SIGNAL("add(QString)"), self.add )
  self.threadPool[len(self.threadPool)-1].start()
  
  '''example code for threading
  self.comboBox_curentstep.clear()
  # adding in main application: locks ui
  #self.addBatch("_non_thread",iters=6,delay=0.3)
 
  # adding by emitting signal in different thread
  self.threadPool.append( WorkThread() )
  self.connect( self.threadPool[len(self.threadPool)-1], QtCore.SIGNAL("update(QString)"), self.add )
  self.threadPool[len(self.threadPool)-1].start()
 
  # generic thread using signal
  self.threadPool.append( GenericThread(self.addBatch2,"from generic thread using signal ",delay=2) )
  self.disconnect( self, QtCore.SIGNAL("add(QString)"), self.add )
  self.connect( self, QtCore.SIGNAL("add(QString)"), self.add )
  self.threadPool[len(self.threadPool)-1].start()
  
  #end example code for threading'''
 
class WorkThread(QtCore.QThread):
 def __init__(self):
  QtCore.QThread.__init__(self)
 
 def __del__(self):
  self.wait()
 
 def run(self):
  for i in range(6):
   time.sleep(1.) # artificial time delay
   self.emit( QtCore.SIGNAL('update(QString)'), "from work thread " + str(i) )
  return
 
class GenericThread(QtCore.QThread):
 def __init__(self, function, *args, **kwargs):
  QtCore.QThread.__init__(self)
  self.function = function
  self.args = args
  self.kwargs = kwargs
 
 def __del__(self):
  self.wait()
 
 def run(self):
  self.function(*self.args,**self.kwargs)
  return


    

# run
def main():
    app = QtGui.QApplication(sys.argv)  # A new instance of QApplication
    form = MainApp()                    # We set the form to be our ExampleApp (design)
    form.show()                         # Show the form
    app.exec_()                         # and execute the appapp = QtGui.QApplication(sys.argv)

main()