import os
import time
import simplejson
from bd_lib.daq import DAQ
from pprint import pprint
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder

class ConfigureDAQ(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, available_daqs, status_bar, n_channels=8):
        '''
        '''
        super(ConfigureDAQ, self).__init__()
        self.status_bar = status_bar
        self.available_daqs = available_daqs
        self.n_channels = n_channels
        self.class_name = 'md'
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.cd_add_daq_tabs()
        self.cd_add_channels()
        self.cd_add_controls()
        self.daq = DAQ()

    def cd_add_controls(self, sample_rate=1000, int_time=500):
        '''
        '''
        read_daq_pushbutton = QtWidgets.QPushButton('Start DAQ', self)
        read_daq_pushbutton.clicked.connect(self.cd_start_stop)
        self.layout().addWidget(read_daq_pushbutton, 10, 0, 1, 16)
        set_daq_pushbutton = QtWidgets.QPushButton('Set DAQ', self)
        set_daq_pushbutton.clicked.connect(self.cd_set_daq)
        self.layout().addWidget(set_daq_pushbutton, 11, 0, 1, 16)

    def cd_add_daq_tabs(self):
        '''
        '''
        daq_tab_bar = QtWidgets.QTabBar(self)
        self.daq_tab_bar = daq_tab_bar
        for active_daq in self.available_daqs:
            daq_tab_bar.addTab(active_daq)
        self.layout().addWidget(daq_tab_bar, 0, 0, 1, 16)
        self.daq_tab_bar.setCurrentIndex(len(self.available_daqs) - 1)

    def cd_add_channels(self):
        '''
        '''
        for i in range(self.n_channels):
            self.cd_add_channel(i)

    def cd_start_stop(self, sample_rate=1000, int_time=500):
        '''
        '''
        if 'Start' in self.sender().text():
            self.sender().setText('Stop DAQ')
            self.started = True
            self.status_bar.showMessage('Collecting Data')
            self.cd_get_daq()
        else:
            self.sender().setText('Start DAQ')
            self.started = False
            self.status_bar.showMessage('Paused')

    def cd_add_channel(self, index):
        '''
        '''
        if len(self.available_daqs) == 0:
            return None
        device = self.daq_tab_bar.tabText(self.daq_tab_bar.currentIndex())
        channel_header_label = QtWidgets.QLabel('DAQ {0}'.format(index), self)
        self.layout().addWidget(channel_header_label, 1, index * 2, 1, 1)
        channel_checkbox = QtWidgets.QCheckBox('Enabled', self)
        setattr(self, 'channel_{0}_checkbox'.format(index), channel_checkbox)
        self.layout().addWidget(channel_checkbox, 2, index * 2, 1, 1)
        channel_value_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(channel_value_label, 3, index * 2, 1, 1)
        setattr(self, 'channel_{0}_value_label'.format(index), channel_value_label)
        # Sample Rate
        channel_sample_rate_header_label = QtWidgets.QLabel('Sample Rate', self)
        self.layout().addWidget(channel_sample_rate_header_label, 4, index * 2, 1, 1)
        channel_sample_rate_combobox = QtWidgets.QComboBox(self)
        setattr(self, 'channel_{0}_sample_rate_combobox'.format(index), channel_sample_rate_combobox)
        self.layout().addWidget(channel_sample_rate_combobox, 4, index * 2 + 1, 1, 1)
        for i, sample_rate in enumerate([100, 500, 1000, 2000, 5000]):
            channel_sample_rate_combobox.addItem(str(sample_rate))
            saved_value = self.available_daqs[device][str(index)]['sample_rate']
            if str(saved_value) == str(sample_rate):
                saved_index = i
        channel_sample_rate_combobox.setCurrentIndex(saved_index)
        # Integration Time
        channel_sample_rate_header_label = QtWidgets.QLabel('Integration Time', self)
        self.layout().addWidget(channel_sample_rate_header_label, 5, index * 2, 1, 1)
        channel_int_time_combobox = QtWidgets.QComboBox(self)
        setattr(self, 'channel_{0}_int_time_combobox'.format(index), channel_int_time_combobox)
        for i, int_time in enumerate([100, 500, 1000]):
            channel_int_time_combobox.addItem(str(int_time))
            saved_value = self.available_daqs[device][str(index)]['int_time']
            if str(saved_value) == str(int_time):
                saved_index = i
        channel_int_time_combobox.setCurrentIndex(saved_index)
        self.layout().addWidget(channel_int_time_combobox, 5, index * 2 + 1, 1, 1)

    def cd_set_daq(self):
        '''
        '''
        device = self.daq_tab_bar.tabText(self.daq_tab_bar.currentIndex())
        for i in range(self.n_channels):
            sample_rate = getattr(self, 'channel_{0}_sample_rate_combobox'.format(i)).currentText()
            int_time = getattr(self, 'channel_{0}_int_time_combobox'.format(i)).currentText()
            self.available_daqs[device][i] = {
                'sample_rate' : sample_rate,
                'int_time' : int_time,
                }
        with open(os.path.join('bd_settings', 'daq_settings.json'), 'w') as json_handle:
            simplejson.dump(self.available_daqs, json_handle, indent=4, sort_keys=True)

    def cd_get_daq(self):
        while self.started:
            enabled = False
            for i in range(self.n_channels):
                if getattr(self, 'channel_{0}_checkbox'.format(i)).isChecked():
                    enabled = True
                    device = self.daq_tab_bar.tabText(self.daq_tab_bar.currentIndex())
                    sample_rate = getattr(self, 'channel_{0}_sample_rate_combobox'.format(i)).currentText()
                    int_time = getattr(self, 'channel_{0}_int_time_combobox'.format(i)).currentText()
                    vol_ts, vol_mean, vol_min, vol_max, vol_std = self.daq.get_data(signal_channel=i,
                                                                                    int_time=int_time,
                                                                                    sample_rate=sample_rate,
                                                                                    device=device)
                    info = '\nDevice: ' + str(device)
                    info = '\n\nVol: ' + str(vol_mean)
                    info += '\n\nSample Rate: ' + str(sample_rate)
                    info += '\n\nIntegration Time: ' + str(int_time)
                    getattr(self, 'channel_{0}_value_label'.format(i)).setText(info)
                    self.repaint()
                    QtWidgets.QApplication.processEvents()
            if not enabled:
                QtWidgets.QApplication.processEvents()
