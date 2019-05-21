import time
import visa
#from datetime import datetime
from lab_code.lab_serial import lab_serial

class LockIn():

    def __init__(self, port='COM3'):
        self.port = port
        self._connection = lab_serial(port=self.port)
        self._set_lock_in_defaults()
        #import ipdb;ipdb.set_trace()

    def _send_command(self, msg):
        self._connection.write(msg)

    def _query(self, query, timeout=0.5):
        self._send_command(query)
        response = self._connection.read()
        return response

    def _set_lock_in_defaults(self):
        self._change_lock_in_sensitivity_range(setting=22)
        self._change_lock_in_time_constant(setting=8)

    def _zero_lock_in_phase(self):
        self._send_command('APHS\r\n')

    def _change_lock_in_sensitivity_range(self, direction=None, setting=None):
        current_value = self._get_current_sensitivity_range()
        if self._is_float(current_value):
            current_value = int(current_value)
            if direction is not None:
                if direction == 'up':
                    new_value = int(current_value + 1)
                elif direction == 'down':
                    new_value = int(current_value - 1)
                else:
                    print("please specificy 'up' or 'down'")
                    new_value = int(current_value)
            elif setting is not None:
                new_value = int(setting)
            if new_value > 26:
                new_value = 26
            if new_value < 0:
                new_value = 0
            self._send_command('SENS {0}\r\n'.format(new_value))

    def _get_current_sensitivity_range(self):
        sensitivity_range_index = self._query('SENS?\r\n')
        if self._is_float(sensitivity_range_index):
            return int(sensitivity_range_index)
        else:
            return 0

    def _change_lock_in_time_constant(self, direction=None, setting=None):
        current_value = self._get_current_time_constant()
        if self._is_float(current_value):
            current_value = int(current_value)
            if direction is not None:
                if direction == 'up':
                    new_value = int(current_value + 1)
                elif direction == 'down':
                    new_value = int(current_value - 1)
                else:
                    print("please specificy 'up' or 'down'")
                    new_value = int(current_value)
            elif setting is not None:
                new_value = int(setting)
            if new_value > 19:
                new_value = 19
            if new_value < 0:
                new_value = 0
            self._send_command('OFLT {0}\r\n'.format(new_value))

    def _get_current_time_constant(self):
        time_constant_index = self._query('OFLT?\r\n')
        if self._is_float(time_constant_index):
            return int(time_constant_index)
        else:
            return 0

    def _is_float(self, value):
        try:
            float(value)
            is_float = True
        except ValueError:
            is_float = False
        return is_float

    def run(self):
        print('running')

if __name__ == '__main__':
    li = LockIn()
    li.run()
