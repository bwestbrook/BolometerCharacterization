from lab_code.lab_serial import lab_serial
import sys
import serial
import time
import numpy as np
from operator import mul, div
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import csv

class stepper_motor():

    def __init__(self, port):
        self.port = port
        self._connection = lab_serial(port=self.port)
        self._send_command('DL2')

    def _send_command(self, msg):
        ###     if not msg.endswith('\r'):
        #msg +='\r'
        self._connection.write(msg)

    def _query_motor(self, query, timeout=0.5):
        self._send_command(query)
        response = self._connection.read()
        return response

    def move_to_position(self, x):
        # check that this is a valid position
        # convert physical units to stepper motor units
        # tell the motor what to do
        self._setup()
        self._send_command('FP{:d}'.format(int(x)))
        # check that the motor did what you wanted
        # IP, EP, commands to see

    def get_motor_current(self):
        current = self._query_motor('CC')
        return current

    def get_motor_voltage(self):
        voltage = self._query_motor('RA')
        return voltage

    def get_position(self):
        return self._query_motor('SP')

    def get_velocity(self):
        velocity = self._query_motor('VE')
        return velocity

    def get_acceleration(self):
        acceleration = self._query_motor('AC')
        return acceleration

    def set_current(self,current):
        self._send_command('CC{:f}'.format(current))

    def set_acceleration(self, acceleration):
        self._send_command('AC{:f}'.format(acceleration))

    def set_velocity(self, velocity):
        """
        Set the desired velocity (angular velocity of the HWP itself, not the servo)
        Arguments:
            velocity (float) - angular velocity in Hz
        """
        self._send_command('VE{:f}'.format(velocity))

    def finite_rotation(self, step_size):
        degrees = step_size*2500/6
        # degrees = step_size
        self._setup()
        self._send_command('DI{:d}'.format(int(degrees)))
        self._send_command('FL')

    def _setup(self):
        self._send_command('PM2')
        self._send_command('ME')

    def get_simulated_data(self, datatype, current_position, noise=10):
        '''
        noise is in percent and is of the max-min of data
        '''
        in_degree = current_position*np.pi/180
        dev = (np.random.randn()-0.5)*2/100*noise
        simulated_data = np.sin(in_degree) + dev
        print(simulated_data)
        return simulated_data

    def take_pol_efficiency(self, start_angle,end_angle, step_size, pause = 1,noise=10):
        stepnum = div(end_angle-start_angle,step_size)+1
        steps = np.linspace(start_angle,end_angle,stepnum)
        data = []
        for i, step in enumerate(steps):
            data_point = self.get_simulated_data(int, step,noise=noise)
            data.append(data_point)
            if step != 0:
                self.finite_rotation(step_size)
                time.sleep(pause)
            print step, i, data[i]
        data = np.array(data)
        self.write_file(steps,data)
        return steps, data

    def write_file(self,xdata,ydata):
        with open('rawdata.csv','w') as f:
            #wtr = csv.writer(f,delimiter=' ')
            #wtr.writerows([xdata,ydata])
            for x, y in zip(xdata, ydata):
                f.write('{:f}\t{:f}\n'.format(x, y))

    def read_file(self, filename):
        x, y = np.loadtxt(filename, unpack=True)
        return x,y

    def plot_pol_efficiency_data(self,angles, data):
        def func(x,b):
            return np.sin(x*np.pi/180+b)
        plt.title('Data vs Angles')
        plt.xlabel('angles')
        plt.ylabel('data')
        #blue_star, = plt.plot(angles,data, "b*", markersize = 10)
        popt, pocv= curve_fit(func, angles, data)
        #red_dot, = plt.plot(angles, func(angles, popt), "ro", markersize = 10)
        #plt.legend([blue_star, red_dot], ["Original Data","Fitted Data"])
        plt.plot(angles,data, 'b-', label = 'Original Data')
        fitangles = np.linspace(0,360,1)
        plt.plot(fitangles, func(fitangles,popt), 'r--', label = 'Fitted Data')
        plt.legend()
        plt.show()

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
    SM = stepper_motor('COM3')
    # SM.set_current(2)
    # SM.finite_rotation(6000)
    # angles, data = SM.take_pol_efficiency(1, 60, noise = 1)
    # SM.plot_pol_efficiency_data(angles, data)
    import ipdb;ipdb.set_trace()
