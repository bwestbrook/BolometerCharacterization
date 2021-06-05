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

class AgilentE3634A(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, serial_com, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(AgilentE3634A, self).__init__()
        self.serial_com = serial_com
        self.status_bar = status_bar
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.ae_initialize()
        self.ae_build_panel()

    def ae_update_serial_com(self, serial_com):
        '''
        '''
        self.serial_com = serial_com
        self.ae_get_id()

    def ae_send_command(self, msg):
        '''
        '''
        self.serial_com.bs_write(msg)

    def ae_query(self, query, timeout=0.5):
        '''
        '''
        self.ae_send_command(query)
        response = self.serial_com.bs_read()
        return response

    def ae_apply_voltage(self, volts):
        print()
        print()
        print()
        self.ae_send_command('APPL {0:.2f}, 0.2\r\n'.format(volts))
        self.ae_send_command('OUTP ON\r\n'.format(volts))
        self.serial_com.bs_read()
        return self.ae_get_voltage()

    def ae_get_voltage(self):
        voltage = self.ae_query('MEAS:VOLT?')
        if self.gb_is_float(voltage):
            voltage_str = '{0:.2f}'.format(float(voltage))
        else:
            voltage_str = voltage
        if self.gb_is_float(voltage):
            return float(voltage), voltage_str
        else:
            self.ae_send_command("*CLS\r\n;")
            time.sleep(0.5)
            self.ae_get_voltage()

    def ae_initialize(self):
        self.ae_send_command("INIT\r\n;")
        self.serial_com.bs_read()
        self.ae_send_command("*RST\r\n;")
        self.serial_com.bs_read()
        self.ae_query('MEAS:VOLT?')
        self.ae_apply_voltage(0)
        self.ae_query('MEAS:VOLT?')

    def ae_build_panel(self):
        '''
        '''
        id_number = self.ae_get_id()
        welcome_label = QtWidgets.QLabel('Welcome to the Agilent E3634A Controller {0}'.format(id_number), self)
        self.layout().addWidget(welcome_label, 0, 0, 1, 1)
        for i, config in enumerate(['Voltage']):
            header_label = QtWidgets.QLabel('{0}: '.format(config), self)
            self.layout().addWidget(header_label, i + 1, 0, 1, 1)
            combobox = QtWidgets.QComboBox(self)
            #for item in getattr(self, '{0}_dict'.format(config.lower())):
                #combobox.addItem(item)
            setattr(self, '{0}_combobox'.format(config.lower()), combobox)
            self.layout().addWidget(combobox, i + 1, 1, 1, 1)
            lineedit = QtWidgets.QLineEdit('', self)
            setattr(self, '{0}_lineedit'.format(config.lower()), lineedit)
            self.layout().addWidget(lineedit, i + 1, 2, 1, 1)
            update_pushbutton = QtWidgets.QPushButton('Update', self)
            update_pushbutton.setWhatsThis('{0}_update_pushbutton'.format(config.lower()))
            setattr(self, '{0}_update_pushbutton'.format(config.lower()), lineedit)
            self.layout().addWidget(update_pushbutton, i + 1, 3, 1, 1)
            add_pushbutton = QtWidgets.QPushButton('Add', self)
            add_pushbutton.setWhatsThis('{0}_add_pushbutton'.format(config.lower()))
            self.layout().addWidget(add_pushbutton, i + 1, 4, 1, 1)
            setattr(self, '{0}_add_pushbutton'.format(config.lower()), lineedit)
            remove_pushbutton = QtWidgets.QPushButton('Remove', self)
            remove_pushbutton.setWhatsThis('{0}_remove_pushbutton'.format(config.lower()))
            setattr(self, '{0}_remove_pushbutton'.format(config.lower()), lineedit)
            self.layout().addWidget(remove_pushbutton, i + 1, 5, 1, 1)
            #add_pushbutton.clicked.connect(self.cbd_update_dict)
            update_pushbutton.clicked.connect(self.ae_set_ps_voltage)
            #remove_pushbutton.clicked.connect(self.cbd_update_dict)

    def ae_get_id(self):
        '''
        '''
        self.ae_send_command('*CLS ')
        idn = self.ae_query('*IDN? ')
        message = 'ID {0}'.format(idn)
        self.status_bar.showMessage(message)
        return idn

    def ae_set_ps_voltage(self, voltage_to_set=None):
        if voltage_to_set is None or type(voltage_to_set) is bool:
            voltage_to_set = getattr(self, 'voltage_lineedit').text()
        print(voltage_to_set)
        if self.gb_is_float(voltage_to_set, enforce_positive=True):
            self.ae_apply_voltage(float(voltage_to_set))
            set_voltage, set_voltage_str = self.ae_get_voltage()

    def bd_set_ps_voltage_dial(self):
        dial_value = float(getattr(self, '_power_supply_popup_voltage_control_dial').value())
        getattr(self, '_power_supply_popup_test2_label').setText(str(dial_value))
        self.set_ps_voltage(dial_value)
