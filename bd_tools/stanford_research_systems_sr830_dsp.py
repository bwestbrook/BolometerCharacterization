import time
import os
import simplejson
import pylab as pl
import numpy as np
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class StanfordResearchSystemsSR830DSP(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, serial_com, com_port, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(StanfordResearchSystemsSR830DSP, self).__init__()
        self.serial_com = serial_com
        self.com_port = com_port
        self.status_bar = status_bar
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.srs_get_id()
        self.srs_build_control_panel()

    def srs_build_control_panel(self):
        '''
        '''
        welcome_label = QtWidgets.QLabel('Welcome to the Stanford Research Systems SR830 DSP Controller!', self)
        self.layout().addWidget(welcome_label, 0, 0, 1, 4)
        # Sensitivity Range
        sensitivity_down_pushbutton = QtWidgets.QPushButton('Sensitivity Down', self)
        sensitivity_down_pushbutton.clicked.connect(self.srs_change_lock_in_sensitivity_range)
        self.layout().addWidget(sensitivity_down_pushbutton, 1, 0, 1, 2)
        sensitivity_up_pushbutton = QtWidgets.QPushButton('Sensitivity Up', self)
        sensitivity_up_pushbutton.clicked.connect(self.srs_change_lock_in_sensitivity_range)
        self.layout().addWidget(sensitivity_up_pushbutton, 1, 2, 1, 2)
        # Time Constant 
        time_constant_pushbutton = QtWidgets.QPushButton('Time Constant Down', self)
        time_constant_pushbutton.clicked.connect(self.srs_change_lock_in_time_constant)
        self.layout().addWidget(time_constant_pushbutton, 2, 0, 1, 2)
        sensitivity_up_pushbutton = QtWidgets.QPushButton('Time Constant Up', self)
        sensitivity_up_pushbutton.clicked.connect(self.srs_change_lock_in_time_constant)
        self.layout().addWidget(sensitivity_up_pushbutton, 2, 2, 1, 2)
        # Zero
        zero_lock_in_pushbutton = QtWidgets.QPushButton('Zero Lock In', self)
        self.layout().addWidget(zero_lock_in_pushbutton, 3, 0, 1, 4)
        zero_lock_in_pushbutton.clicked.connect(self.srs_zero_lock_in_phase)
        get_id_pushbutton = QtWidgets.QPushButton('Get ID', self)
        self.layout().addWidget(get_id_pushbutton, 4, 0, 1, 4)
        get_id_pushbutton.clicked.connect(self.srs_get_id)

    def srs_update_serial_com(self, serial_com):
        '''
        '''
        self.serial_com = serial_com
        self.srs_get_id()

    def srs_send_command(self, msg):
        '''
        '''
        self.serial_com.bs_write(msg)

    def srs_query(self, query, timeout=0.5):
        '''
        '''
        self.srs_send_command(query)
        response = self.serial_com.bs_read()
        return response

    def srs_get_id(self):
        '''
        '''
        self.srs_send_command('*CLS ')
        idn = self.srs_query('*IDN? ')
        message = 'ID {0}'.format(idn)
        self.status_bar.showMessage(message)

    def srs_zero_lock_in_phase(self):
        '''
        '''
        self.srs_send_command('APHS')

    def srs_change_lock_in_sensitivity_range(self):
        '''
        '''
        direction = self.sender().text().split(' ')[-1]
        current_value = self.srs_get_current_sensitivity_range()

    def srs_change_lock_in_sensitivity_range(self):
        '''
        '''
        direction = self.sender().text().split(' ')[-1]
        current_value = self.srs_get_current_sensitivity_range()
        print(current_value)
        if self.gb_is_float(current_value):
            current_value = int(current_value)
            if direction is not None:
                if direction == 'Up':
                    new_value = int(current_value + 1)
                elif direction == 'Down':
                    new_value = int(current_value - 1)
                else:
                    print("please specificy 'up' or 'down'")
                    new_value = int(current_value)
            elif setting is not None:
                new_value = int(setting)
            if new_value > 26:
                new_value = 26
            if new_value < 0:
                new_value = 0
            self.srs_send_command('SENS {0}'.format(new_value))

    def srs_get_current_sensitivity_range(self):
        '''
        '''
        sensitivity_range_index = self.srs_query('SENS?')
        print()
        print(sensitivity_range_index)
        if self.gb_is_float(sensitivity_range_index):
            return int(sensitivity_range_index)
        else:
            return 0

    def srs_change_lock_in_time_constant(self, direction=None, setting=None):
        '''
        '''
        direction = self.sender().text().split(' ')[-1]
        current_value = self.srs_get_current_time_constant()
        print('tc', current_value)
        if self.gb_is_float(current_value):
            current_value = int(current_value)
            if direction is not None:
                if direction == 'Up':
                    new_value = int(current_value + 1)
                elif direction == 'Down':
                    new_value = int(current_value - 1)
                else:
                    print("please specificy 'up' or 'down'")
                    new_value = int(current_value)
            elif setting is not None:
                new_value = int(setting)
            if new_value > 19:
                new_value = 19
            if new_value < 0:
                new_value = 0
            self.srs_send_command('OFLT {0}'.format(new_value))

    def srs_get_current_time_constant(self):
        '''
        '''
        time_constant_index = self.srs_query('OFLT?')
        print()
        print(time_constant_index)
        if self.gb_is_float(time_constant_index):
            return int(time_constant_index)
        else:
            return 0
