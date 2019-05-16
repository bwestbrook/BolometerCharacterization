import time
import serial
import os
import numpy as np
from datetime import datetime
from lab_code.lab_serial import lab_serial

do_cycle_fridge = False

class FridgeCycle():

    def __init__(self, ps_port='COM3', mm_port='COM12'):
        self.ps_port = ps_port
        self.ps_connection = lab_serial(port=self.ps_port, parity=None)
        self.mm_port = mm_port
        self.mm_connection = lab_serial(port=self.mm_port, parity=serial.PARITY_NONE)
        self.initialize_mm_for_resistance()

    def _send_ps_command(self, msg):
        self.ps_connection.write(msg)

    def _query_ps(self, query, timeout=0.5):
        self._send_ps_command(query)
        response = self.ps_connection.read()
        return response

    def _send_mm_command(self, msg):
        self.mm_connection.write(msg)

    def _query_mm(self, query, timeout=0.5):
        self._send_mm_command(query)
        response = self.mm_connection.read()
        return response

    def get_resistance(self):
        resistance = self._query_mm(":MEAS:RES?\r\n")
        if self._is_float(resistance):
            resistance_str = '{0:.2f}'.format(float(resistance))
        else:
            resistance_str = resistance
        if self._is_float(resistance):
            return float(resistance), resistance_str
        else:
            self._send_mm_command("*CLS\r\n;")
            time.sleep(0.5)
            self.get_resistance()

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

    def initialize_mm_for_resistance(self):
        self._send_mm_command("*RST\r\n;")
        self.mm_connection.read()
        self._send_mm_command(":SYST:REM\r\n;")
        self.mm_connection.read()
        self._send_mm_command(":CONF:RES AUTO\r\n;")
        self.mm_connection.read()
        self._send_mm_command("*CLS\r\n;")
        resistance = self.get_resistance()

    def initialize_ps_for_resistance(self):
        self._send_ps_command("INIT\r\n;")
        self.ps_connection.read()
        self._send_ps_command("*RST\r\n;")
        self.ps_connection.read()
        self._query_ps('MEAS:VOLT?')
        self.apply_voltage(0)
        self._query_ps('MEAS:VOLT?')

    def run_cycle(self, charcoal_start_resistance=1e3, charcoal_end_resistance=0.5e3, sleep_time=0.5):
        global do_cycle_fridge
        do_cycle_fridge = True
        resistance = self.get_resistance()
        # Wait for charcoal to cool down
        print('Start Cool', resistance, charcoal_start_resistance, do_cycle_fridge)
        while resistance < charcoal_start_resistance and do_cycle_fridge:
            time.sleep(sleep_time)
            resistance = self.get_resistance()
            print('Cooling', resistance, charcoal_start_resistance, do_cycle_fridge)
        print('Charcol has reached {0} turning on Voltage'.format(charcoal_start_resistance))
        # Turn on voltage in steps of 1 volt over with a sleep between
        for i in range(3):
            time.sleep(sleep_time)
            self.apply_voltage(i)
        print('Start Heat', resistance, charcoal_end_resistance, do_cycle_fridge)
        print('Voltage to heater set to {0} V'.format(i))
        while resistance > charcoal_end_resistance and do_cycle_fridge:
            time.sleep(sleep_time)
            resistance = self.get_resistance()
            print('Heating', resistance, charcoal_start_resistance, do_cycle_fridge)
        print('Charcol has reached {0} turning off Voltage'.format(charcoal_start_resistance))
        self.apply_voltage(0)
        print('Voltage on heater set to 0V')

    def stop_cycle(self, charcoal_start_resistance=5e5, charcoal_end_resistance=3.5e3, sleep_time=0.5):
        global do_cycle_fridge
        do_fridge_cyle = False
        print('Stopping Fridge Cycle at {0}'.format(datetime.now()))
        self.apply_voltage(0)

    def _is_float(self, value):
        try:
            float(value)
            is_float = True
        except ValueError:
            is_float = False
        return is_float

if __name__ == '__main__':
    fc = FridgeCycle()
    fc.run_cycle()

