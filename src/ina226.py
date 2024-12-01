# The MIT License (MIT)
#
# Copyright (c) 2017 Dean Miller for Adafruit Industries
# Copyright (c) 2020 Christian Becker
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`ina226`
====================================================

micropython driver for the INA226 current sensor.

* Author(s): Rastislav Michalek
* License: MIT

"""
# taken from https://github.com/robert-hh/INA219 , modified for the INA226 devices by
# Christian Becker
# June 2020

# taken from https://github.com/elschopi/TI_INA226_micropython , modified by 
# Rastislav Michalek
# November 2024

from micropython import const

# Config Register (R/W)
_REG_CONFIG = const(0x00)
_CONFIG_DEFAULT = const(0x4127) # Default value
_CONFIG_RESET = const(0x8000)  # Reset Bit

# Constant bits - don't change
# _CONFIG_CONST_BITS = const(0x4000)

# Averaging mode
# _CONFIG_AVGMODE_MASK = const(0x0e00)
# _CONFIG_AVGMODE_1SAMPLES = const(0x0000)
# _CONFIG_AVGMODE_4SAMPLES = const(0x0200)
# _CONFIG_AVGMODE_16SAMPLES = const(0x0400)
# _CONFIG_AVGMODE_64SAMPLES = const(0x0600)
# _CONFIG_AVGMODE_128SAMPLES = const(0x0800)
# _CONFIG_AVGMODE_256SAMPLES = const(0x0a00)
# _CONFIG_AVGMODE_512SAMPLES = const(0x0c00)
# _CONFIG_AVGMODE_1024SAMPLES = const(0x0e00)

# Bus voltage conversion time
# _CONFIG_VBUSCT_MASK = const(0x01c0)
# _CONFIG_VBUSCT_140us = const(0x0000)
# _CONFIG_VBUSCT_204us = const(0x0040)
# _CONFIG_VBUSCT_332us = const(0x0080)
# _CONFIG_VBUSCT_588us = const(0x00c0)
# _CONFIG_VBUSCT_1100us = const(0x0100)
# _CONFIG_VBUSCT_21116us = const(0x0140)
# _CONFIG_VBUSCT_4156us = const(0x0180)
# _CONFIG_AVGMODE_8244us = const(0x01c0)

# Shunt voltage conversion time
# _CONFIG_VSHUNTCT_MASK = const(0x0038)
# _CONFIG_VSHUNTCT_140us = const(0x0000)
# _CONFIG_VSHUNTCT_204us = const(0x0008)
# _CONFIG_VSHUNTCT_332us = const(0x0010)
# _CONFIG_VSHUNTCT_588us = const(0x0018)
# _CONFIG_VSHUNTCT_1100us = const(0x0020)
# _CONFIG_VSHUNTCT_21116us = const(0x0028)
# _CONFIG_VSHUNTCT_4156us = const(0x0030)
# _CONFIG_VSHUNTCT_8244us = const(0x0038)

# Operating mode
# _CONFIG_MODE_MASK = const(0x0007)  # Operating Mode Mask
# _CONFIG_MODE_POWERDOWN = const(0x0000)
# _CONFIG_MODE_SVOLT_TRIGGERED = const(0x0001)
# _CONFIG_MODE_BVOLT_TRIGGERED = const(0x0002)
# _CONFIG_MODE_SANDBVOLT_TRIGGERED = const(0x0003)
# _CONFIG_MODE_ADCOFF = const(0x0004)
# _CONFIG_MODE_SVOLT_CONTINUOUS = const(0x0005)
# _CONFIG_MODE_BVOLT_CONTINUOUS = const(0x0006)
# _CONFIG_MODE_SANDBVOLT_CONTINUOUS = const(0x0007)

# SHUNT VOLTAGE REGISTER (R)
_REG_SHUNTVOLTAGE = const(0x01)

# BUS VOLTAGE REGISTER (R)
_REG_BUSVOLTAGE = const(0x02)

# POWER REGISTER (R)
_REG_POWER = const(0x03)

# CURRENT REGISTER (R)
_REG_CURRENT = const(0x04)

# CALIBRATION REGISTER (R/W)
_REG_CALIBRATION = const(0x05)

# MASK/ENABLE REGISTER (R/W)
_REG_MASKENABLE = const(0x06)
_MASKENABLE_DEFAULT = const(0x0000)
_MASKENABLE_ALERT_LATCH = const(0x0001)
_MASKENABLE_MATH_OVF = const(1 << 2)
_MASKENABLE_POWER_OVER = const(1 << 11)
_MASKENABLE_BUS_UNDER = const(1 << 12)
_MASKENABLE_BUS_OVER = const(1 << 13)
_MASKENABLE_SHUNT_UNDER = const(1 << 14)
_MASKENABLE_SHUNT_OVER = const(1 << 15)

# ALERT LIMIT REGISTER (R/W)
_REG_ALERTLIMIT = const(0x07)

# MANUFACTURER ID REGISTER (R)
_REG_MANUFACTURERID = const(0xFE)
_MANUFACTURERID_TI = const(0x5449)

# DEVICE ID REGISTER (R)
_REG_DEVICEID = const(0xFF)
_DEVICEID_INA226 = const(0x2260)


def _to_signed(num):
    if num > 0x7FFF:
        num -= 0x10000
    return num

def _limit_s16(num):
    if num > 32767:
        num = 32767
    if num < -32768:
        num = -32768
    return num

class INA226:
    """Driver for the INA226 current sensor"""
    def __init__(self, i2c_device, addr=0x40):
        """Configure the INA226 to measure with a resistance of 0.01 Ohm up to 36V
        and 3.6A of current. Counter overflow occurs at about 8A.
        """
        self.i2c_device = i2c_device
        self.i2c_addr = addr
        self.buf = bytearray(2)
        # verify device
        if self._verify() is False:
            raise RuntimeError("INA226 device not found")

        # Multiplier in mA used to determine current from raw reading
        self._current_lsb = 0
        # Multiplier in W used to determine power from raw reading
        self._power_lsb = 0

        # Set chip to known config values to start
        self.set_calibration(2560)
        self.set_current_lsb(.0002)
        self.set_config(_CONFIG_DEFAULT)

    def __repr__(self) -> str:
        return f"INA226(i2c_device={self.i2c_device}, addr={hex(self.i2c_addr)})"

    def _write_register(self, reg, value):
        self.buf[0] = (value >> 8) & 0xFF
        self.buf[1] = value & 0xFF
        self.i2c_device.writeto_mem(self.i2c_addr, reg, self.buf)

    def _read_register(self, reg):
        self.i2c_device.readfrom_mem_into(self.i2c_addr, reg & 0xff, self.buf)
        value = (self.buf[0] << 8) | (self.buf[1])
        return value

    def _verify(self):
        man_id = self._read_register(_REG_MANUFACTURERID)
        dev_id = self._read_register(_REG_DEVICEID)
        return (man_id == _MANUFACTURERID_TI) and (dev_id == _DEVICEID_INA226)

    @property
    def shunt_voltage(self):
        """The shunt voltage (between V+ and V-) in Volts (so +-81.92mV)"""
        value = _to_signed(self._read_register(_REG_SHUNTVOLTAGE))
        # The least signficant bit is 2.5uV
        return value * 2.5e-6

    @property
    def bus_voltage(self):
        """The bus voltage (between V- and GND) in Volts"""
        raw_voltage = self._read_register(_REG_BUSVOLTAGE)
        # voltage in millVolt is register content multiplied with 1.25mV/bit
        return raw_voltage * 1.25e-3

    @property
    def current(self):
        """The current through the shunt resistor in Amps."""
        # Sometimes a sharp load will reset the INA219, which will
        # reset the cal register, meaning CURRENT and POWER will
        # not be available ... athis by always setting a cal
        # value even if it's an unfortunate extra step
        self._write_register(_REG_CALIBRATION, self._cal_value)

        # Now we can safely read the CURRENT register!
        raw_current = _to_signed(self._read_register(_REG_CURRENT))
        return raw_current * self._current_lsb
    
    @property
    def power(self):
        """The power supplied by the bus in Watts"""
        # INA226 stores the calculated power in this register        
        raw_power = _to_signed(self._read_register(_REG_POWER))
        # Calculated power is derived by multiplying raw power value with the power LSB
        return raw_power * self._power_lsb

    def set_current_lsb(self, current_lsb: float):
        self._current_lsb = current_lsb
        self._power_lsb = 25 * current_lsb

    def set_calibration(self, cal_value: int):
        self._cal_value = cal_value
        self._write_register(_REG_CALIBRATION, self._cal_value)

    def set_config(self, config_value: int):
        self._write_register(_REG_CONFIG, config_value)

    def disable_alerts(self):
        self._write_register(_REG_MASKENABLE, _MASKENABLE_DEFAULT)

    def set_under_current(self, i_min: float, r_shunt: float):
        # vshunt_min = i_min * r_shunt
        alert_reg = _limit_s16(int(i_min * r_shunt / 2.5e-6))
        self._write_register(_REG_ALERTLIMIT, alert_reg)
        self._write_register(_REG_MASKENABLE, _MASKENABLE_SHUNT_UNDER)

    def set_over_current(self, i_max: float, r_shunt: float):
        # vshunt_max = i_max * r_shunt
        alert_reg = _limit_s16(int(i_max * r_shunt / 2.5e-6))
        self._write_register(_REG_ALERTLIMIT, alert_reg)
        self._write_register(_REG_MASKENABLE, _MASKENABLE_SHUNT_OVER)

    def set_under_voltage(self, vbus_min: float):
        alert_reg = _limit_s16(int(vbus_min / 1.25e-3))
        self._write_register(_REG_ALERTLIMIT, alert_reg)
        self._write_register(_REG_MASKENABLE, _MASKENABLE_BUS_UNDER)
    
    def set_over_voltage(self, vbus_max: float):
        alert_reg = _limit_s16(int(vbus_max / 1.25e-3))
        self._write_register(_REG_ALERTLIMIT, alert_reg)
        self._write_register(_REG_MASKENABLE, _MASKENABLE_BUS_OVER)
