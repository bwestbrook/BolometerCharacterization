from lab_code.lab_serial import lab_serial
import sys
import time
import numpy as np
from operator import mul, truediv
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import csv

class stepper_motor():

    def __init__(self, port):
        self.port = port
        self._connection = lab_serial(port=self.port)
        self._setup()

    def _setup(self):
        self._send_command('PM2\r\n') # set for SCL ready code when turned on
        self._send_command('ME\r\n') # Motor is enabled 
        self._send_command('DL1\r\n') # Set limit to be normally open

    def _send_command(self, msg):
        self._connection.write(msg)

    def _query_motor(self, query, timeout=0.5):
        self._send_command(query)
        response = self._connection.read()
        return response

    def move_to_position(self, x):
        # check that this is a valid position
        # convert physical units to stepper motor units
        # tell the motor what to do
        #import ipdb;ipdb.set_trace()
        self._send_command("DI{:d}\r\n".format(int(x)))
        response = self._query_motor("DI\r\n")
        self._send_command('FP\r\n')
        # check that the motor did what you wanted
        # IP, EP, commands to see

    def reset_zero(self):
        self._send_command('SP0\r\n')
        self._send_command('SP\r\n')

    def get_motor_current(self):
        current = self._query_motor('CC\r\n')
        return current

    def get_motor_voltage(self):
        voltage = self._query_motor('RA\r\n')
        return voltage

    def get_position(self):
        return self._query_motor('SP\r\n')

    def get_velocity(self):
        velocity = self._query_motor('VE\r\n')
        return velocity

    def get_acceleration(self):
        acceleration = self._query_motor('AC\r\n')
        return acceleration

    def set_current(self,current):
        self._send_command('CC{:f}\r\n'.format(current))

    def set_acceleration(self, acceleration):
        self._send_command('AC{:f}\r\n'.format(acceleration))

    def set_velocity(self, velocity):
        """
        Set the desired velocity (angular velocity of the HWP itself, not the servo)
        Arguments:
            velocity (float) - angular velocity in Hz
        """
        self._send_command('VE{:f}\r\n'.format(velocity))

    def finite_rotation(self, step_size):
        degrees = step_size*2500/6
        # degrees = step_size
        self._setup()
        self._send_command('DI{:d}\r\n'.format(int(degrees)))
        self._send_command('FL\r\n')

    def get_simulated_data(self, datatype, current_position, noise=10):
        '''
        noise is in percent and is of the max-min of data
        '''
        in_degree = current_position*np.pi/180
        dev = (np.random.randn()-0.5)*2/100*noise
        simulated_data = np.sin(in_degree) + dev
        print(simulated_data)
        return simulated_data

    def get_active_serial_ports(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        active_ports = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                active_ports.append(port)
            except (OSError, serial.SerialException):
                pass
        return active_ports

if __name__ == '__main__':
    SM = stepper_motor('COM9')
    import ipdb;ipdb.set_trace()
