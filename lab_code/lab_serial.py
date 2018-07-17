"""
Class for communicating with RS232 lab devices w/ a USB-to-RS232 converter
"""

import serial
import time

DEFAULT_PORT = '/dev/ttyUSB0'

class lab_serial(object):
    def __init__(self, port=DEFAULT_PORT, verbose=True):
        self.port = port
        self.verbose = verbose
        self.ser = serial.Serial(port = self.port,
                                 baudrate = 9600,
                                 bytesize = serial.EIGHTBITS,
                                 parity = serial.PARITY_NONE,
                                 stopbits = serial.STOPBITS_TWO,
                                 timeout = 1,
                                 xonxoff = False,
                                 rtscts = False,
                                 dsrdtr = True,
                                 writeTimeout = 1)
        if not self.ser.isOpen():
            self.ser.open() # sometimes it's already open
        if self.ser.isOpen():
            if self.verbose:
                print('Successfully opened serial connection on port {:s}!'.format(port))
        else:
            raise RuntimeError('Failed to open serial connection on port {:s}.'.format(port))

        self.ser.flushInput()
        self.ser.flushOutput()


    def write(self, string):
        """
        Properly terminates and encodes a message, then writes it to the port
        """
        if not string.endswith('\r\n'): # the '\n' may not be necessary, but the '\r' usually is.  Depends on the device, so add both
            string += '\r\n'
        self.ser.write(string.encode()) # unicode not supported for serial module in python 3

        
    def read(self):
        "Returns a properly decoded string of the bytes read from the port"
        return self.ser.readline().decode('utf-8').strip('\r\n')

    
    def write_read(self, string, wait_time=0.1):
        self.write(string)
        time.sleep(wait_time)
        return self.read()

    
    def is_open(self):
        return self.ser.isOpen()

        
    def close(self):
        self.ser.close()

        
    def reopen(self):
        if self.is_open():
            print('Warning! Attempt made to re-open serial connection that is already open.  Doing nothing...')
        else:
            self.__init__(port=self.port, verbose=self.verbose) # careful in case I start adding extra functionality to the constructor
