#!/usr/bin/env python3
# ADS1115 adc is multi channel.  If any channel has a delta (current-previous) that is above the
# noise threshold then the voltage from all channels will be returned.
# MQTT version has a publish section in the main code to test MQTT ability stand alone
import os, busio, digitalio, board, sys, re, json
from time import time
import paho.mqtt.client as mqtt
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

class ads1115:
  def __init__(self, numOfChannels, vref, sampleInterval=1, noiseThreshold=0.001, numOfSamples= 10):
    self.vref = vref
    # Create the I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)
    # Create the ADC object using the I2C bus
    ads = ADS.ADS1115(i2c)
    #ads.gain = 2/3
    self.numOfChannels = numOfChannels
    self.chan = [AnalogIn(ads, ADS.P0), # create analog input channel on pins
                 AnalogIn(ads, ADS.P1),
                 AnalogIn(ads, ADS.P2),
                 AnalogIn(ads, ADS.P3)]
    self.noiseThreshold = noiseThreshold
    self.sensorChanged = False
    self.numOfSamples = numOfSamples
    self.sensorAve = [x for x in range(self.numOfChannels)]
    self.sensorLastRead = [x for x in range(self.numOfChannels)]
    for x in range(self.numOfChannels): # initialize the first read for comparison later
      self.sensorLastRead[x] = self.chan[x].value
    self.adcValue = [x for x in range(self.numOfChannels)]
    self.sensor = [[x for x in range(0, self.numOfSamples)] for x in range(0, self.numOfChannels)]
    self.sampleInterval = sampleInterval  # interval in seconds to check for update
    self.time0 = time()   # time 0
    
  def valmap(self, value, istart, istop, ostart, ostop):
    return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))

  def getValue(self):
    if time() - self.time0 > self.sampleInterval:
      self.time0 = time()
      for x in range(self.numOfChannels):
        for i in range(self.numOfSamples):  # get samples points from analog pin and average
          self.sensor[x][i] = self.chan[x].voltage
        self.sensorAve[x] = sum(self.sensor[x])/len(self.sensor[x])
        if abs(self.sensorAve[x] - self.sensorLastRead[x]) > self.noiseThreshold:
          self.sensorChanged = True
        self.sensorLastRead[x] = self.sensorAve[x]
        self.adcValue[x] = self.sensorAve[x]
        #print('chan: {0} value: {1:1.2f}'.format(x, self.adcValue[x]))
      if self.sensorChanged:
        self.adcValue = ["%.2f"%pin for pin in self.adcValue] #format and send final adc results
        self.sensorChanged = False
        return self.adcValue
      
if __name__ == "__main__":
    #=======   SETUP MQTT =================#
    MQTT_ADDRESS = '10.0.0.22'
    MQTT_TOPIC = 'countchocula/ads1115/+'  # + means one or more occurrence
    MQTT_REGEX = 'countchocula/([^/]+)/([^/]+)'  #regular expression.  ^ means start with
    MQTT_CLIENT_ID = 'countchocula'
    topic_pub = 'countchocula/ads1115/all'

    # create call back functions and then link them to the mqtt callback below in main program
    def on_connect(client, userdata, flags, rc):
        """ The callback for when the client receives a CONNACK response from the server."""
        print('Connected with result code ' + str(rc))  #str() returns the nicely printable representation of a given object.
        client.subscribe(MQTT_TOPIC)

    #on message will receive data from client 
    def on_message(client, userdata, msg):
        """The callback for when a PUBLISH message is received from the server."""
        print(msg.topic + ' ' + str(msg.payload))

    #on publish will send data to client
    def on_publish(client, userdata, mid):
        print("mid: "+str(mid))

    #==== start mqtt functions ===========#
    mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
    # mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect  #bind call back function
    mqtt_client.on_message = on_message  #bind function to be used when PUBLISH messages are found
    mqtt_client.on_publish = on_publish  #bind function for publishing
    mqtt_client.connect(MQTT_ADDRESS, 1883)  # connect to the mqtt
    mqtt_client.loop_start()   # other option is client.loop_forever() but it is blocking

    adc = ads1115(2, 5, 0.1, 0.001) # numOfChannels, vref, delay, noiseThreshold
    ads1115D = {}
    while True:
      voltage = adc.getValue() # returns a list with the voltage for each pin that was passed in ads1115
      if voltage is not None:
        i = 0
        for pin in voltage:                               # create dictionary with voltage from each pin
          ads1115D['a' + str(i) + 'f'] = str(voltage[i])  # key=pin:value=voltage 
          i += 1                                          # will convert dict-to-json for easy MQTT publish of all pin at once
        ads1115MQTT = json.dumps(ads1115D)                # convert dictionary to json
        mqtt_client.publish(topic_pub, ads1115MQTT)       # publish voltage values
