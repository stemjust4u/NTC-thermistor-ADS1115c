#!/usr/bin/env python3
''' ADS1115 adc has 4 channels.  If any channel has a delta (current-previous) that is above the
noise threshold or if the max Time interval exceeded then the 
voltage from all initialized channels will be returned.
 When creating object, pass: Number of channels, noise threshold, max time interval, and gain.
Will return a list with the voltage value for each channel

To find the noise threshold set noise threshold low and max time interval low.
Noise is in Volts

Max time interval is used to catch drift/creep that is below the noise threshold.

Gain options. Set the gain to capture the voltage range being measured.
 PGA setting  FS (V)
 2/3          +/- 6.144
 1            +/- 4.096
 2            +/- 2.048
 4            +/- 1.024
 8            +/- 0.512
 16           +/- 0.256

 Note you can change the I2C address from its default (0x48), and/or the I2C
 bus by passing in these optional parameters:
 ads = ADS.ADS1015(address=0x49, bus=1)

'''

import busio, board, logging
from time import time, sleep
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

class ads1115:
    ''' ADC using ADS1115 (I2C). Returns a list with voltge values '''
    
    def __init__(self, numOfChannels=1, noiseThreshold=0.001, maxInterval=1, gain=1):
        ''' Create I2C bus and initialize lists '''
        
        i2c = busio.I2C(board.SCL, board.SDA)  # Create the I2C bus
        ads = ADS.ADS1115(i2c)   # Create the ADC object using the I2C bus
        ads.gain = gain
        #ads.gain = 2/3
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
    
    adc = ads1115(1, 0.001, 1, 1) # numOfChannels, noiseThreshold, Gain
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
