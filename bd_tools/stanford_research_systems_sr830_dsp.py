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
        self.sensitivity_range_dict = {
                '0': {
                    'range': 2e-9,
                    'multiplier': 1e9,
                    'units': 'nV'
                    },
                '1': {
                    'range': 5e-9,
                    'multiplier': 1e9,
                    'units': 'nV'
                    },
                '2': {
                    'range': 10e-9,
                    'multiplier': 1e9,
                    'units': 'nV'
                    },
                '3': {
                    'range': 20e-9,
                    'multiplier': 1e9,
                    'units': 'nV'
                    },
                '4': {
                    'range': 50e-9,
                    'multiplier': 1e9,
                    'units': 'nV'
                    },
                '5': {
                    'range': 100e-9,
                    'multiplier': 1e9,
                    'units': 'nV'
                    },
                '6': {
                    'range': 200e-9,
                    'multiplier': 1e9,
                    'units': 'nV'
                    },
                '7': {
                    'range': 500e-9,
                    'multiplier': 1e9,
                    'units': 'nV'
                    },
                '8': {
                    'range': 1e-6,
                    'multiplier': 1e6,
                    'units': 'uV'
                    },
                '9': {
                    'range': 2e-6,
                    'multiplier': 1e6,
                    'units': 'uV'
                    },
                '10': {
                    'range': 5e-6,
                    'multiplier': 1e6,
                    'units': 'uV'
                    },
                '11': {
                    'range': 10e-6,
                    'multiplier': 1e6,
                    'units': 'uV'
                    },
                '12': {
                    'range': 20e-6,
                    'multiplier': 1e6,
                    'units': 'uV'
                    },
                '13': {
                    'range': 50e-6,
                    'multiplier': 1e6,
                    'units': 'uV'
                    },
                '14': {
                    'range': 100e-6,
                    'multiplier': 1e6,
                    'units': 'uV'
                    },
                '15': {
                    'range': 200e-6,
                    'multiplier': 1e6,
                    'units': 'uV'
                    },
                '16': {
                    'range': 500e-6,
                    'multiplier': 1e6,
                    'units': 'uV'
                    },
                '17': {
                    'range': 1e-3,
                    'multiplier': 1e3,
                    'units': 'mV'
                    },
                '18': {
                    'range': 2e-3,
                    'multiplier': 1e3,
                    'units': 'mV'
                    },
                '19': {
                    'range': 5e-3,
                    'multiplier': 1e3,
                    'units': 'mV'
                    },
                '20': {
                    'range': 10e-3,
                    'multiplier': 1e3,
                    'units': 'mV'
                    },
                '21': {
                    'range': 20e-3,
                    'multiplier': 1e3,
                    'units': 'mV'
                    },
                '22': {
                    'range': 50e-3,
                    'multiplier': 1e3,
                    'units': 'mV'
                    },
                '23': {
                    'range': 100e-3,
                    'multiplier': 1e3,
                    'units': 'mV'
                    },
                '24': {
                    'range': 200e-3,
                    'multiplier': 1e3,
                    'units': 'mV'
                    },
                '25': {
                    'range': 500e-3,
                    'multiplier': 1e3,
                    'units': 'mV'
                    },
                '26': {
                    'range': 1e0,
                    'multiplier': 1e0,
                    'units': 'V'
                    }
                }
        self.time_constant_dict = {
                '0': {
                    'range': 10e-6,
                    'multiplier': 1e6,
                    'units': 'us'
                    },
                '1': {
                    'range': 30e-6,
                    'multiplier': 1e6,
                    'units': 'us'
                    },
                '2': {
                    'range': 100e-6,
                    'multiplier': 1e6,
                    'units': 'us'
                    },
                '3': {
                    'range': 300e-6,
                    'multiplier': 1e6,
                    'units': 'us'
                    },
                '4': {
                    'range': 1e-3,
                    'multiplier': 1e3,
                    'units': 'ms'
                    },
                '5': {
                    'range': 3e-3,
                    'multiplier': 1e3,
                    'units': 'ms'
                    },
                '6': {
                    'range': 10e-3,
                    'multiplier': 1e3,
                    'units': 'ms'
                    },
                '7': {
                    'range': 30e-3,
                    'multiplier': 1e3,
                    'units': 'ms'
                    },
                '8': {
                    'range': 100e-3,
                    'multiplier': 1e3,
                    'units': 'ms'
                    },
                '9': {
                    'range': 300e-3,
                    'multiplier': 1e3,
                    'units': 'ms'
                    },
                '10': {
                    'range': 1e0,
                    'multiplier': 1e0,
                    'units': 's'
                    },
                '11': {
                    'range': 3e0,
                    'multiplier': 1e0,
                    'units': 's'
                    },
                '12': {
                    'range': 10e0,
                    'multiplier': 1e0,
                    'units': 's',
                    },
                '13': {
                    'range': 30e-0,
                    'multiplier': 1e0,
                    'units': 's'
                    },
                '14': {
                    'range': 100e0,
                    'multiplier': 1e0,
                    'units': 's'
                    },
                '15': {
                    'range': 300e0,
                    'multiplier': 1e0,
                    'units': 's'
                    },
                '16': {
                    'range': 1e3,
                    'multiplier': 1e-3,
                    'units': 'ks'
                    },
                '17': {
                    'range': 3e3,
                    'multiplier': 1e-3,
                    'units': 'ks'
                    },
                '18': {
                    'range': 10e3,
                    'multiplier': 1e-3,
                    'units': 'ks'
                    },
                '19': {
                    'range': 30e3,
                    'multiplier': 1e-3,
                    'units': 'ks'
                    }
                }
        self.srs_get_current_sensitivity_range()
        self.srs_get_current_time_constant()

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
        self.sensitivity_display_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.sensitivity_display_label, 1, 4, 1, 2)
        # Time Constant 
        time_constant_pushbutton = QtWidgets.QPushButton('Time Constant Down', self)
        time_constant_pushbutton.clicked.connect(self.srs_change_lock_in_time_constant)
        self.layout().addWidget(time_constant_pushbutton, 2, 0, 1, 2)
        sensitivity_up_pushbutton = QtWidgets.QPushButton('Time Constant Up', self)
        sensitivity_up_pushbutton.clicked.connect(self.srs_change_lock_in_time_constant)
        self.layout().addWidget(sensitivity_up_pushbutton, 2, 2, 1, 2)
        self.time_constant_display_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.time_constant_display_label, 2, 4, 1, 2)
        # Zero
        zero_lock_in_pushbutton = QtWidgets.QPushButton('Zero Lock In', self)
        self.layout().addWidget(zero_lock_in_pushbutton, 3, 0, 1, 4)
        zero_lock_in_pushbutton.clicked.connect(self.srs_zero_lock_in_phase)
        # Set Default
        set_defaults_pushbutton = QtWidgets.QPushButton('Set Defaults', self)
        self.layout().addWidget(set_defaults_pushbutton, 4, 0, 1, 4)
        set_defaults_pushbutton.clicked.connect(self.srs_set_bolo_daq_defaults)
        # Get ID
        get_id_pushbutton = QtWidgets.QPushButton('Get ID', self)
        self.layout().addWidget(get_id_pushbutton, 5, 0, 1, 4)
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
        self.status_bar.showMessage('Getting ID')
        QtWidgets.QApplication.processEvents()
        self.srs_send_command('*CLS ')
        idn = self.srs_query('*IDN? ')
        message = 'Found SRS with ID: '
        message += '{0}'.format(idn)
        self.status_bar.showMessage(message)
        QtWidgets.QApplication.processEvents()

    def srs_zero_lock_in_phase(self):
        '''
        '''
        self.srs_send_command('APHS')

    def srs_set_bolo_daq_defaults(self):
        '''
        This sets the sensitivtiy to be fairly high and the time constnat to be 300ms
        '''

        self.srs_change_lock_in_time_constant(setting=9)
        self.srs_change_lock_in_sensitivity_range(setting=16)

    def srs_change_lock_in_sensitivity_range(self):
        '''
        '''
        direction = self.sender().text().split(' ')[-1]
        current_value = self.srs_get_current_sensitivity_range()

    def srs_change_lock_in_sensitivity_range(self, clicked=True, direction=None, setting=None):
        '''
        '''
        direction = self.sender().text().split(' ')[-1]
        current_value = self.srs_get_current_sensitivity_range()
        print(current_value)
        if self.gb_is_float(current_value):
            current_value = int(current_value)
            if setting is not None:
                new_value = int(setting)
            elif direction is not None:
                if direction == 'Up':
                    new_value = int(current_value + 1)
                elif direction == 'Down':
                    new_value = int(current_value - 1)
                else:
                    print("please specificy 'up' or 'down'")
                    new_value = int(current_value)
            if new_value > 26:
                new_value = 26
            if new_value < 0:
                new_value = 0
            self.srs_send_command('SENS {0}'.format(new_value))
        self.srs_get_current_sensitivity_range()

    def srs_get_current_sensitivity_range(self):
        '''
        '''
        self.status_bar.showMessage('Getting Sensistiviy Range')
        QtWidgets.QApplication.processEvents()
        sensitivity_range_index = self.srs_query('SENS?')
        if self.gb_is_float(sensitivity_range_index):
            value = self.sensitivity_range_dict[str(sensitivity_range_index)]['range']
            value *= self.sensitivity_range_dict[str(sensitivity_range_index)]['multiplier']
            units = self.sensitivity_range_dict[str(sensitivity_range_index)]['units']
            sensitivity_string = 'Current Range: [{0}] {1} ({2})'.format(sensitivity_range_index, value, units)
            self.sensitivity_display_label.setText(sensitivity_string)
            self.status_bar.showMessage(sensitivity_string)
            QtWidgets.QApplication.processEvents()
            return int(sensitivity_range_index)
        else:
            return 0

    def srs_change_lock_in_time_constant(self, clicked=True, direction=None, setting=None):
        '''
        '''
        direction = self.sender().text().split(' ')[-1]
        current_value = self.srs_get_current_time_constant()
        if self.gb_is_float(current_value):
            current_value = int(current_value)
            if setting is not None:
                new_value = int(setting)
            elif direction is not None:
                if direction == 'Up':
                    new_value = int(current_value + 1)
                elif direction == 'Down':
                    new_value = int(current_value - 1)
                else:
                    print("please specificy 'up' or 'down'")
                    new_value = int(current_value)
            if new_value > 19:
                new_value = 19
            if new_value < 0:
                new_value = 0
            self.srs_send_command('OFLT {0}'.format(new_value))
        self.srs_get_current_time_constant()

    def srs_get_current_time_constant(self):
        '''
        '''
        self.status_bar.showMessage('Getting Time Constant')
        QtWidgets.QApplication.processEvents()
        time_constant_index = self.srs_query('OFLT?')
        if self.gb_is_float(time_constant_index):
            value = self.time_constant_dict[str(time_constant_index)]['range']
            value *= self.time_constant_dict[str(time_constant_index)]['multiplier']
            units = self.time_constant_dict[str(time_constant_index)]['units']
            time_constant_string = 'Time Constant: [{0}] {1} ({2})'.format(time_constant_index, value, units)
            self.time_constant_display_label.setText(time_constant_string)
            self.status_bar.showMessage(time_constant_string)
            QtWidgets.QApplication.processEvents()
            return int(time_constant_index)
        else:
            return 0
