import os
from pprint import pprint
from bd_lib.bolo_serial import BoloSerial
from GuiBuilder.gui_builder import GuiBuilder
from PyQt5 import QtCore, QtGui, QtWidgets

class ConfigureStepperMotor(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, com_port, status_bar):
        super(ConfigureStepperMotor, self).__init__()
        self.com_port = com_port
        self.status_bar = status_bar
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.serial_com = BoloSerial(self.com_port, device='Stepper')
        #import ipdb;ipdb.set_trace()
        is_stepper = self.csm_is_stepper()
        if not is_stepper:
            return None
        self.csm_setup()
        self.csm_get_motor_state()
        self.csm_input_panel()

    ###########################################
    # GUI 
    ###########################################

    def csm_input_panel(self):
        '''
        '''
        basic_info_header_label = QtWidgets.QLabel('{0}'.format(self.com_port), self)
        self.layout().addWidget(basic_info_header_label, 0, 1, 1, 1)

    ###########################################
    # Serial Communication 
    ###########################################

    def csm_get_motor_state(self):
        '''
        '''
        stepper_settings_dict = {
            'position': '',
            'velocity': '',
            'acceleration': '',
            'current': '',
            }
        self.status_bar.showMessage('Setting up stepper motor on {0}'.format(self.com_port))
        QtWidgets.QApplication.processEvents()
        for i, item in enumerate(stepper_settings_dict):
            value = getattr(self, 'csm_get_{0}'.format(item))()
            stepper_settings_dict[item] = value
            self.status_bar.showMessage('Getting {0} data for stepper motor on {1}'.format(item, self.com_port))
            QtWidgets.QApplication.processEvents()
            current_value_label = QtWidgets.QLabel('{0}:'.format(item), self)
            self.layout().addWidget(current_value_label, i + 1, 0, 1, 1)
            current_value_lineedit = QtWidgets.QLineEdit(value, self)
            if item == 'position':
                current_value_lineedit.setValidator(QtGui.QIntValidator(-500000, 300000, current_value_lineedit))
            else:
                current_value_lineedit.setValidator(QtGui.QDoubleValidator(0, 1000, 8, current_value_lineedit))
            self.layout().addWidget(current_value_lineedit, i + 1, 1, 1, 1)
            setattr(self, '{0}_lineedit'.format(item), current_value_lineedit)
            set_item_pushbutton = QtWidgets.QPushButton('Set {0}'.format(item), self)
            set_item_pushbutton.clicked.connect(getattr(self, 'csm_set_{0}'.format(item)))
            self.layout().addWidget(set_item_pushbutton, i + 1, 2, 1, 1)
        pprint(stepper_settings_dict)


    def csm_setup(self):
        '''
        '''
        self.csm_send_command('PM2') # set for SCL ready code when turned on
        self.csm_send_command('ME') # Motor is enabled 
        self.csm_send_command('DL1') # Set limit to be normally open

    def csm_send_command(self, msg):
        '''
        '''
        self.serial_com.write(msg)

    def csm_query_motor(self, query, timeout=0.5):
        '''
        '''
        self.csm_send_command(query)
        response = self.serial_com.read()
        return response


    def csm_reset_zero(self):
        '''
        '''
        self.csm_send_command('SP0')
        self.csm_send_command('SP')

    def csm_get_current(self):
        '''
        '''
        current = self.csm_query_motor('CC')
        current = current.split('=')[-1]
        return current

    def csm_get_voltage(self):
        '''
        '''
        voltage = self.csm_query_motor('RA')
        voltage = voltage.split('=')[-1]
        return voltage

    def csm_get_position(self):
        '''
        '''
        position = self.csm_query_motor('SP')
        position = position.split('=')[-1]
        return position

    def csm_get_velocity(self):
        '''
        '''
        velocity = self.csm_query_motor('VE')
        velocity = velocity.split('=')[-1]
        return velocity

    def csm_get_acceleration(self):
        '''
        '''
        acceleration = self.csm_query_motor('AC')
        acceleration = acceleration.split('=')[-1]
        return acceleration

    def csm_set_position(self, x):
        '''
        '''
        # check that this is a valid position
        # convert physical units to stepper motor units
        # tell the motor what to do
        position = int(self.position_lineedit.text())
        self.csm_send_command("DI{:d}".format(position))
        self.csm_send_command("DI")
        self.csm_send_command('FP')
        # check that the motor did what you wanted
        # IP, EP, commands to see
        self.status_bar.showMessage('Set position to {0} on stepper motor {1}'.format(position, self.com_port))
        QtWidgets.QApplication.processEvents()

    def csm_set_current(self):
        '''
        '''
        current = float(self.current_lineedit.text())
        self.csm_send_command('CC{:f}'.format(current))
        current = self.csm_get_current()
        self.status_bar.showMessage('Set current to {0} on stepper motor {1}'.format(current, self.com_port))
        QtWidgets.QApplication.processEvents()

    def csm_set_acceleration(self, acceleration):
        '''
        '''
        acceleration = float(self.acceleration_lineedit.text())
        self.csm_send_command('AC{:f}'.format(acceleration))
        acceleration = self.csm_get_acceleration()
        self.status_bar.showMessage('Set acceleration to {0} on stepper motor {1}'.format(acceleration, self.com_port))
        QtWidgets.QApplication.processEvents()

    def csm_set_velocity(self, velocity):
        """
        Set the desired velocity (angular velocity of the HWP itself, not the servo)
        Arguments:
            velocity (float) - angular velocity in Hz
        """
        velocity = float(self.velocity_lineedit.text())
        self.csm_send_command('VE{:f}'.format(velocity))
        velocity = self.csm_get_velocity()
        self.status_bar.showMessage('Set velocity to {0} on stepper motor {1}'.format(velocity, self.com_port))
        QtWidgets.QApplication.processEvents()

    def csm_finite_rotation(self, step_size):
        '''
        '''
        degrees = step_size*2500/6
        # degrees = step_size
        self._setup()
        self.sm_send_command('DI{:d}'.format(int(degrees)))
        self.sm_send_command('FL')

    def csm_get_simulated_data(self, datatype, current_position, noise=10):
        '''
        noise is in percent and is of the max-min of data
        '''
        in_degree = current_position*np.pi/180
        dev = (np.random.randn()-0.5)*2/100*noise
        simulated_data = np.sin(in_degree) + dev
        print(simulated_data)
        return simulated_data

    def csm_is_stepper(self):
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
