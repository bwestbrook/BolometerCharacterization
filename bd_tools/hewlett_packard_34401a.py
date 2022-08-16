import time
import shutil
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
from PyQt5.QtCore import *
from PyQt5 import  QtGui, QtWidgets
#from bd_lib.mpl_canvas import MplCanvas
from GuiBuilder.gui_builder import GuiBuilder, GenericClass


class HewlettPackard34401A(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, serial_com_hp1, serial_com_hp2, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(HewlettPackard34401A, self).__init__()
        self.serial_com_hp1 = serial_com_hp1
        self.serial_com_hp2 = serial_com_hp2
        self.status_bar = status_bar
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
        self.qthreadpool = QThreadPool()

    def hp_build_control_panel(self):
        '''
        '''
        welcome_label = QtWidgets.QLabel('Welcome to the Hewlett Packard 34401A Controller!', self)
        self.layout().addWidget(welcome_label, 0, 0, 1, 4)
        #get_id_pushbutton = QtWidgets.QPushButton('Get ID', self)
        #self.layout().addWidget(get_id_pushbutton, 1, 0, 1, 2)
        #get_id_pushbutton.clicked.connect(self.hp_get_id)
        self.select_dev_combobox = self.gb_make_labeled_combobox(label_text='Select Dev')
        for device in range(1, 3):
            self.select_dev_combobox.addItem(str(device))
        self.layout().addWidget(self.select_dev_combobox, 1, 2, 1, 2)
        self.label_1_lineedit = self.gb_make_labeled_lineedit(label_text='HP1', lineedit_text='1')
        self.layout().addWidget(self.label_1_lineedit, 3, 0, 1, 2)
        self.label_2_lineedit = self.gb_make_labeled_lineedit(label_text='HP2', lineedit_text='2')
        self.layout().addWidget(self.label_2_lineedit, 3, 2, 1, 2)
        plot_resistance_pushbutton = QtWidgets.QPushButton('Start', self)
        self.layout().addWidget(plot_resistance_pushbutton, 4, 0, 1, 2)
        plot_resistance_pushbutton.clicked.connect(self.hp_start_stop)
        save_pushbutton = QtWidgets.QPushButton('Save ', self)
        self.layout().addWidget(save_pushbutton, 4, 2, 1, 2)
        save_pushbutton.clicked.connect(self.hp_save)
        self.fig_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.fig_label, 5, 0, 1, 4)


    def hp_start_stop(self):
        '''
        '''
        if self.sender().text() == "Start":
            self.sender().setText("Stop")
            self.started = True
            self.hp_log_resistance()
        else:
            self.communicator.stop()
            self.sender().setText("Start")
            self.started = False

    def hp_organize_resistances(self, time_stamp_1, resistance_1, time_stamp_2, resistance_2):
        '''
        '''
        QtWidgets.QApplication.processEvents()
        if len(resistance_1) > 0:
            self.resistances_1.append(float(resistance_1))
            self.times_1.append(time_stamp_1)
        if len(resistance_2) > 0:
            self.resistances_2.append(float(resistance_2))
            self.times_2.append(time_stamp_2)
        self.hp_plot_resistances(False)
        status_line = 'Resistances: {0} {1} {2} {3}\n'.format(
                self.times_1[-1],
                self.resistances_1[-1],
                self.times_2[-1],
                self.resistances_2[-1])
        self.status_bar.showMessage(status_line)

    def hp_log_resistance(self):
        '''
        '''
        self.communicator = Communicator(self)
        self.communicator.signals.resistance_ready.connect(self.hp_organize_resistances)
        i = 0
        self.qthreadpool.start(self.communicator)
        while self.started:
            QtWidgets.QApplication.processEvents()

    def hp_save(self):
        '''
        '''
        new_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', '', '')[0]
        save_path = os.path.join('temp_files', 'temp_hp.png')
        new_path = new_path + '.png'
        shutil.copy(save_path, new_path)
        new_data_path = new_path.replace('png', 'txt')
        self.hp_save_data(save_path=new_data_path)
        data_save_path = os.path.join('temp_files', 'temp_hp_log.txt')
        self.hp_save_data(data_save_path)

    def hp_save_data(self, save_path=None):
        '''
        '''
        if save_path is None:
            log_file_name = self.log_file_name_lineedit.text()
            save_path = os.path.join('log_files', log_file_name)
        with open(save_path, 'w') as fh:
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





class Communicator(QRunnable):
    '''
    '''
    def __init__(self, hp):
        '''
        '''
        self.hp = hp
        self.serial_com_1 = hp.serial_com_hp1
        self.serial_com_2 = hp.serial_com_hp1
        super(Communicator, self).__init__()
        self.signals = CommunicatorSignals()

    def hp_get_id(self, clicked):
        '''
        '''
        dev = self.select_dev_combobox.currentText()
        self.hp_send_command('*CLS ')
        idn = getattr(self, 'serial_com_{0}'.format(dev)).bs_write_read('*IDN? ')
        message = 'ID {0}'.format(idn)
        self.hp.status_bar.showMessage(message)

    def hp_update_serial_com(self, serial_com):
        '''
        '''
        self.serial_com = serial_com
        self.hp_get_id()

    @pyqtSlot()
    def stop(self):
        self.hp.started = False

    @pyqtSlot()
    def run(self):
        '''
        '''
        self.hp.resistances_1 = []
        self.hp.resistances_2 = []
        self.hp.times_1 = []
        self.hp.times_2 = []
        while self.hp.started:
            resistance_1 = self.hp_get_resistance(False, dev=1)
            time_stamp_1 = float(datetime.now().timestamp())
            resistance_2 = self.hp_get_resistance(False, dev=2)
            time_stamp_2 = float(datetime.now().timestamp())
            self.signals.resistance_ready.emit(time_stamp_1, resistance_1, time_stamp_2, resistance_2)

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
        return resistance

    def hp_send_command(self, msg):
        '''
        '''
        dev = self.hp.select_dev_combobox.currentText()
        getattr(self, 'serial_com_{0}'.format(dev)).bs_write(msg)


    def get_resistance(self):
        '''
        '''
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

class CommunicatorSignals(QObject):
    '''
    '''
    resistance_ready = pyqtSignal(float, str, float, str)
