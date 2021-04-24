<link rel="stylesheet" href="./images/sj4u.css"></link>

# [STEM Just 4 U Home Page](https://stemjust4u.com/)
## This project collects temperature from a ntc thermistor

On the Raspberry Pi an external ADC is required. Libraries for ads1115 and mcp3008 are used for this project. The 10k ntc thermistor is connected to 3.3V with a 10k-ntc/10k voltage divider setup. The voltage from thermistor to ground is measured with ADC. As the temperature goes up the thermistor resistance decreases resulting in a change of the fractional voltage drop across the thermistor. The thermistor voltage will go down while the voltage across R1 goes up. This voltage change is measured with the ADC and converted to a temp in C° using Steinhart-Hart equation.

[Link to Project Web Site](https://github.com/stemjust4u/adc-thermistor-ads1115)



## Materials 
* Raspberry Pi
* NTC B 3950 5% 10k Thermistor

![thermistor](images/falstad.gif#5rad)

![thermistor](images/thermistor.png#5rad)
​
