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

class HewlettPackard34401A(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, serial_com, com_port, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(HewlettPackard34401A, self).__init__()
        self.serial_com = serial_com
        self.com_port = com_port
        self.status_bar = status_bar
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.hp_get_id()
        self.hp_build_control_panel()

    def hp_build_control_panel(self):
        '''
        '''
        welcome_label = QtWidgets.QLabel('Welcome to the Hewlett Packard 34401A Controller!', self)
        self.layout().addWidget(welcome_label, 0, 0, 1, 4)
        get_id_pushbutton = QtWidgets.QPushButton('Get ID', self)
        self.layout().addWidget(get_id_pushbutton, 4, 0, 1, 4)
        get_id_pushbutton.clicked.connect(self.hp_get_id)


    def hp_get_id(self):
        '''
        '''
        self.hp_send_command('*CLS ')
        idn = self.hp_query('*IDN? ')
        message = 'ID {0}'.format(idn)
        print(idn)
        self.status_bar.showMessage(message)

    def hp_send_command(self, msg):
        '''
        '''
        self.serial_com.bs_write(msg)

    def hp_query(self, query, timeout=0.5):
        '''
        '''
        self.hp_send_command(query)
        response = self.serial_com.bs_read()
        return response
