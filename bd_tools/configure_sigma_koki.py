import os
import time
from pprint import pprint
from bd_lib.bolo_serial import BoloSerial
from GuiBuilder.gui_builder import GuiBuilder
from PyQt5 import QtCore, QtGui, QtWidgets

class ConfigureSigmaKoki(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, com_port, status_bar, serial_com=None):
        '''
        '''
        super(ConfigureSigmaKoki, self).__init__()
        self.com_port = com_port
        self.status_bar = status_bar
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        if serial_com is None:
            self.serial_com = self.sk_get_serial_com()
        else:
            self.serial_com = serial_com
        self.sk_input_panel()

    def sk_get_serial_com(self):
        '''
        '''
        if not hasattr(self, 'serial_com'):
            self.serial_com = BoloSerial(self.com_port, device='Stepper')
        return self.serial_com

    ###########################################
    # GUI 
    ###########################################

    def sk_input_panel(self):
        '''
        '''
        # Set Position
        self.set_position_lineedit = self.gb_make_labeled_lineedit(label_text='Set Angle (deg):')
        self.set_position_lineedit.setText('45')
        self.layout().addWidget(self.set_position_lineedit, 0, 0, 1, 1)
        self.set_position_lineedit.setValidator(QtGui.QDoubleValidator(0, 360, 3, self.set_position_lineedit))
        self.current_position_label = QtWidgets.QLabel('Current Position (deg): 0', self)
        self.layout().addWidget(self.current_position_label, 0, 1, 1, 1)
        self.set_position_pushbutton = QtWidgets.QPushButton('Set Position', self)
        self.layout().addWidget(self.set_position_pushbutton, 0, 2, 1, 1)
        self.set_position_pushbutton.clicked.connect(self.sk_set_angle)
        label_text = 'Steps per 360 degress\n 72000 comes from 1:144 worm gear reduction times 0.72degs per step'
        self.degs_per_step_lineedit = self.gb_make_labeled_lineedit(label_text=label_text, lineedit_text='72000')
        self.degs_per_step_lineedit.setDisabled(True)
        self.layout().addWidget(self.degs_per_step_lineedit, 1, 0, 1, 1)
        #self.set_position_lineedit.setValidator(QtGui.QIntValidator(0, 360, self.set_position_lineedit))


        # Special Position Set Home
        self.set_home_pushbutton = QtWidgets.QPushButton('Set Home', self)
        self.layout().addWidget(self.set_home_pushbutton, 3, 1, 1, 1)
        self.set_home_pushbutton.clicked.connect(self.sk_set_home)

        # Stop
        self.stop_pushbutton = QtWidgets.QPushButton('Stop', self)
        self.layout().addWidget(self.stop_pushbutton, 2, 1, 1, 1)
        self.stop_pushbutton.clicked.connect(self.sk_stop)
        self.stop_hard_pushbutton = QtWidgets.QPushButton('Emergency Stop', self)
        self.layout().addWidget(self.stop_hard_pushbutton, 2, 2, 1, 1)
        self.stop_hard_pushbutton.clicked.connect(self.sk_stop_hard)

    ###########################################
    # Serial Communication 
    ###########################################

    def sk_send_command(self, msg):
        '''
        '''
        self.serial_com.bs_write(msg)

    def sk_query(self, query, timeout=0.5):
        '''
        '''
        self.sk_send_command(query)
        response = self.serial_com.bs_read()
        print()
        print('query')
        print(query)
        print('response')
        print(response)
        print()
        return response

    def sk_stop(self):
        '''
        '''
        self.sk_query('L:1')

    def sk_stop_hard(self):
        '''
        '''
        self.sk_query('L:E')

    def sk_set_home(self):
        '''
        '''
        self.sk_query('H:1')
        self.current_position_label.setText('Current Position (deg): 0')

    def sk_set_angle(self, clicked, set_to_position_deg=None, degs_per_step=72000):
        '''
        '''
        print(set_to_position_deg)
        if set_to_position_deg is None:
            set_to_position_deg = float(self.set_position_lineedit.text())
        self.current_position_label.setText('Current Position (deg): {0}'.format(set_to_position_deg))
        set_to_position_motor = int(degs_per_step * (set_to_position_deg / 360.))
        query = 'A:1+P{0}'.format(set_to_position_motor)
        response = self.sk_query(query)
        self.sk_query('G:')
        return response

    def sk_set_position(self, clicked, position=None, degs_per_step=72000):
        '''
        '''
        query = 'A:1+P{0}'.format(position)
        response = self.sk_query(query)
        self.sk_query('G:')
        return response
