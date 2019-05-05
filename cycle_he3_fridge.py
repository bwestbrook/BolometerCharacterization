import time
from lab_code.lab_serial import lab_serial


class FridgeCycle():

    def __init__(self, ps_port='COM6', mm_port='COM3'):
        self.ps_port = ps_port
        self.ps_connection = lab_serial(port=self.ps_port)
        self.mm_port = mm_port
        self.mm_connection = lab_serial(port=self.mm_port)
        self._query_mm('MEAS:RES')
        import ipdb;ipdb.set_trace()

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

    def apply_voltage(self, volts):
        self._send_command('VOLT {0}'.format(volts))

    def check_resistance(self):
        resistance = self._query('RES')
        return resistance

    def run_cycle(self, charcoal_start_resistance=5e5, charcoal_end_resistance=3.5e3, sleep_time=0.5):
        resistance = self.check_resistance()
        # Wait for charcoal to cool down
        while resistance < charcoal_start_resistance:
            time.sleep(sleep_time)
            resistance = self.check_resistance()
            print(resistance)
        # Turn on voltage in steps of 1 volt over with a sleep between
        for i in range(26):
            time.sleep(sleep_time)
            self.apply_voltage(i)
        while resistance > charcoal_end_resistance:
            time.sleep(sleep_time)
            resistance = self.check_resistance()
            print(resistance)

if __name__ == '__main__':
    fc = FridgeCycle()

