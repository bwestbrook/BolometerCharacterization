import time
import serial
import os
import numpy as np
from datetime import datetime
from lab_code.lab_serial import lab_serial

do_cycle_fridge = False

class PowerSupply():

    def __init__(self, ps_port='COM3'):
        self.ps_port = ps_port
        self.ps_connection = lab_serial(port=self.ps_port, parity=None)
        self.initialize_ps()

    def _send_ps_command(self, msg):
        self.ps_connection.write(msg)

    def _query_ps(self, query, timeout=0.5):
        self._send_ps_command(query)
        response = self.ps_connection.read()
        return response

    def apply_voltage(self, volts):
        self._send_ps_command('APPL {0}, 0.2\r\n'.format(volts))
        self._send_ps_command('OUTP ON\r\n'.format(volts))
        self.ps_connection.read()
        return self.get_voltage()

    def get_voltage(self):
        voltage = self._query_ps('MEAS:VOLT?')
        if self._is_float(voltage):
            voltage_str = '{0:.2f}'.format(float(voltage))
        else:
            voltage_str = voltage
        if self._is_float(voltage):
            return float(voltage), voltage_str
        else:
            self._send_ps_command("*CLS\r\n;")
            time.sleep(0.5)
            self.get_voltage()

    def initialize_ps(self):
        self._send_ps_command("INIT\r\n;")
        self.ps_connection.read()
        self._send_ps_command("*RST\r\n;")
        self.ps_connection.read()
        self._query_ps('MEAS:VOLT?')
        self.apply_voltage(0)
        self._query_ps('MEAS:VOLT?')

    def _is_float(self, value):
        try:
            float(value)
            is_float = True
        except ValueError:
            is_float = False
        return is_float

if __name__ == '__main__':
    ps = PowerSupply()

