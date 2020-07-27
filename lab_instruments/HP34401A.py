"""
Class to control a HP 34401A multimeter over RS232
"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import super
from builtins import int
from builtins import str
from future import standard_library
standard_library.install_aliases()

from lab_code import lab_serial

class HP34401A(lab_serial.lab_serial):

    def __init__(self, port=lab_serial.DEFAULT_PORT, verbose=True):
        super().__init__(port=port, verbose=verbose)
        self.write('*RST') # reset to power on configuration
        self.write('SYSTem:REMote') # set for remote operation
        self.ser.flushInput()
        self.ser.flushOutput()
        self.flush_error_queue()
        
    def measure_voltage(self):
        "Returns the voltage, in Volts, trying twice in case of failure on the first attempt"
        if not self.is_open():
            self.reopen()
        response = self.write_read('MEAS:VOLT:DC? DEF,MIN', wait_time=2.5) # minimum wait time found empirically
        try:
            voltage = float(response)
        except:
            self.flush_error_queue() # beware
            response = self.write_read('MEAS:VOLT:DC? DEF,MIN', wait_time=2.5)
            try:
                voltage = float(response)
            except:
                print('Multimeter is responding with something other than a voltage! {:s}'.format(response))
                voltage = -1.
        return voltage

    
    def read_error(self):
        response = str(self.write_read('SYSTem:ERRor?'))
        error_code = int(response.split(',')[0])
        error_message = response.split(',')[1].replace('"', '') # remove extra quotes
        if self.verbose:
            print(error_message)
        return error_code, error_message

    
    def flush_error_queue(self):
        "The manual says that up to 20 error messages can be stored in the error queue"
        if self.verbose:
            print('Flushing error queue...')
        while True:
            try:
                error_code, error_message = self.read_error()
                if error_code == 0:
                    break
            except:
                pass
        
