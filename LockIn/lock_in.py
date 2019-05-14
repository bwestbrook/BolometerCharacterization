import time
import visa
#from datetime import datetime
from lab_code.lab_serial import lab_serial

class LockIn():


    def __init__(self, port='COM12'):
        self.port = port
        self._connection = lab_serial(port=self.port)
        import ipdb;ipdb.set_trace()

    def __init__(self, port='COM12'):
        self.port = port
        self._connection = lab_serial(port=self.port)
        import ipdb;ipdb.set_trace()

    def _send_command(self, msg):
        self._connection.write(msg)

    def _query(self, query, timeout=0.5):
        self._send_command(query)
        response = self._connection.read()
        print(response)
        return response

    def _change_lock_in_range(self, direction):
        current_value = self._query('SENS?\r\n')
        if direction == 'up':
            new_value = int(current_value + 1)))
        elif direction == 'up':
            new_value = int(current_value + 1)))
        else:
            print("please specificy 'up' or 'down'")
            new_value = int(current_value)
        self._send_command('SENS {0}\r\n'.format(new_value))

    def run(self):
        print('running')

if __name__ == '__main__':
    li = LockIn()
    li.run()
