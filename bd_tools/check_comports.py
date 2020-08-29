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

class CheckComPorts(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, status_bar, screen_resolution, monitor_dpi):
        super(CheckComPorts, self).__init__()
        self.status_bar = status_bar
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        test_widget = QtWidgets.QLabel('Check Com Ports', self)
        self.layout().addWidget(test_widget, 0, 1, 1, 1)
