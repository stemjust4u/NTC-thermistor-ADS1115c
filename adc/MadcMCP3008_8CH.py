#!/usr/bin/env python3
''' MCP3008 adc has 8 channels.  If any channel has a delta (current-previous) that is above the
noise threshold or if the max Time interval exceeded then the 
voltage from all channels will be returned.
 When creating object, pass: Number of channels, Vref, noise threshold, and max time interval
 Will return a list with the voltage value for each channel

To find the noise threshold set noise threshold low and max time interval lowpygame.examples.mask.main()
Noise is in raw ADC

Max time interval is used to catch drift/creep that is below the noise threshold.

You can enable SPI1 with a dtoverlay configured in "/boot/config.txt"
dtoverlay=spi1-3cs

'''
import busio, digitalio, board, logging
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from time import time, sleep

class mcp3008:
    ''' ADC using MCP3008 (SPI). Returns a list with voltge values '''

    def __init__(self, numOfChannels, vref, noiseThreshold=350, maxInterval=1, cs=8):
        ''' Create spi connection and initialize lists '''
        
        self.vref = vref
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI) # create the spi bus
        if cs == 8:
            cs = digitalio.DigitalInOut(board.D8) # create the cs (chip select). Use GPIO8 (CE0) or GPIO7 (CE1)
        elif cs == 7:
            cs = digitalio.DigitalInOut(board.D7) # create the cs (chip select). Use GPIO8 (CE0) or GPIO7 (CE1)
        else:
            logging.info("Chip Select pin must be 7 or 8")
            exit()
        mcp = MCP.MCP3008(spi, cs) # create the mcp object
        self.numOfChannels = numOfChannels
        self.chan = [AnalogIn(mcp, MCP.P0), # create analog input channel on pins
                     AnalogIn(mcp, MCP.P1),
                     AnalogIn(mcp, MCP.P2),
                     AnalogIn(mcp, MCP.P3),
                     AnalogIn(mcp, MCP.P4),
                     AnalogIn(mcp, MCP.P5),
                     AnalogIn(mcp, MCP.P6),
                     AnalogIn(mcp, MCP.P7)]
        self.noiseThreshold = noiseThreshold
        self.numOfSamples = 10             # Number of samples to average
        self.maxInterval = maxInterval  # interval in seconds to check for update
        self.time0 = time()   # time 0
        # Initialize lists
        self.sensorAve = [x for x in range(self.numOfChannels)]
        self.sensorLastRead = [x for x in range(self.numOfChannels)]
        self.adcValue = [x for x in range(self.numOfChannels)]
        self.sensor = [[x for x in range(0, self.numOfSamples)] for x in range(0, self.numOfChannels)]
        for x in range(self.numOfChannels): # initialize the first read for comparison later
            self.sensorLastRead[x] = self.chan[x].value
    
    def valmap(self, value, istart, istop, ostart, ostop):
        ''' Used to convert from raw ADC to voltage '''

        return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))

    def getValue(self):
        ''' If adc is above noise threshold or time limit exceeded will return voltage of each channel '''
        
        sensorChanged = False
        timelimit = False
        if time() - self.time0 > self.maxInterval:
            timelimit = True
        for x in range(self.numOfChannels):
            for i in range(self.numOfSamples):  # get samples points from analog pin and average
                self.sensor[x][i] = self.chan[x].value
            self.sensorAve[x] = sum(self.sensor[x])/len(self.sensor[x])
            if abs(self.sensorAve[x] - self.sensorLastRead[x]) > self.noiseThreshold:
                sensorChanged = True
                logging.debug('changed: {0} chan: {1} value: {2:1.3f} previously: {3:1.3f}'.format(sensorChanged, x, self.sensorAve[x], self.sensorLastRead[x]))
            self.adcValue[x] = self.valmap(self.sensorAve[x], 0, 65535, 0, self.vref) # 4mV change is approx 500
            self.sensorLastRead[x] = self.sensorAve[x]
            #logging.debug('chan: {0} value: {1:1.3f}'.format(x, self.adcValue[x]))
        if sensorChanged or timelimit:
            self.adcValue = ["%.3f"%item for item in self.adcValue] #format and send final adc results
            self.time0 = time()
            return self.adcValue
        else:
            pass
      
if __name__ == "__main__":
  
    adc = mcp3008(2, 5, 400, 1) # numOfChannels, vref, noiseThreshold
    outgoingD = {}
    while True:
        voltage = adc.getValue()
        if voltage is not None:
            i = 0
            for pin in voltage:                               # create dictionary with voltage from each pin
                outgoingD['a' + str(i) + 'f'] = str(voltage[i])  # key=pin:value=voltage 
                i += 1
            print(outgoingD)
            sleep(.05)