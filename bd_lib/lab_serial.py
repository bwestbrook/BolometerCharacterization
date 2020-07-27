"""
Class for communicating with RS232 lab devices w/ a USB-to-RS232 converter
"""
import serial
import time


class lab_serial(object):

    def __init__(self, port, parity=None, verbose=True):
        '''
        #self.ser = serial.Serial(
        port=self.port,
        baudrate = 9600,
        parity = serial.PARITY_NONE,
        stopbits = serial.STOPBITS_TWO,
        timeout = 10,
        xonxoff = False,
        rtscts = False,
        dsrdtr = True,
        writeTimeout = 1)
        '''
        self.port = port
        self.verbose = verbose#
        if parity is None:
            print('This port {0} has no parity parameter'.format(port))
            self.ser = serial.Serial(port=self.port,
                                     baudrate = 9600,
                                     timeout = 3)
        else:
            print('This port {0} has parity {1}'.format(port, parity))
            self.ser = serial.Serial(port=self.port,
                                     baudrate = 9600,
                                     parity = parity,
                                     timeout = 3)
        if not self.ser.isOpen():
            self.ser.open() # sometimes it's already open
        if self.ser.isOpen():
            if self.verbose:
                print('Successfully opened serial connection on port {:s}!'.format(port))
        else:
            raise RuntimeError('Failed to open serial connection on port {:s}.'.format(port))
        self.ser.flushInput()
        self.ser.flushOutput()

    def write(self, string, encode=None):
        """
        Properly terminates and encodes a message, then writes it to the port
        """
        if not string.endswith('\r\n'):
            string += '\r\n'
        #self.ser.write(string.encode('utf-8')) # unicode not supported for serial module in python 3
        self.ser.write(string.encode('ASCII')) # unicode not supported for serial module in python 3

    def read(self, decode='utf-8'):
        "Returns a properly decoded string of the bytes read from the port"
        response = self.ser.readline().decode(decode).strip('\r\n')
        return response

    def read2(self):
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


if __name__ == '__main__':
    LS = lab_serial()
    import ipdb;ipdb.set_trace()
