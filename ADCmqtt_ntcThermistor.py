#!/usr/bin/env python3

'''
ADS1115 adc has 4 channels.  If any channel has a delta (current-previous) that is above the
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

MCP3008 adc has 8 channels.  If any channel has a delta (current-previous) that is above the
 noise threshold or if the max Time interval exceeded then the  voltage from all channels will be returned.
 When creating object, pass: Number of channels, Vref, noise threshold, max time interval, and CS or CE (chip select)
 Will return a list with the voltage value for each channel
 Number of channels (1-8)
 Vref (3.3 or 5V) ** Important on RPi. If using 5V must use a voltage divider on MISO
 R2=R1(1/(Vin/Vout-1)) Vin=5V, Vout=3.3V, R1=2.4kohm
 R2=4.7kohm
 Noise threshold is in raw ADC - To find the noise threshold set initial threshold low and monitor
 Max time interval is used to catch drift/creep that is below the noise threshold.
 CS (chip select) - Uses SPI0 with GPIO 8 (CE0) or GPIO 7 (CE1)

 Requires 4 lines. SCLK, MOSI, MISO, CS
 You can enable SPI1 with a dtoverlay configured in "/boot/config.txt"
 dtoverlay=spi1-3cs
 SPI1 SCLK = GPIO 21
      MISO = GPIO 19
      MOSI = GPIO 20
      CS = GPIO 18(CE0) 17(CE1) 16(CE2)

Check Hardware and MQTT setup sections for pin assignments and topics

'''

import sys, json, logging, math, re
from time import sleep
import paho.mqtt.client as mqtt
from os import path
from pathlib import Path
import adc

if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO) # Set to CRITICAL to turn logging off. Set to DEBUG to get variables. Set to INFO for status messages.

    #=======   SETUP MQTT =================#
    # Import mqtt and wifi info. Remove if hard coding in python file
    home = str(Path.home())
    with open(path.join(home, "stem"),"r") as f:
        stem = f.read().splitlines()

    #=======   SETUP MQTT =================#
    MQTT_SERVER = '10.0.0.115'                    # Replace with IP address of device running mqtt server/broker
    MQTT_USER = stem[0]                           # Replace with your mqtt user ID
    MQTT_PASSWORD = stem[1]                       # Replace with your mqtt password
    MQTT_SUB_TOPIC = []          # + is wildcard for that level. Can .append more topics
    MQTT_SUB_TOPIC.append('nred2pi/adcZCMD/+')
    MQTT_REGEX = r'nred2pi/([^/]+)/([^/]+)'

    #MQTT_CLIENT_ID = 'RPi4Argon1'
    MQTT_CLIENT_ID = 'RPi3AP'
    #MQTT_CLIENT_ID = 'RPi0'

    MQTT_PUB_TOPIC = ['pi2nred/', '/' + MQTT_CLIENT_ID] # Final topic is joined at time of publishing based on which ADC is sending data

    def on_connect(client, userdata, flags, rc):
        """ on connect callback verifies a connection established and subscribe to TOPICs"""
        logging.info("attempting on_connect")
        if rc==0:
            mqtt_client.connected = True
            for topic in MQTT_SUB_TOPIC:
                client.subscribe(topic)
                logging.info("Subscribed to: {0}\n".format(topic))
            logging.info("Successful Connection: {0}".format(str(rc)))
        else:
            mqtt_client.failed_connection = True  # If rc != 0 then failed to connect. Set flag to stop mqtt loop
            logging.info("Unsuccessful Connection - Code {0}".format(str(rc)))

    def on_message(client, userdata, msg):
        """on message callback will receive messages from the server/broker. Must be subscribed to the topic in on_connect"""
        global mqtt_dummy1, mqtt_dummy2
        logging.debug("Received: {0} with payload: {1}".format(msg.topic, str(msg.payload)))
        msgmatch = re.match(MQTT_REGEX, msg.topic)   # Check for match to subscribed topics
        if msgmatch:
            incomingD = json.loads(str(msg.payload.decode("utf-8", "ignore"))) 
            incomingID = [msgmatch.group(0), msgmatch.group(1), msgmatch.group(2), type(incomingD)] # breaks msg topic into groups - group/group1/group2
            if incomingID[2] == 'group2A':
                mqtt_dummy1 = incomingD
            elif incomingID[2] == 'group2B':
                mqtt_dummy2 = incomingD
        # Debugging. Will print the JSON incoming payload and unpack it
        logging.debug("Topic grp0:{0} grp1:{1} grp2:{2}".format(msgmatch.group(0), msgmatch.group(1), msgmatch.group(2)))
        #incomingD = json.loads(str(msg.payload.decode("utf-8", "ignore")))
        logging.debug("Payload type:{0}".format(type(incomingD)))
        #if isinstance(incomingD, (str, bool, int, float)):
        #    logging.debug(incomingD)
        #elif isinstance(incomingD, list):
        #    for item in incomingD:
        #        logging.debug(item)
        #elif isinstance(incomingD, dict):
        #    for key, value in incomingD.items():  
        #        logging.debug("{0}:{1}".format(key, value))

    def on_publish(client, userdata, mid):
        """on publish will send data to client"""
        #Debugging. Will unpack the dictionary and then the converted JSON payload
        logging.debug("msg ID: " + str(mid)) 
        logging.debug("Publish: Unpack outgoing dictionary (Will convert dictionary->JSON)")
        #for key, value in outgoingD.items():
        #    logging.debug("{0}:{1}".format(key, value))
        logging.debug("Converted msg published on topic: {0} with JSON payload: {1}\n".format(MQTT_PUB_TOPIC1, json.dumps(outgoingD))) # Uncomment for debugging. Will print the JSON incoming msg
        pass 

    def on_disconnect(client, userdata,rc=0):
        logging.debug("DisConnected result code "+str(rc))
        mqtt_client.loop_stop()

    #==== start/bind mqtt functions ===========#
    # Create a couple flags to handle a failed attempt at connecting. If user/password is wrong we want to stop the loop.
    mqtt.Client.connected = False          # Flag for initial connection (different than mqtt.Client.is_connected)
    mqtt.Client.failed_connection = False  # Flag for failed initial connection
    # Create our mqtt_client object and bind/link to our callback functions
    mqtt_client = mqtt.Client(MQTT_CLIENT_ID) # Create mqtt_client object
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD) # Need user/password to connect to broker
    mqtt_client.on_connect = on_connect    # Bind on connect
    mqtt_client.on_message = on_message    # Bind on message
    mqtt_client.on_publish = on_publish    # Bind on publish
    logging.info("Connecting to: {0}".format(MQTT_SERVER))
    mqtt_client.connect(MQTT_SERVER, 1883) # Connect to mqtt broker. This is a blocking function. Script will stop while connecting.
    mqtt_client.loop_start()               # Start monitoring loop as asynchronous. Starts a new thread and will process incoming/outgoing messages.
    # Monitor if we're in process of connecting or if the connection failed
    while not mqtt_client.connected and not mqtt_client.failed_connection:
        logging.info("Waiting")
        sleep(1)
    if mqtt_client.failed_connection:      # If connection failed then stop the loop and main program. Use the rc code to trouble shoot
        mqtt_client.loop_stop()
        sys.exit()

    def ntc(voltage, R1=10000, Vcc=3.3, Bc=3950, Tnom=23, Rntc=10000):
        ''' Calculate ntc temp in C° using steinhart method '''
        R2=voltage*R1/(Vcc-voltage)
        steinhart = R2 / Rntc
        steinhart = math.log(steinhart)
        steinhart /= Bc
        steinhart += 1 / (Tnom + 273.15)
        steinhart = 1 / steinhart
        steinhart -= 273.15
        return "{:.1f}".format(steinhart)

    #==== HARDWARE SETUP ===============# 
    # 
    adcSet = {}  # Can comment out any ADC type not being used
    adcSet['ads1115'] = adc.ads1115(1, 0.003, 1, 1, 0x48) # numOfChannels, noiseThreshold (V), max interval, gain=1 (+/-4.1V readings), address
    #adcSet['mcp3008'] = adc.mcp3008(2, 3.3, 400, 1, 8) # numOfChannels, vref, noiseThreshold (raw ADC), maxInterval = 1sec, and ChipSelect GPIO pin (7 or 8)
    
    outgoingD = {}
    try:
        while True:
            for model, adc in adcSet.items():
                    voltage = adc.getValue() # returns a list with the voltage for each pin that was passed in ads1115
                    print(voltage)
                    if voltage is not None:
                        for i, pin in enumerate(voltage):                       # create dictionary with voltage from each pin
                            steinhart = ntc(float(voltage[i]), 10040, 3.34, 3950, 23, 9500)    # Could also send Voltage and do steinhart calc in node-red
                            outgoingD['a' + str(i) + 'f'] = str(steinhart)  # key=pin:value=voltage 
                        # will convert dict-to-json for easy MQTT publish of all pins at once
                        MQTT_PUB_TOPIC1 = model.join(MQTT_PUB_TOPIC)
                        mqtt_client.publish(MQTT_PUB_TOPIC1, json.dumps(outgoingD))  # publish voltage values
                        sleep(1)
    except KeyboardInterrupt:
        logging.info("Pressed ctrl-C")
    finally:
        # Do any cleanup here
        logging.info("Cleaned up")