# TI_INA226_micropython

This library provides support for the TI INA226 power measurement IC with micropython firmware.
Datasheet and other information on the IC can be found here: https://www.ti.com/product/INA226

> [!NOTE]
> This library is based on [TI_INA226_micropython](https://github.com/elschopi/TI_INA226_micropython)
> written by Christian Becker. However, this library is not compatible with the original library.
> Some methods have been changed, removed or added. Errors have been fixed. Alerts are partially
> implemented.<BR>
> The helper script `ina_calc_config.py` has also been modified. 

## Basics

To use the device, it has to be configured at startup. In it's default configuration, the calibration
register is not set and thus the current and power cannot be directly read out.<br>
By default, this library configures the device to a maximum current of 3.6 A and 36V bus voltage.
Resistance of the shunt is assumed as 0.01 Ohm (10 mOhm). For different configurations, use
`ina_calc_config.py` to calculate the correct values.

## Methods
Constructor:

* `INA226(i2c_device, addr=0x40)` - Initializes the INA226 device; the driver also checks if the
device is present.

Public methods:

* `set_current_lsb(current_LSB: float)` - Sets the calculation coefficient to determine the real
value of the current.
* `set_calibration(cal_value: int)` - Sets the calibration register in INA226.
* `set_config(config_value: int)` - Sets the configuration register in INA226.
* `disable_alerts()` - Disable all alerts.
* `set_under_current(self, i_min: float, r_shunt: float)` - Sets the under current alert. It needs `r_shunt` value in Ohm.
* `set_over_current(self, i_max: float, r_shunt: float)` - Sets the over current alert. It needs `r_shunt` value in Ohm.
* `set_under_voltage(self, v_min: float)` - Sets the under voltage alert.
* `set_over_voltage(self, v_max: float)` - Sets the over voltage alert.

Getters:

* `shunt_voltage` - gets the shunt voltage (between V+ and V-) in Volts (-81.9175mV to +81.92mV),<br>
fixed conversion, defined by chip to 2.5uV/bit.
* `bus_voltage` - gets the bus voltage (between V- and GND) in Volts (0 to 36V),<br>
fixed conversion, defined by chip to 1.25mV/bit.
* `current` - gets the current through the shunt resistor in Amperes.<br>
variable conversion, defined by calibration register value to `current_LSB`.<br>
`current` = `raw_current` x `current_LSB` = `shunt_voltage` x `calibration_register` x `current_LSB`<br>
`current_LSB` is suitable choice.
* `power` - gets the power in milliWatts.<br>
`power` = `bus_voltage` x `raw_current` x `power_LSB`<br>
`power_LSB` = `current_LSB` x 25

## Configuration
Best way to configure the INA226 is to use `ina_calc_conf.py`. This script will calculate the correct
configuration values for configuration register, calibration register and conversion coefficient for
current. Then use methods `set_config`, `set_calibration` and `set_current_lsb` to setup the INA226.

By default, the INA226 class is configured to work with a 0.01 Ohm shunt and a maximum current about 3.2A (even though for 10mOhm the maximum current output is over 8A).
Configuration register is set to default value: 1 sample average, 1.1ms conversion time for bus voltage
and shunt voltage, continuous operating mode.

## Calculations

The following values need to be calculated in order to set the configuration and calibration register values:
- configuration register value
- calibration register value
- current LSB value
- power LSB value

### Configuration register
Configuration register value is derived from the values of the corresponding bits.

| BitNr	   | Name   | Info |
|----------|--------|------|
| D15 	   | Reset  | When set to 1, the configuration register is reset to the default value. |
| D14 	   | N/A    | Always must be set to 1 |
| D13..D12 | N/A    | Always must be set to 0 |
| D11..D9  | AVG    | Averaging mode 1 to 1024 samples<br>Options: **1**, 4, 16, 64, 128, 256, 512, 1024 |
| D08..D6  | VBUSCT | Bus voltage conversion time 140us to 8244us<br>Options: 140us, 204us, 332us, 588us, **1100us**, 2116us, 4156us, 8244us |
| D05..D3  | VSHCT  | Shunt voltage conversion time 140us to 8244us<br>Options: 140us, 204us, 332us, 588us, **1100us**, 2116us, 4156us, 8244us |
| D2..D0   | MODE   | Operating mode<br>Options: Shutdown, Shunt / Bus / Shunt & Bus Voltage, Triggered / Continuous |

Default configuration according to the datasheet (value 0x4127):
- Averaging mode: 1 sample
- Bus voltage conversion time: 1.1ms
- Shunt voltage conversion time: 1.1ms
- Operating mode: Shunt and Bus voltage, continuous

`ina_calc_conf.py` with option `c` as `configuration` will offers the user possible values ​​and calculates
the correct value of the configuration register. Result `Ttotal` will indicate the total conversion time
for new sample.

### Current_LSB
As example, a maximum expected current of 3.2A is assumed.

current_LSB = max_expected_I / (2^15)</br>
current_LSB = 3.2 A / (2^15)</br>
current_LSB = 97.65625 uA/bit

The calculated value can be used directly. However, for simpler calculations, it is customary to use the
nearest higher rounded value. Suitable values ​​are 1, 2 or 5 x 10^n. 

For the example above, we choose the value:</br>
current_LSB = 100uA/bit -> 0.0001

`ina_calc_conf.py` with option `l` as `calibration` will calculate the correct value of the calibration
register and the current_LSB.

### Calibration register
The basis for calculating the calibration value is the shunt resistor. It is important to check that the
given resistor meets the maximum voltage requirement of the INA226.

Rshunt = 25 mOhm = 0.025 Ohm</br>
Vimax = Rshunt * Imax < 0.0819</br>
Vimax = 0.025 Ohm * 3.2 A = 0.08V

Cal_value = 0.00512 / (current_LSB * Rshunt)</br>
Cal_value = 0.00512 / (0.0001 * 0.025)</br>
Cal_value = 2048</br>

`ina_calc_conf.py` with option `l` as `calibration` will calculate the correct value of the calibration
register and the current_LSB. It will also check if the maximum voltage requirement is met.

### Power_LSB
The conversion factor for power is tied to the current_LSB value. This value is therefore not set
separately, but is calculated when setting current_LSB.

power_LSB = 25 * current_LSB</br>
power_LSB = 25 * 0.0001 = 0.0025</br>

## Example
This code was tested on "Strom" PCB with ESP32-C3 Super Mini (400KB SRAM, 384KB ROM built-in 4Mflash)
and INA226 with 25mOhm shunt.

Using `ina_calc_conf.py` first:
```
Welcome to the INA226 configuration calculator.
Results from this calculator can be used to configure the INA226 instance.
Choice: (c)onfiguration or ca(l)ibration or (e)xit: c


Averaging Mode:
0: N = 1 ~ 0x0000
1: N = 4 ~ 0x0200
2: N = 16 ~ 0x0400
3: N = 64 ~ 0x0600
4: N = 128 ~ 0x0800
5: N = 256 ~ 0x0A00
6: N = 512 ~ 0x0C00
7: N = 1024 ~ 0x0E00
Please input sample number: 5

Bus voltage conversion time:
0: Tbus = 140us ~ 0x0000
1: Tbus = 204us ~ 0x0040
2: Tbus = 332us ~ 0x0080
3: Tbus = 588us ~ 0x00C0
4: Tbus = 1100us ~ 0x0100
5: Tbus = 2116us ~ 0x0140
6: Tbus = 4156us ~ 0x0180
7: Tbus = 8244us ~ 0x01C0
Please input VBUS conversion time: 4

Shunt voltage conversion time:
0: Tshunt = 140us ~ 0x0000
1: Tshunt = 204us ~ 0x0008
2: Tshunt = 332us ~ 0x0010
3: Tshunt = 588us ~ 0x0018
4: Tshunt = 1100us ~ 0x0020
5: Tshunt = 2116us ~ 0x0028
6: Tshunt = 4156us ~ 0x0030
7: Tshunt = 8244us ~ 0x0038
Please input VSHUNT conversion time: 4

Operating mode:
0: Power off ~ 0x0000
1: Vshunt, Triggered ~ 0x0001
2: Vbus, Triggered ~ 0x0002
3: Vshunt & Vbus, Triggered ~ 0x0003
4: Power off ~ 0x0004
5: Vshunt, Continuous ~ 0x0005
6: Vbus, Continuous ~ 0x0006
7: Vshunt & Vbus, Continuous ~ 0x0007
Please input operating mode: 7
Configuration result:
    Tbus = 256 x 1100us = 281.6ms
    Tshunt = 256 x 1100us = 281.6ms
    Ttotal = 563.2ms
    Use "config" =  0x4B27


Choice: (c)onfiguration or ca(l)ibration or (e)xit: l


Please input maximum expected current in Amps: 3.2
Please input shunt resistance in miliOhms: 25
    Maximum allowed current = 3.28A
    Calculated Current_LSB: 97.65625 uA/bit
    Rounded Current_LSB: 100 uA/bit
    Use "current_LSB" = 0.000100
    Use "calValue" =  2048
    Shunt voltage Vmax = 0.080V


Choice: (c)onfiguration or ca(l)ibration or (e)xit: e
Goodbye!
```

Testing code:
```python
import ina226
from machine import Pin, I2C
import time
# i2c
i2c = I2C(0, scl=Pin(7), sda=Pin(6))
# ina226
ina = ina226.INA226(i2c, 0x45)
# user configuration and calibration value
ina.set_config(0x4B27)
ina.set_current_lsb(0.0001)
ina.set_calibration(2048)
# wait for first sample (Ttotal = 563.2ms)
time.sleep_ms(600)
# print measured values
print(ina.bus_voltage)
print(ina.shunt_voltage)
print(ina.current)
print(ina.power)
```
