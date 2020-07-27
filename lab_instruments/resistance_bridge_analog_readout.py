"""
Class for reading out the Oxford/Picowatt AVS47 resistance bridge by reading out its analog output voltage
with a HP34401A digital multimeter
"""
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from builtins import super
from future import standard_library
standard_library.install_aliases()

from lab_code import lab_serial
from lab_code import HP34401A

class resistance_bridge_analog_readout(HP34401A.HP34401A):

    def __init__(self, range_setting, port=lab_serial.DEFAULT_PORT, verbose=True):
        super().__init__(port=port, verbose=verbose)
        if range_setting not in [2, 20, 200, 2e3, 20e3, 200e3, 2e6]:
            raise ValueError('Invalid range setting for resistance bridge.  Options: 2, 20, 200, 2e3, 20e3, 200e3, 2e6')
        self.range_setting = range_setting
        
        
    def measure_resistance(self):
        voltage = self.measure_voltage() # Volts
        multiplier = float(self.range_setting / 2)
        resistance = voltage * multiplier # Ohms
        return resistance
        
            
    def reopen(self):
        if self.is_open():
            pass
        else:
            self.__init__(port=self.port, verbose=self.verbose, range_setting = self.range_setting)
