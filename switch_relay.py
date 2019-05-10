import time
import sys
from lab_code.lab_serial import lab_serial

class SwitchRelay():

    def __init__(self, port='COM12'):
        self.port = port
        self._connection = lab_serial(port=self.port)
        self._query('MEAS:VOlT?')
        import ipdb;ipdb.set_trace()

    def _send_command(self, msg):
        self._connection.write(msg)

    def switch_to_position(self, position):
        print('Switching to position {0}'.format(position))
        if position == 1:
            self._send_command('APPL 0, 0.2\r\n')
        elif position == 2:
            self._send_command('APPL 14, 0.2\r\n')

    def _query(self, query, timeout=0.5):
        self._send_command(query)
        response = self._connection.read()
        print(response)
        return response


if __name__ == '__main__':
    sr = SwitchRelay()
    position_0 = sys.argv[1]
    position_1 = sys.argv[2]
    sr.switch_to_position(position_0)
    time.sleep(5)
    sr.switch_to_position(position_1)
