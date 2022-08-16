import time
import os
import simplejson
import pylab as pl
import numpy as np
from datetime import datetime
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from bd_lib.bolo_serial import BoloSerial
from PyQt5 import QtCore, QtGui, QtWidgets
#from bd_lib.mpl_canvas import MplCanvas
from GuiBuilder.gui_builder import GuiBuilder, GenericClass


class HewlettPackard34401A(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(HewlettPackard34401A, self).__init__()

        self.status_bar = status_bar
        self.serial_com_1 = BoloSerial('COM19', device='HP_34401A', splash_screen=self.status_bar)
        self.serial_com_2 = BoloSerial('COM20', device='HP_34401A', splash_screen=self.status_bar)
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.hp_build_control_panel()
        self.resistances_1 = [1]
        self.resistances_2 = [2]
        self.times_1 = [datetime.fromtimestamp(time.time())]
        self.times_2 = [datetime.fromtimestamp(time.time())]
        self.hp_plot_resistances(False)

    def hp_update_serial_com(self, serial_com):
        '''
        '''
        self.serial_com = serial_com
        self.hp_get_id()

    def hp_build_control_panel(self):
        '''
        '''
        welcome_label = QtWidgets.QLabel('Welcome to the Hewlett Packard 34401A Controller!', self)
        self.layout().addWidget(welcome_label, 0, 0, 1, 4)
        get_id_pushbutton = QtWidgets.QPushButton('Get ID', self)
        self.layout().addWidget(get_id_pushbutton, 1, 0, 1, 2)
        get_id_pushbutton.clicked.connect(self.hp_get_id)
        self.select_dev_combobox = self.gb_make_labeled_combobox(label_text='Select Dev')
        for device in range(1, 3):
            self.select_dev_combobox.addItem(str(device))
        self.layout().addWidget(self.select_dev_combobox, 1, 2, 1, 2)
        get_resistance_pushbutton = QtWidgets.QPushButton('Get Res', self)
        self.layout().addWidget(get_resistance_pushbutton, 2, 0, 1, 4)
        get_resistance_pushbutton.clicked.connect(self.hp_get_resistance)


        self.label_1_lineedit = self.gb_make_labeled_lineedit(label_text='HP1', lineedit_text='1')
        self.layout().addWidget(self.label_1_lineedit, 3, 0, 1, 2)
        self.label_2_lineedit = self.gb_make_labeled_lineedit(label_text='HP2', lineedit_text='2')
        self.layout().addWidget(self.label_2_lineedit, 3, 2, 1, 2)

        plot_resistance_pushbutton = QtWidgets.QPushButton('START', self)
        self.layout().addWidget(plot_resistance_pushbutton, 4, 0, 1, 2)
        plot_resistance_pushbutton.clicked.connect(self.hp_start_stop)

        continue_pushbutton = QtWidgets.QPushButton('Continue', self)
        self.layout().addWidget(continue_pushbutton, 4, 2, 1, 2)
        continue_pushbutton.clicked.connect(self.hp_continue)


        self.fig_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.fig_label, 5, 0, 1, 4)


    def hp_get_id(self, clicked):
        '''
        '''
        dev = self.select_dev_combobox.currentText()
        self.hp_send_command('*CLS ')
        idn = getattr(self, 'serial_com_{0}'.format(dev)).bs_write_read('*IDN? ')
        message = 'ID {0}'.format(idn)
        self.status_bar.showMessage(message)

    def hp_send_command(self, msg):
        '''
        '''
        dev = self.select_dev_combobox.currentText()
        getattr(self, 'serial_com_{0}'.format(dev)).bs_write(msg)

    def hp_start_stop(self):
        '''
        '''
        self.resistances_1 = []
        self.resistances_2 = []
        self.times_1 = []
        self.times_2 = []
        if self.sender().text() == "START":
            self.sender().setText("STOP")
            self.started = True
            self.hp_log_resistance()
        else:
            self.sender().setText("START")
            self.started = False

    def hp_continue(self):
        '''
        '''
        self.started = True
        self.hp_log_resistance()
        print('continuing to log')

    def hp_log_resistance(self):
        '''
        '''
        i = 0
        while self.started:
            resistance_1 = self.hp_get_resistance(False, dev=1)
            time_stamp_1 = datetime.now()
            if len(resistance_1) > 0:
                self.resistances_1.append(float(resistance_1))
                self.times_1.append(time_stamp_1)
            resistance_2 = self.hp_get_resistance(False, dev=2)
            time_stamp_2 = datetime.now()
            if len(resistance_2) > 0:
                self.resistances_2.append(float(resistance_2))
                self.times_2.append(time_stamp_2)
            self.hp_plot_resistances(False)
            status_line = 'Resistances: {0} {1} {2} {3}\n'.format(
                    self.times_1[i],
                    self.resistances_1[i],
                    self.times_2[i],
                    self.resistances_2[i])
            self.status_bar.showMessage(status_line)
            QtWidgets.QApplication.processEvents()
            self.hp_save_data()
            i += 1


    def hp_save_data(self):
        '''
        '''
        data_save_path = os.path.join('temp_files', 'temp_hp_log.txt')
        with open(data_save_path, 'w') as fh:
            for i, time_stamp_1 in enumerate(self.times_1):
                line = '{0} {1} {2} {3}\n'.format(
                    self.times_1[i],
                    self.resistances_1[i],
                    self.times_2[i],
                    self.resistances_2[i])
                fh.write(line)

    def hp_plot_resistances(self, clicked, dev=None):
        '''
        '''
        fig = pl.figure()
        ax = fig.add_subplot(111)
        label_1 = self.label_1_lineedit.text()
        label_2 = self.label_2_lineedit.text()
        pl.plot(self.times_1, self.resistances_1, 'r', label=label_1)
        pl.plot(self.times_2, self.resistances_2, 'g', label=label_2)
        pl.legend()
        save_path = os.path.join('temp_files', 'temp_hp.png')
        fig.savefig(save_path)
        image_to_display = QtGui.QPixmap(save_path)
        self.fig_label.setPixmap(image_to_display)
        QtWidgets.QApplication.processEvents()
        pl.close()

    def hp_get_resistance(self, clicked, dev=None):
        '''
        '''
        if dev is None:
            dev = self.select_dev_combobox.currentText()
        self.hp_send_command('*CLS ')
        self.hp_send_command(':SYST:REM')
        query = ":MEAS:RES? "
        resistance = getattr(self, 'serial_com_{0}'.format(dev)).bs_write_read(query)
        query = ":SYST:ERR?"
        sys_error = getattr(self, 'serial_com_{0}'.format(dev)).bs_write_read(query)
        self.status_bar.showMessage(str(resistance))
        return resistance

    def get_resistance(self):
        resistance = self._query_mm(":MEAS:RES?\r\n")
        if self._is_float(resistance):
            resistance_str = '{0:.2f} Ohms'.format(float(resistance))
        else:
            resistance_str = resistance
        if self._is_float(resistance):
            return float(resistance), resistance_str
        else:
            self._send_mm_command("*CLS\r\n;")
            time.sleep(0.5)
            self.get_resistance()

