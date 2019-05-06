import time
import serial
from datetime import datetime
from lab_code.lab_serial2 import lab_serial

do_cycle_fridge = False

class FridgeCycle():

    def __init__(self, ps_port='COM10', mm_port='COM3'):
        self.ps_port = ps_port
        self.ps_connection = lab_serial(port=self.ps_port)
        self.mm_port = mm_port
        self.mm_connection = lab_serial(port=self.mm_port, parity=serial.PARITY_NONE)
        self.initialize_mm_for_resistance()
        try:
            self.check_resistance()
        except ValueError:
            import ipdb;ipdb.set_trace()
        self.apply_voltage(0)
        #import ipdb;ipdb.set_trace()

    def _send_ps_command(self, msg):
        self.ps_connection.write(msg)

    def _query_ps(self, query, timeout=0.5):
        self._send_ps_command(query)
        response = self.ps_connection.read()
        print(response)
        return response

    def _send_mm_command(self, msg):
        self.mm_connection.write(msg)

    def _query_mm(self, query, timeout=0.5):
        self._send_mm_command(query)
        response = self.mm_connection.read()
        print(response)
        return response

    def initialize_mm_for_resistance(self):
        self._send_mm_command(":SYST:REM\r\n;")
        self._send_mm_command(":CONF:RES AUTO\r\n;")

    def apply_voltage(self, volts):
        self._send_ps_command('VOLT {0}\r\n'.format(volts))

    def get_voltage(self):
        self._send_ps_command('VOLT?\r\n'.format(volts))

    def check_resistance(self):
        self._send_mm_command(":MEAS:RES?\r\n")
        resistance = float(self.mm_connection.read())
        print(resistance)
        return resistance

    def run_cycle(self, charcoal_start_resistance=1e3, charcoal_end_resistance=0.5e3, sleep_time=0.5):
        global do_cycle_fridge
        do_cycle_fridge = True
        resistance = self.check_resistance()
        # Wait for charcoal to cool down
        print('Start Cool', resistance, charcoal_start_resistance, do_cycle_fridge)
        while resistance < charcoal_start_resistance and do_cycle_fridge:
            time.sleep(sleep_time)
            resistance = self.check_resistance()
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
            resistance = self.check_resistance()
            print('Heating', resistance, charcoal_start_resistance, do_cycle_fridge)
        print('Charcol has reached {0} turning off Voltage'.format(charcoal_start_resistance))
        self.apply_voltage(0)
        print('Voltage on heater set to 0V')

    def stop_cycle(self, charcoal_start_resistance=5e5, charcoal_end_resistance=3.5e3, sleep_time=0.5):
        global do_cycle_fridge
        do_fridge_cyle = False
        print('Stopping Fridge Cycle at {0}'.format(datetime.now()))
        self.apply_voltage(0)

if __name__ == '__main__':
    fc = FridgeCycle()
    fc.run_cycle()

