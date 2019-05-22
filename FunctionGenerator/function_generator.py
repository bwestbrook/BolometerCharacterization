import time
import visa
#from datetime import datetime
from lab_code.lab_serial import lab_serial

class FunctionGenerator():

    def __init__(self, port='COM17'):
        self.port = port
        self._connection = lab_serial(port=self.port)
        rsp = self._query('*IDN?\r\n')
        print(rsp)
        #self._set_lock_in_defaults()
        import ipdb;ipdb.set_trace()

    def _send_command(self, msg):
        self._connection.write(msg)

    def _query(self, query, timeout=0.5):
        self._send_command(query)
        response = self._connection.read()
        return response

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
    fg = FunctionGenerator()
    fg.run()
