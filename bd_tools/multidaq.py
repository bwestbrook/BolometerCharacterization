import time
from bd_lib.daq import DAQ
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder

class Multidaq(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, active_daqs, n_channels=8):
        '''
        '''
        super(Multidaq, self).__init__()
        self.active_daqs = active_daqs
        self.n_channels = n_channels
        self.class_name = 'md'
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.md_add_daq_tabs()
        self.md_add_channels()
        self.md_add_controls()
        self.real_daq = DAQ()

    def md_add_controls(self, sample_rate=1000, integration_time=500):
        '''
        '''
        read_daq_pushbutton = QtWidgets.QPushButton('Start DAQ', self)
        read_daq_pushbutton.clicked.connect(self.md_start_stop)
        self.layout().addWidget(read_daq_pushbutton, 10, 0, 1, 16)

    def md_add_daq_tabs(self):
        '''
        '''
        daq_tab_bar = QtWidgets.QTabBar(self)
        self.daq_tab_bar = daq_tab_bar
        for active_daq in self.active_daqs:
            daq_tab_bar.addTab(active_daq)
        self.layout().addWidget(daq_tab_bar, 0, 0, 1, 16)
        self.daq_tab_bar.setCurrentIndex(len(self.active_daqs) - 1)

    def md_add_channels(self):
        '''
        '''
        for i in range(self.n_channels):
            self.md_add_channel(i)

    def md_start_stop(self, sample_rate=1000, integration_time=500):
        '''
        '''
        if 'Start' in self.sender().text():
            self.sender().setText('Stop DAQ')
            self.started = True
            self.md_get_daq()
        else:
            self.sender().setText('Start DAQ')
            self.started = False

    def md_add_channel(self, index):
        '''
        '''
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
        for sample_rate in ['100', '1000', '2000', '5000']:
            channel_sample_rate_combobox.addItem(sample_rate)
        # Integration Time
        channel_sample_rate_header_label = QtWidgets.QLabel('Integration Time', self)
        self.layout().addWidget(channel_sample_rate_header_label, 5, index * 2, 1, 1)
        channel_integration_time_combobox = QtWidgets.QComboBox(self)
        setattr(self, 'channel_{0}_integration_time_combobox'.format(index), channel_integration_time_combobox)
        for integration_time in ['100', '500', '1000']:
            channel_integration_time_combobox.addItem(integration_time)
        self.layout().addWidget(channel_integration_time_combobox, 5, index * 2 + 1, 1, 1)

    def md_get_daq(self):
        while self.started:
            enabled = False
            for i in range(self.n_channels):
                if getattr(self, 'channel_{0}_checkbox'.format(i)).isChecked():
                    enabled = True
                    daq = self.daq_tab_bar.tabText(self.daq_tab_bar.currentIndex())
                    sample_rate = getattr(self, 'channel_{0}_sample_rate_combobox'.format(i)).currentText()
                    int_time = getattr(self, 'channel_{0}_integration_time_combobox'.format(i)).currentText()
                    vol_ts, vol_mean, vol_min, vol_max, vol_std = self.real_daq.get_data(signal_channel=i,
                                                                                         integration_time=int_time,
                                                                                         sample_rate=sample_rate,
                                                                                         daq=daq)
                    info = '\nDAQ: ' + str(daq)
                    info = '\n\nVol: ' + str(vol_mean)
                    info += '\n\nSample Rate: ' + str(sample_rate)
                    info += '\n\nIntegration Time: ' + str(int_time)
                    print(i, vol_mean)
                    getattr(self, 'channel_{0}_value_label'.format(i)).setText(info)
                    self.repaint()
                    QtWidgets.QApplication.processEvents()
            if not enabled:
                QtWidgets.QApplication.processEvents()

