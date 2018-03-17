#IMPORTS
# imports for SPI / Thermostats and General
from os import system
system("sudo pigpiod")

import time
import get_temp3 as Temps

# imports for pyqtgui
from PyQt4 import QtGui, QtCore # Import the PyQt4 module we'll need
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

#Load Config file into global variables

config = configparser.ConfigParser()
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


class MyApp(QtGui.QMainWindow, brewgui.Ui_MainWindow):
 def __init__(self):
 
  super(self.__class__, self).__init__()
  self.setupUi(self)
  self.threadPool = []
  #self.testButton = QtGui.QPushButton("test")
  #self.connect(self.testButton, QtCore.SIGNAL("released()"), self.test)
  #self.listwidget = QtGui.QListWidget(self)
 
  #self.layout.addWidget(self.testButton)
  #self.layout.addWidget(self.listwidget)
  timer = QtCore.QTimer(self)
  timer.timeout.connect(self.onTimeout)
  timer.start(1000) 
  
 
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
 
 def test():
  print("Placeholder for Start Step Code")
        
 def onTimeout(self):
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
    form = MyApp()                 # We set the form to be our ExampleApp (design)
    form.show()                         # Show the form
    app.exec_()                         # and execute the appapp = QtGui.QApplication(sys.argv)

main()