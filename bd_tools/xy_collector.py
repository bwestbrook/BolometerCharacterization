import time
import os
import simplejson
import pylab as pl
import numpy as np
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.daq import DAQ
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class XYCollector(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, available_daqs, status_bar, screen_resolution, monitor_dpi):
        super(XYCollector, self).__init__()
        self.status_bar = status_bar
        self.available_daqs = available_daqs
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.daq = DAQ()
        grid_1 = QtWidgets.QGridLayout()
        self.setLayout(grid_1)
        self.xyc_make_tab_bar()
        self.xyc_input_panel = QtWidgets.QWidget(self)
        grid_2 = QtWidgets.QGridLayout()
        self.xyc_input_panel.setLayout(grid_2)
        self.layout().addWidget(self.xyc_input_panel, 2, 0, 1, 1)
        grid_3 = QtWidgets.QGridLayout()
        self.xyc_plot_panel = QtWidgets.QWidget(self)
        self.xyc_plot_panel.setLayout(grid_3)
        self.layout().addWidget(self.xyc_plot_panel, 2, 1, 1, 1)
        self.x_data = []
        self.y_data = []
        self.xyc_populate(0)
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = './Data/{0}'.format(self.today_str)
        self.squid_calibration_dict  = {'1': 30.0, '2': 26.8, '3': 24.67,
                                        '4': 30.1, '5': 25.9, '6': 25.0}

    ###########
    # GUI and Input Handling
    ###########

    def xyc_populate(self, tab_index):
        '''
        '''
        self.gb_initialize_panel('xyc_input_panel')
        self.gb_initialize_panel('xyc_plot_panel')
        self.xyc_daq_panel()
        self.tab_index = tab_index
        if tab_index == 0: # IV 
            self.xyc_iv_config()
        elif tab_index == 1: # RT
            self.xyc_rt_config()
        self.xyc_make_plot_panel()
        self.xyc_add_buttons()
        self.xyc_daq_tab_bar.currentChanged.connect(self.xyc_display_daq_settings)
        self.xyc_mode_tab_bar.currentChanged.connect(self.xyc_populate)

    def xyc_add_buttons(self):
        '''
        '''
        start_pushbutton = QtWidgets.QPushButton('Start', self)
        start_pushbutton.clicked.connect(self.xyc_start_stop)
        self.xyc_input_panel.layout().addWidget(start_pushbutton, 12, 0, 1, 10)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        save_pushbutton.clicked.connect(self.xyc_save)
        self.xyc_input_panel.layout().addWidget(save_pushbutton, 13, 0, 1, 10)

    def xyc_make_tab_bar(self):
        '''
        '''
        self.xyc_mode_tab_bar = QtWidgets.QTabBar(self)
        for tab in ['IV', 'RT']:
            self.xyc_mode_tab_bar.addTab(tab)
        self.layout().addWidget(self.xyc_mode_tab_bar, 0, 0, 1, 10)
        self.xyc_daq_tab_bar = QtWidgets.QTabBar(self)
        for tab in self.available_daqs:
            self.xyc_daq_tab_bar.addTab(tab)
        self.layout().addWidget(self.xyc_daq_tab_bar, 1, 0, 1, 10)

    def xyc_daq_panel(self):
        '''
        '''
        self.xyc_initialize_input()
        daq_x_header_label = QtWidgets.QLabel('DAQ Ch X Data:', self)
        self.xyc_input_panel.layout().addWidget(daq_x_header_label, 1, 0, 1, 1)
        self.daq_x_combobox = QtWidgets.QComboBox(self)
        for daq in range(0, 4):
            self.daq_x_combobox.addItem(str(daq))
        self.xyc_input_panel.layout().addWidget(self.daq_x_combobox, 1, 1, 1, 1)
        daq_y_header_label = QtWidgets.QLabel('DAQ Ch Y Data:', self)
        self.xyc_input_panel.layout().addWidget(daq_y_header_label, 1, 2, 1, 1)
        self.daq_y_combobox = QtWidgets.QComboBox(self)
        self.daq_y_combobox.currentIndexChanged.connect(self.xyc_display_daq_settings)
        for daq in range(0, 4):
            self.daq_y_combobox.addItem(str(daq))
        self.xyc_input_panel.layout().addWidget(self.daq_y_combobox, 1, 3, 1, 1)


    def xyc_display_daq_settings(self, index):
        '''
        '''
        self.xyc_initialize_input()
        daq = self.xyc_daq_tab_bar.tabText(self.xyc_daq_tab_bar.currentIndex())
        self.x_channel = self.daq_x_combobox.currentIndex()
        self.y_channel = self.daq_y_combobox.currentIndex()
        # X
        int_time_x_header_label = QtWidgets.QLabel('Int Time X:', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(int_time_x_header_label, 2, 0, 1, 1)
        self.int_time_x = self.available_daqs[daq][str(self.x_channel)]['int_time']
        int_time_x_label = QtWidgets.QLabel(str(self.int_time_x), self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(int_time_x_label, 2, 1, 1, 1)
        sample_rate_x_header_label = QtWidgets.QLabel('Sample Rate X:', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(sample_rate_x_header_label, 3, 0, 1, 1)
        self.sample_rate_x = self.available_daqs[daq][str(self.x_channel)]['sample_rate']
        sample_rate_x_label = QtWidgets.QLabel(str(self.sample_rate_x), self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(sample_rate_x_label, 3, 1, 1, 1)
        # Y
        int_time_y_header_label = QtWidgets.QLabel('Int Time Y:', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(int_time_y_header_label, 2, 2, 1, 1)
        self.int_time_y = self.available_daqs[daq][str(self.y_channel)]['int_time']
        int_time_y_label = QtWidgets.QLabel(str(self.int_time_y), self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(int_time_y_label, 2, 3, 1, 1)
        sample_rate_y_header_label = QtWidgets.QLabel('Sample Rate Y:', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(sample_rate_y_header_label, 3, 2, 1, 1)
        self.sample_rate_y = self.available_daqs[daq][str(self.y_channel)]['sample_rate']
        sample_rate_y_label = QtWidgets.QLabel(str(self.sample_rate_y), self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(sample_rate_y_label, 3, 3, 1, 1)

    def xyc_iv_config(self):
        '''
        '''
        dc_squid_header_label = QtWidgets.QLabel('DC SQUID:', self)
        self.xyc_input_panel.layout().addWidget(dc_squid_header_label, 7, 0, 1, 1)
        dc_squid_combobox = QtWidgets.QComboBox(self)
        for squid in range(1, 7):
            dc_squid_combobox.addItem(str(squid))
        self.xyc_input_panel.layout().addWidget(dc_squid_combobox, 7, 1, 1, 1)

    def xyc_rt_config(self):
        '''
        '''
        grt_serial_header_label = QtWidgets.QLabel('GRT SERIAL:', self)
        self.xyc_input_panel.layout().addWidget(grt_serial_header_label, 7, 0, 1, 1)
        self.grt_serial_combobox = QtWidgets.QComboBox(self)
        for grt_serial in ['Lakeshore']:
            self.grt_serial_combobox.addItem(grt_serial)
        self.xyc_input_panel.layout().addWidget(self.grt_serial_combobox, 7, 1, 1, 1)

    def xyc_initialize_input(self):
        '''
        '''
        # Init
        for x in range(2, 4):
            for y in range(0, 4):
                if self.xyc_input_panel.layout().itemAtPosition(x, y) is not None:
                    self.xyc_input_panel.layout().itemAtPosition(x, y).widget().setParent(None)


    ###########
    # Plotting
    ###########

    def xyc_plot(self):
        '''
        '''
        self.xyc_plot_x()
        self.xyc_plot_y()
        self.xyc_plot_xy()

    def xyc_plot_x(self):
        '''
        '''
        fig, ax = self.xyc_create_blank_fig()
        ax.errorbar(range(len(self.x_data)), self.x_data, self.x_stds, marker='.', linestyle='None')
        fig.savefig('temp_x.png')
        pl.close('all')
        image_to_display = QtGui.QPixmap('temp_x.png')
        self.x_time_stream_label.setPixmap(image_to_display)
        os.remove('temp_x.png')

    def xyc_plot_y(self):
        '''
        '''
        fig, ax = self.xyc_create_blank_fig()
        ax.errorbar(range(len(self.y_data)), self.y_data, self.y_stds, marker='.', linestyle='None')
        fig.savefig('temp_y.png')
        pl.close('all')
        image_to_display = QtGui.QPixmap('temp_y.png')
        self.y_time_stream_label.setPixmap(image_to_display)
        os.remove('temp_y.png')

    def xyc_plot_xy(self):
        '''
        '''
        fig, ax = self.xyc_create_blank_fig()
        ax.errorbar(self.x_data, self.y_data, self.y_stds, marker='.', linestyle='-')
        fig.savefig('temp_xy.png')
        pl.close('all')
        image_to_display = QtGui.QPixmap('temp_xy.png')
        self.xy_scatter_label.setPixmap(image_to_display)
        os.remove('temp_xy.png')

    def xyc_create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.25,
                             left=0.12, right=0.98, top=0.9, bottom=0.23, multiple_axes=False,
                             aspect=None):
        if frac_screen_width is None and frac_screen_height is None:
            fig = pl.figure()
        else:
            width = (frac_screen_width * self.screen_resolution.width()) / self.monitor_dpi
            height = (frac_screen_height * self.screen_resolution.height()) / self.monitor_dpi
            fig = pl.figure(figsize=(width, height))
        if not multiple_axes:
            if aspect is None:
                ax = fig.add_subplot(111)
            else:
                ax = fig.add_subplot(111, aspect=aspect)
        else:
            ax = None
        fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
        return fig, ax

    def xyc_make_plot_panel(self):
        '''
        '''
        # X
        self.xyc_initialize_plot_panel()
        self.x_time_stream_label = QtWidgets.QLabel('', self)
        self.xyc_plot_panel.layout().addWidget(self.x_time_stream_label, 0, 0, 3, 4)
        x_mean_header_label = QtWidgets.QLabel('X Mean: ', self)
        self.xyc_plot_panel.layout().addWidget(x_mean_header_label, 3, 0, 1, 1)
        self.x_mean_label = QtWidgets.QLabel('', self)
        self.xyc_plot_panel.layout().addWidget(self.x_mean_label, 3, 1, 1, 1)
        x_std_header_label = QtWidgets.QLabel('X STD: ', self)
        self.xyc_plot_panel.layout().addWidget(x_std_header_label, 3, 2, 1, 1)
        self.x_std_label = QtWidgets.QLabel('', self)
        self.xyc_plot_panel.layout().addWidget(self.x_std_label, 3, 3, 1, 1)
        # Y
        self.y_time_stream_label = QtWidgets.QLabel('', self)
        self.xyc_plot_panel.layout().addWidget(self.y_time_stream_label, 4, 0, 3, 4)
        y_mean_header_label = QtWidgets.QLabel('Y Mean: ', self)
        self.xyc_plot_panel.layout().addWidget(y_mean_header_label, 7, 0, 1, 1)
        self.y_mean_label = QtWidgets.QLabel('', self)
        self.xyc_plot_panel.layout().addWidget(self.y_mean_label, 7, 1, 1, 1)
        y_std_header_label = QtWidgets.QLabel('Y STD: ', self)
        self.xyc_plot_panel.layout().addWidget(y_std_header_label, 7, 2, 1, 1)
        self.y_std_label = QtWidgets.QLabel('', self)
        self.xyc_plot_panel.layout().addWidget(self.y_std_label, 7, 3, 1, 1)
        # XY
        self.xy_scatter_label = QtWidgets.QLabel('', self)
        self.xyc_plot_panel.layout().addWidget(self.xy_scatter_label, 8, 0, 3, 4)

    def xyc_initialize_plot_panel(self):
        for x in range(0, 4):
            for y in (3, 7):
                if self.xyc_plot_panel.layout().itemAtPosition(x, y) is not None:
                    self.xyc_plot_panel.layout().itemAtPosition(x, y).widget().setParent(None)

    ###########
    # Running
    ###########

    def xyc_start_stop(self):
        '''
        '''
        if 'Start' in self.sender().text():
            self.sender().setText('Stop DAQ')
            self.started = True
            self.xyc_collecter()
        else:
            self.sender().setText('Start DAQ')
            self.started = False

    def xyc_collecter(self):
        '''
        '''
        device = self.xyc_daq_tab_bar.tabText(self.xyc_daq_tab_bar.currentIndex())
        self.x_data, self.x_stds = [], []
        self.y_data, self.y_stds = [], []
        while self.started:
            x_ts, x_mean, x_min, x_max, x_std = self.daq.get_data(signal_channel=self.x_channel,
                                                                  int_time=self.int_time_x,
                                                                  sample_rate=self.sample_rate_x,
                                                                  device=device)
            y_ts, y_mean, y_min, y_max, y_std = self.daq.get_data(signal_channel=self.y_channel,
                                                                  int_time=self.int_time_y,
                                                                  sample_rate=self.sample_rate_y,
                                                                  device=device)
            self.x_mean_label.setText('{0:.5f}'.format(x_mean))
            self.x_std_label.setText('{0:.5f}'.format(x_std))
            self.y_mean_label.setText('{0:.5f}'.format(y_mean))
            self.y_std_label.setText('{0:.5f}'.format(y_std))
            self.x_data.append(x_mean)
            self.x_stds.append(x_std)
            self.y_data.append(y_mean)
            self.y_stds.append(y_std)
            self.xyc_plot()
            QtWidgets.QApplication.processEvents()
            self.repaint()

    def xyc_save(self):
        '''
        '''
        mode = self.xyc_mode_tab_bar.tabText(self.xyc_mode_tab_bar.currentIndex())
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', self.data_folder, '.txt')[0]
        if len(save_path) > 0:
            return None
            with open(save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_data):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_data[i], self.x_stds[i], self.y_data[i], self.y_stds[i])
                    save_handle.write(line)
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')
        fig, ax = self.xyc_create_blank_fig(frac_screen_width=0.5, frac_screen_height=0.5,
                                            left=0.08, right=0.98, top=0.9, bottom=0.13, multiple_axes=False,
                                            aspect=None)
        title, okPressed = self.gb_quick_info_gather(title='Plot Title', dialog='What is the title of this plot?')
        if mode == 'IV':
            if len(title) > 0:
                ax.set_title(title)
            else:
                ax.set_title('I vs V Curve')
            ax.set_xlabel('Bias Voltage (uV)')
            ax.set_ylabel('SQUID Out (V)')
        elif mode == 'RT':
            if len(title) > 0:
                ax.set_title(title)
            else:
                ax.set_title('R vs T Curve')
            ax.set_xlabel('Temperature ($mK$)')
            ax.set_ylabel('Sample Resistance ($m \Omega$)')
        self.xyc_adjust_x_data()
        self.xyc_adjust_y_data()
        ax.errorbar(self.x_data, self.y_data, self.y_stds, marker='.', linestyle='-')
        pl.show()

    def xyc_adjust_x_data(self, bias_voltage_reduction_factor=1e-5):
        '''
        '''
        mode = self.xyc_mode_tab_bar.tabText(self.xyc_mode_tab_bar.currentIndex())
        if mode == 'IV':
            self.x_data = np.asarray(self.x_data) * bias_voltage_reduction_factor
        elif mode == 'RT':
            grt_serial = self.grt_serial_combobox.currentText()
            if grt_serial == 'Lakeshore':
                self.x_data = np.asarray(self.x_data) * 100

    def xyc_adjust_y_data(self, voltage_reduction_factor=1.0e2):
        '''
        '''
        mode = self.xyc_mode_tab_bar.tabText(self.xyc_mode_tab_bar.currentIndex())
        if mode == 'IV':
            squid = self.squid_combobox.currentText()
            calibration_factor = self.squid_calibration_dict[squid]
            self.y_data = np.asarray(self.y_data) * calibration_factor
            self.y_stds = np.asarray(self.y_stds) * calibration_factor
        elif mode == 'RT':
            self.y_data = np.asarray(self.y_data) * voltage_reduction_factor
