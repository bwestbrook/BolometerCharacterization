import sys
import serial
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
from bd_lib.bolo_serial import BoloSerial

class ComPortUtility(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(ComPortUtility, self).__init__()
        self.status_bar = status_bar
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.cpu_get_active_serial_ports()
        self.cpu_gui_panel()

    def cpu_gui_panel(self):
        '''
        '''
        welcome_header_label = QtWidgets.QLabel('Welcome to Comport Utility', self)
        self.layout().addWidget(welcome_header_label, 0, 0, 1, 2)
        self.com_port_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.com_port_combobox, 1, 0, 1, 1)
        for com_port in self.active_com_ports:
            self.com_port_combobox.addItem(com_port)
        self.test_command_lineedit = QtWidgets.QLineEdit('*idn? ', self)
        self.layout().addWidget(self.test_command_lineedit, 1, 1, 1, 2)
        send_command_and_read_pushbutton = QtWidgets.QPushButton('Send Command and Read', self)
        self.layout().addWidget(send_command_and_read_pushbutton, 2, 0, 1, 1)
        send_command_pushbutton = QtWidgets.QPushButton('Send Command', self)
        self.layout().addWidget(send_command_pushbutton, 2, 1, 1, 1)
        read_port_pushbutton = QtWidgets.QPushButton('Read Serial Report', self)
        self.layout().addWidget(read_port_pushbutton, 2, 2, 1, 1)
        self.status_string_label = QtWidgets.QLabel('SERIAL READ', self)
        self.layout().addWidget(self.status_string_label, 3, 0, 1, 3)
        read_port_pushbutton.clicked.connect(self.cpu_read_command)
        send_command_pushbutton.clicked.connect(self.cpu_send_command)
        send_command_and_read_pushbutton.clicked.connect(self.cpu_send_command_and_read)

    def cpu_open_serial_com(self, com_port, splash_screen=None):
        '''
        '''
        if hasattr(self, 'serial_com'):
            self.serial_com.bs_close()
        if splash_screen is not None:
            self.serial_com = BoloSerial(com_port, splash_screen=splash_screen)
        else:
            self.serial_com = BoloSerial(com_port)

    def cpu_send_command(self):
        '''
        '''
        com_port = self.com_port_combobox.currentText()
        command = self.test_command_lineedit.text()
        self.cpu_open_serial_com(com_port, splash_screen=self.status_bar)
        self.serial_com.bs_write(command)

    def cpu_send_command_and_read(self):
        '''
        '''
        com_port = self.com_port_combobox.currentText()
        command = self.test_command_lineedit.text()
        self.cpu_open_serial_com(com_port, splash_screen=self.status_bar)
        self.serial_com.bs_write(command)
        return_value = self.serial_com.bs_read()
        self.status_string_label.setText(return_value)

    def cpu_read_command(self):
        '''
        '''
        com_port = self.com_port_combobox.currentText()
        self.cpu_open_serial_com(com_port, splash_screen=self.status_bar)
        return_value = self.serial_com.bs_read()
        self.status_string_label.setText(return_value)

    def cpu_get_com_device_types(self):
        '''
        '''
        self.lab_devices = [
            'Model372',
            'E3634A',
            ]
        self.com_port_dict = {}
        active_ports = copy(self.active_ports)
        for device in self.lab_devices:
            for active_port in active_ports:
                print()
                print(self.active_ports)
                print(device, active_port)
                serial_com = BoloSerial(port=active_port, device=device, splash_screen=self.splash_screen)
                id_string = serial_com.write_read('*IDN? ')
                self.splash_screen.showMessage("Checking to see what's connected to COM{0} ::: ID = {1}".format(device, id_string))
                print(device in str(id_string))
                print(device)
                print(id_string, type(id_string))
                if device in str(id_string):
                    if not device in self.com_port_dict:
                        self.com_port_dict[device] = comport
                        active_ports.pop(active_port)
                        break
                    else:
                        import ipdb;ipdb.set_trace()
                serial_com.close()
        pprint(self.com_port_dict)

    def cpu_change_status_bar(self, status_bar):
        '''
        '''
        self.status_bar = status_bar

    def cpu_get_active_serial_ports(self):

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
        self.active_com_ports = []
        for port in ports:
            self.status_bar.showMessage('Checking COM Port {0}'.format(port))
            try:
                s = serial.Serial(port)
                s.close()
                self.active_com_ports.append(port)
            except (OSError, serial.SerialException):
                pass
        self.active_com_ports
