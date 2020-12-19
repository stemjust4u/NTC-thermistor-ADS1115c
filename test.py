import time, board, busio, math
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Create the I2C bus #
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus #
ads = ADS.ADS1115(i2c)
# ads.gain = 2/3 #

# PGA Gain Full-Scale Range #
# PGA setting  FS (V) #
# 2/3          +/- 6.144 #
# 1            +/- 4.096 #
# 2            +/- 2.048 #
# 4            +/- 1.024 #
# 8            +/- 0.512 #
# 16           +/- 0.256 #

# Create single-ended input on channel 0 #
chan = AnalogIn(ads, ADS.P0)

# print("{:>5}\t{:>5}".format('raw', 'v')) #

# Vo=R/(R+10K)*Vcc #
# R = 10000 / (65535/thermistor.value - 1) #
# print('Thermistor resistance: {} ohms'.format(R)) #

# Vr2 = Vcc(R2/(R1+R2)) #
R1 = 10040
Vcc=3.34
Bc = 3950
Tnom = 23   # nominal Temp in C for Rntc value #
Rntc = 9500   # R2 or ntc resistance at nom Temp #

while True:
    # print("{:>5}\t{:>5.3f}".format(chan.value, chan.voltage)) #
    Vr2 = chan.voltage
    R2=Vr2*R1/(Vcc-Vr2)
    steinhart = R2 / Rntc
    steinhart = math.log(steinhart)
    steinhart /= Bc
    steinhart += 1 / (Tnom + 273.15)
    steinhart = 1 / steinhart
    steinhart -= 273.15
    print("{0:.2f}".format(steinhart))
    time.sleep(0.5)