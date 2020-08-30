
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
        test_widget = QtWidgets.QLabel('SRS ', self)
        self.layout().addWidget(test_widget, 1, 0, 1, 1)

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

