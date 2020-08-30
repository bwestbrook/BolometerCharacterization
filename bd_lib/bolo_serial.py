"""
Class for communicating with RS232 lab devices w/ a USB-to-RS232 converter
"""
import serial
import time

class BoloSerial(object):

    def __init__(self, port, device=None, splash_screen=None):
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
        self.serial_com_dict = {
            'Model372': {  ## The Lakeshores on the DRs 08/20/2020
                'baudrate': 57600,
                'parity': serial.PARITY_ODD,
                'stopbits': serial.STOPBITS_ONE,
                'bytesize': serial.SEVENBITS,
                'timeout': 2
                },
            'Agilent E3634A': {
                'baudrate': 9600,
                #'parity': serial.PARITY_NONE,
                'timeout': 2
                },
            'Stepper': {
                'baudrate': 9600,
                'timeout': 2
                },
            'SRS_SR830_DSP': {
                'baudrate': 9600,
                'timeout': 3
                }
            }
        self.port = port
        if device in self.serial_com_dict:
            if splash_screen is not None:
                splash_screen.showMessage('Configuring for {0} using {1}'.format(device, self.port))
            self.ser = serial.Serial(port=self.port,
                                     **self.serial_com_dict[device])
        else:
            self.ser = serial.Serial(port=self.port,
                                     baudrate = 9600,
                                     parity = serial.PARITY_EVEN,
                                     timeout = 5)
        if not self.ser.isOpen():
            self.ser.open() # sometimes it's already open
        if self.ser.isOpen():
            if splash_screen is not None:
                splash_screen.showMessage('Successfully opened serial connection on port {:s}!'.format(port))
        else:
            raise RuntimeError('Failed to open serial connection on port {:s}.'.format(port))
        self.ser.flushInput()
        self.ser.flushOutput()

    def bs_write(self, string, encode=None, verbatim=False):
        """
        Properly terminates and encodes a message, then writes it to the port
        """
        if not string.endswith('\r\n') and not verbatim:
            string += '\r\n'
        self.ser.write(string.encode('utf-8')) # unicode not supported for serial module in python 3
        #self.ser.write(string.encode('ASCII')) # unicode not supported for serial module in python 3

    def bs_read(self, decode='latin-1'):
        "Returns a properly decoded string of the bytes read from the port"
        response = self.ser.readline()
        response = response.decode(decode).strip('\r\n')
        print()
        print(response)
        print(response)
        print()
        return response

    def bs_write_read(self, string, wait_time=1, verbatim=False):
        self.bs_write(string, verbatim=verbatim)
        time.sleep(wait_time)
        return self.bs_read()

    def bs_is_open(self):
        return self.ser.isOpen()

    def bs_close(self):
        self.ser.close()

    def bs_reopen(self):
        if self.is_open():
            print('Warning! Attempt made to re-open serial connection that is already open.  Doing nothing...')
        else:
            self.__init__(port=self.port) # careful in case I start adding extra functionality to the constructor

    def bs_is_stepper(self):
        '''
        '''
        try:
            float(self.csm_get_current())
            is_stepper = True
        except ValueError:
            is_stepper = False
        if is_stepper:
            self.status_bar.showMessage('Found a stepper motor on {0}'.format(self.com_port))
        else:
            self.status_bar.showMessage('{0} is not a stepper motor'.format(self.com_port))
        return is_stepper

if __name__ == '__main__':
    bs = BoloSerial('COM10', device='SRS_SR830_DSP')
    bs.bs_write('*cls ')
    idn = bs.bs_write_read('*idn? \n', verbatim=True)
    print(idn)
    import ipdb;ipdb.set_trace()
