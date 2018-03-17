def getTempsensor(temp_pin, TEMP_PINS):
   # MAX6675.py
   # 2016-05-02
   # Public Domain

   import time
   import pigpio # http://abyz.co.uk/rpi/pigpio/python.html
   from os import system
   # system("sudo pigpiod")
   """
   This script reads the temperature of a type K thermocouple
   connected to a MAX6675 SPI chip.

   Type K thermocouples are made of chromel (+ve) and alumel (-ve)
   and are the commonest general purpose thermocouple with a
   sensitivity of approximately 41 uV/C.

   The MAX6675 returns a 12-bit reading in the range 0 - 4095 with
   the units as 0.25 degrees centigrade.  So the reported
   temperature range is 0 - 1023.75 C.

   Accuracy is about +/- 2 C between 0 - 700 C and +/- 5 C
   between 700 - 1000 C.

   The MAX6675 returns 16 bits as follows

   F   E   D   C   B   A   9   8   7   6   5   4   3   2   1   0
   0  B11 B10  B9  B8  B7  B6  B5  B4  B3  B2  B1  B0  0   0   X

   The reading is in B11 (most significant bit) to B0.

   The conversion time is 0.22 seconds.  If you try to read more
   often the sensor will always return the last read value.
   """
   # time.sleep(3)
   pi = pigpio.pi()
         
   if not pi.connected:
      exit(0)

   sensor = pi.spi_open(0, 1000000, 0)   # CE0, 1Mbps, main SPI
   # pi.spi_open(1, 1000000, 0)   # CE1, 1Mbps, main SPI
   # pi.spi_open(0, 1000000, 256) # CE0, 1Mbps, auxiliary SPI
   # pi.spi_open(1, 1000000, 256) # CE1, 1Mbps, auxiliary SPI
   # pi.spi_open(2, 1000000, 256) # CE2, 1Mbps, auxiliary SPI

   #sensor = pi.spi_open(2, 1000000, 256) # CE2 on auxiliary SPI

   #stop = time.time() + 20
   # Commented out this section
   # - changed function to require list of GPIO pins on the SPI bus
   # - need the list of pins to be sure only one is pulled high.
   #TEMP0_PIN = 4
   #TEMP1_PIN = 5
   #TEMP2_PIN = 6
   #TEMP_PINS = {TEMP0_PIN, TEMP1_PIN, TEMP2_PIN}

   for b in TEMP_PINS:
      pi.write(b, 1)
   next

   #while time.time() < stop:
   #for b in TEMP_PINS:
   time.sleep(.5)
   pi.write(temp_pin, 0)
   #time.sleep(2)
   #sensor = pi.spi_open(0, 1000000, 0)
   c, d = pi.spi_read(sensor, 2)
   if c == 2:
      word = (d[0]<<8) | d[1]
      if (word & 0x8006) == 0: # Bits 15, 2, and 1 should be zero.
         t = (word >> 3)/4.0
         tf = t * 9 / 5 + 32
         tf = tf - (tf % 1)
         pi.spi_close(sensor)
         #print (temp_pin)
         sensor = None
         pi.write(temp_pin, 1)
         pi.stop()
         print (pi.connected)
         pi = None
         print (tf)
         return tf
      else:
         pi.spi_close(sensor)
         pi.write(temp_pin, 1)
         sensor = None
         pi.stop()
         return "bad reading"
      
   #next          

