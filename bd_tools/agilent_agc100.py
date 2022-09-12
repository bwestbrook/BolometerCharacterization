# Class to handle cbs_readommunication with Agilent pressure gauge readout box
# Model: AGC-100

import serial
import time # handling sleep
import sys
import os
import shutil
import datetime
import pylab as pl
import numpy as np
from bd_lib.mpl_canvas import MplCanvas
from PyQt5.QtCore import *
from PyQt5 import QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass


class AgilentAGC100(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, serial_com, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(AgilentAGC100, self).__init__()
        self.serial_com = serial_com
        self.status_bar = status_bar
        self.mplc = MplCanvas(self, screen_resolution, monitor_dpi)
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.aa_main_panel()
        self.times = [datetime.datetime.fromtimestamp(time.time())]
        self.pressures = [1]
        self.aa_plot_pressures()
        self.qthreadpool = QThreadPool()


    def aa_main_panel(self):
        '''
        '''
        self.plot_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.plot_label, 0, 0, 1, 5)
        self.sample_interval_lineedit = self.gb_make_labeled_lineedit(label_text='Sample_Rate (s):', lineedit_text='3')
        self.layout().addWidget(self.sample_interval_lineedit, 1, 0, 1, 1)
        self.log_file_name_lineedit = self.gb_make_labeled_lineedit(label_text='File_Name')
        self.layout().addWidget(self.log_file_name_lineedit, 1, 1, 1, 1)
        now = datetime.datetime.now()
        now_str = datetime.datetime.strftime(now, '%Y_%b_%d')
        self.log_file_name_lineedit.setText('pressure_log' + now_str + '_log.txt')
        self.log_data_pushbutton = QtWidgets.QPushButton('Start Logging', self)
        self.layout().addWidget(self.log_data_pushbutton, 1, 2, 1, 1)
        self.log_data_pushbutton.clicked.connect(self.aa_start_stop)
        self.aa_save_pushbutton = QtWidgets.QPushButton('Save', self)
        self.layout().addWidget(self.aa_save_pushbutton, 1, 3, 1, 1)
        self.aa_save_pushbutton.clicked.connect(self.aa_save)

    def aa_organize_pressure(self, status, pressure):
        '''
        '''
        self.status_bar.showMessage(status)
        self.status_bar.showMessage(status)
        QtWidgets.QApplication.processEvents()
        time_stamp = datetime.datetime.fromtimestamp(time.time())
        status_line = 'Pressure: {}\t{}\t{}\n'.format(
            time_stamp,
            datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-7))).isoformat(),
            pressure)
        self.status_bar.showMessage(status_line)
        self.pressures.append(pressure)
        self.times.append(time_stamp)
        self.aa_plot_pressures()


    def aa_start_stop(self):
        '''
        '''
        if self.sender().text().startswith('Start'):
            self.sender().setText('Stop Logging')
            self.started = True
            self.aa_log_data()
        else:
            self.communicator.stop()
            self.sender().setText('Start Logging')
            self.started = False

    def aa_log_data(self):
        '''
        '''
        self.communicator = Communicator(self, self.serial_com)
        self.communicator.signals.pressure_ready.connect(self.aa_organize_pressure)
        self.qthreadpool.start(self.communicator)
        while self.started:
            QtWidgets.QApplication.processEvents()


    def aa_plot_pressures(self):
        '''
        '''
        fig = pl.figure(figsize=(8,4))
        ax = fig.add_subplot(111)
        ax.set_title('Pressure Log of ACG 100')
        ax.set_xlabel('Time Stamp')
        ax.set_ylabel('Pressure (mBar)')
        pl.semilogy(self.times, self.pressures)
        save_path = os.path.join('temp_files', 'temp_pressures.png')
        fig.savefig(save_path)
        image_to_display = QtGui.QPixmap(save_path)
        self.plot_label.setPixmap(image_to_display)
        QtWidgets.QApplication.processEvents()
        pl.close()

    def aa_save(self):
        '''
        '''
        save_path = os.path.join('temp_files', 'temp_pressures.png')
        new_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', save_path, '')[0]
        new_path = new_path + '.png'
        shutil.copy(save_path, new_path)
        new_data_path = new_path.replace('png', 'txt')
        self.aa_save_data(save_path=new_data_path)

    def aa_save_data(self, save_path=None):
        '''
        '''
        if save_path is None:
            log_file_name = self.log_file_name_lineedit.text()
            save_path = os.path.join('log_files', log_file_name)
        with open(save_path, 'w') as fh:
            for i, time in enumerate(self.times):
                data_line = '{}, {}, {}\n'.format(
                    time,
                    datetime.datetime.strftime(time, '%Y_%m_%d_%H_%M_%S'),
                    self.pressures[i])
                fh.write(data_line)


class Communicator(QRunnable):
    '''
    Handles serial communication
    '''
    def __init__(self, aa, serial_com):
        '''
        '''
        self.aa = aa
        self.serial_com = serial_com
        self.ACK = '\x06'
        self.ENQ = '\x05'
        self.NAK = '\x15'
        self.CMD_END = '\r\n'
        self.signals = CommunicatorSignals()
        super(Communicator, self).__init__()

    @pyqtSlot()
    def stop(self):
        '''
        '''
        self.aa.started = False

    @pyqtSlot()
    def run(self):
        '''
        '''
        self.aa.times = []
        self.aa.pressures = []
        sample_wait = float(self.aa.sample_interval_lineedit.text())
        while self.aa.started:
            status, pressure_value = self.aa_read_pressure()
            self.signals.pressure_ready.emit(status, pressure_value)
            time.sleep(sample_wait)

    def write(self, cmd):
        '''
        '''
        self.serial_com.bs_write(cmd)
        report = self.serial_com.bs_read()

    def read(self):
        '''
        '''
        # Assumes cmd sent and ack received from AGC
        self.serial_com.bs_write(self.ENQ.encode('ascii'))
        out = self.serial_com.bs_read()
        return out.rstrip(self.CMD_END.encode('ascii'))

    def get_response(self, cmd):
        '''
        '''
        result = self.write(cmd)
        time.sleep(1.5)
        if result == 0:
            output = self.read().decode()
        else:
            print('CMD not acknowledged')
            output = ''
        return output

    def aa_read_pressure(self):
        pressure_cmd = 'PR1'
        self.serial_com.bs_write(pressure_cmd)
        report = self.serial_com.ser.readline()
        pressure = np.nan
        message = ''
        if report.rstrip(self.CMD_END.encode('ascii')) == self.ACK.encode('ascii'):
            self.serial_com.ser.write(self.ENQ.encode('ascii'))
            pressure_return = self.serial_com.ser.readline()
            msg, pressure = pressure_return.decode().split(',')
            pressure = float(pressure)
            if msg == '1':
                message = 'Gauge underrange!'
            elif msg == '2':
                message = 'Gauge overrange!'
            elif msg == '3':
                message = 'Sensor error!'
            elif msg == '4':
                message = 'Sensor off!'
            elif msg == '5':
                message = 'No sensor detected!'
            elif msg == '6':
                message = 'Identification error!'
            elif msg == '7':
                message = 'Error FRG-720, FRG-730!'
            else:
                message = 'Sucess'
                pressure = float(pressure)
        return message, pressure

    def close(self):
        self.serial_com.close()


class CommunicatorSignals(QObject):
    '''
    This collects the data and sends signals back to the cod e
    '''

    pressure_ready = pyqtSignal(str, float)
