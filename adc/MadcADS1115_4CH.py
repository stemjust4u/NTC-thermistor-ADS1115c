#!/usr/bin/env python3
''' ADS1115 adc has 4 channels.  If any channel has a delta (current-previous) that is above the
noise threshold or if the max Time interval exceeded then the 
voltage from all initialized channels will be returned.
When creating object, pass: Number of channels, noise threshold, max time interval, gain, and address.
Will return a list with the voltage value for each channel

Number of channels (1-4)
To find the noise threshold set noise threshold low. Noise is in Volts
Max time interval is used to catch drift/creep that is below the noise threshold.
Gain options. Set the gain to capture the voltage range being measured.
 User         FS (V)
 2/3          +/- 6.144
 1            +/- 4.096
 2            +/- 2.048
 4            +/- 1.024
 8            +/- 0.512
 16           +/- 0.256

Note you can change the I2C address from its default (0x48)
To check the address
$ sudo i2cdetect -y 1
Change the address by connecting the ADDR pin to one of the following
0x48 (1001000) ADR -> GND
0x49 (1001001) ADR -> VDD
0x4A (1001010) ADR -> SDA
0x4B (1001011) ADR -> SCL
Then update the address when creating the ads object in the HARDWARE section

'''

import busio, board, logging
from time import time, sleep
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

class ads1115:
    ''' ADC using ADS1115 (I2C). Returns a list with voltge values '''
    
    def __init__(self, numOfChannels=1, noiseThreshold=0.001, maxInterval=1, usergain=1, useraddress=0x48):
        ''' Create I2C bus and initialize lists '''
        
        logging.info("ADS1115 using I2C at address {0}".format(str(useraddress)))
        i2c = busio.I2C(board.SCL, board.SDA)  # Create the I2C bus
        ads = ADS.ADS1115(i2c, gain=usergain, address=useraddress)   # Create the ADC object using the I2C bus
        self.numOfChannels = numOfChannels
        self.chan = [AnalogIn(ads, ADS.P0), # create analog input channel on pins
                     AnalogIn(ads, ADS.P1),
                     AnalogIn(ads, ADS.P2),
                     AnalogIn(ads, ADS.P3)]
        self.noiseThreshold = noiseThreshold
        self.numOfSamples = 10        # Number of samples to average
        self.maxInterval = maxInterval  # interval in seconds to check for update
        self.time0 = time()   # time 0
        # Initialize lists
        self.sensorAve = [x for x in range(self.numOfChannels)]
        self.sensorLastRead = [x for x in range(self.numOfChannels)]
        self.adcValue = [x for x in range(self.numOfChannels)]
        self.sensor = [[x for x in range(0, self.numOfSamples)] for x in range(0, self.numOfChannels)]
        for x in range(self.numOfChannels): # initialize the first read for comparison later
            self.sensorLastRead[x] = self.chan[x].value

    def getValue(self):
        ''' If adc is above noise threshold or time limit exceeded will return voltage of each channel '''
        
        sensorChanged = False
        timelimit = False
        if time() - self.time0 > self.maxInterval:
            timelimit = True
        for x in range(self.numOfChannels):
            for i in range(self.numOfSamples):  # get samples points from analog pin and average
                self.sensor[x][i] = self.chan[x].voltage
            self.sensorAve[x] = sum(self.sensor[x])/len(self.sensor[x])
            if abs(self.sensorAve[x] - self.sensorLastRead[x]) > self.noiseThreshold:
                sensorChanged = True
                logging.debug('changed: {0} chan: {1} value: {2:1.3f} previously: {3:1.3f}'.format(sensorChanged, x, self.sensorAve[x], self.sensorLastRead[x]))
            self.adcValue[x] = self.sensorAve[x]            
            self.sensorLastRead[x] = self.sensorAve[x]
            #logging.debug('chan: {0} value: {1:1.2f}'.format(x, self.adcValue[x]))
        if sensorChanged or timelimit:
            self.adcValue = ["%.3f"%pin for pin in self.adcValue] #format and send final adc results
            self.time0 = time()
            return self.adcValue
        else:
            pass
      
if __name__ == "__main__":
    
    adc = ads1115(1, 0.001, 1, 1, 0x48) # numOfChannels, noiseThreshold, max time interval, Gain, Address
    outgoingD = {}
    while True:
        voltage = adc.getValue() # returns a list with the voltage for each pin that was passed in ads1115
        if voltage is not None:
            i = 0
            for pin in voltage:                               # create dictionary with voltage from each pin
                outgoingD['a' + str(i) + 'f'] = str(voltage[i])  # key=pin:value=voltage 
                i += 1
            print(outgoingD)
            sleep(.05)
