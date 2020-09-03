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
from bd_lib.iv_curves import IVCurves
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class XYCollector(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, mode, daq_settings, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(XYCollector, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.daq = BoloDAQ()
        with open(os.path.join('bd_settings', 'squids_settings.json'), 'r') as fh:
            self.squid_calibration_dict = simplejson.load(fh)
        self.voltage_reduction_factor_dict  = {
            '1': 1e-4,
            '2': 1e-5,
            '3': 100,
            '4': 1e3,
            }
        grid_1 = QtWidgets.QGridLayout()
        self.setLayout(grid_1)
        self.xyc_input_panel = QtWidgets.QWidget(self)
        self.xyc_input_panel.setFixedWidth(0.3 * screen_resolution.width())
        grid_2 = QtWidgets.QGridLayout()
        self.xyc_input_panel.setLayout(grid_2)
        self.layout().addWidget(self.xyc_input_panel, 2, 0, 1, 1)
        grid_3 = QtWidgets.QGridLayout()
        self.xyc_plot_panel = QtWidgets.QWidget(self)
        self.xyc_plot_panel.setLayout(grid_3)
        self.xyc_plot_panel.setFixedWidth(0.7 * screen_resolution.width())
        self.layout().addWidget(self.xyc_plot_panel, 2, 1, 20, 1)
        self.x_data = []
        self.x_stds = []
        self.y_data = []
        self.y_stds = []
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = os.path.join('Data', '{0}'.format(self.today_str))
        self.xyc_populate(mode)
        self.xyc_plot_running()
        self.ivc = IVCurves()

    #########################################################
    # GUI and Input Handling
    #########################################################

    def xyc_populate(self, mode):
        '''
        '''
        self.mode = mode
        self.gb_initialize_panel('xyc_input_panel')
        self.gb_initialize_panel('xyc_plot_panel')
        self.xyc_daq_panel()
        if self.mode == 'iv':
            self.xyc_iv_config()
        else:
            self.xyc_rt_config()
        self.xyc_make_plot_panel()
        self.xyc_add_common_widgets()
        self.xyc_plot_running()

    def xyc_add_common_widgets(self):
        '''
        '''
        # Sample Name
        sample_name_header_label = QtWidgets.QLabel('Sample Name:', self.xyc_input_panel)
        sample_name_header_label.setAlignment(QtCore.Qt.AlignRight)
        self.xyc_input_panel.layout().addWidget(sample_name_header_label, 6, 0, 1, 1)
        self.sample_name_lineedit = QtWidgets.QLineEdit('', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(self.sample_name_lineedit, 6, 1, 1, 3)
        # Buttons
        start_pushbutton = QtWidgets.QPushButton('Start', self.xyc_input_panel)
        start_pushbutton.clicked.connect(self.xyc_start_stop)
        self.xyc_input_panel.layout().addWidget(start_pushbutton, 12, 0, 1, 4)
        save_pushbutton = QtWidgets.QPushButton('Save', self.xyc_input_panel)
        save_pushbutton.clicked.connect(self.xyc_save)
        self.xyc_input_panel.layout().addWidget(save_pushbutton, 13, 0, 1, 4)
        spacer_label = QtWidgets.QLabel(' ', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(spacer_label, 14, 0, 6, 4)

    def xyc_daq_panel(self):
        '''
        '''
        self.xyc_initialize_input()
        xyc_daq_header_label = QtWidgets.QLabel('DAQ Device:', self)
        self.xyc_input_panel.layout().addWidget(xyc_daq_header_label, 0, 0, 1, 1)
        self.xyc_daq_combobox = QtWidgets.QComboBox(self)
        for daq in self.daq_settings:
            self.xyc_daq_combobox.addItem(daq)
        self.xyc_input_panel.layout().addWidget(self.xyc_daq_combobox, 0, 1, 1, 3)
        self.xyc_daq_combobox.currentIndexChanged.connect(self.xyc_display_daq_settings)
        daq_x_header_label = QtWidgets.QLabel('DAQ Ch X Data:', self)
        daq_x_header_label.setAlignment(QtCore.Qt.AlignRight)
        self.xyc_input_panel.layout().addWidget(daq_x_header_label, 1, 0, 1, 1)
        self.daq_x_combobox = QtWidgets.QComboBox(self)
        for daq in range(0, 8):
            self.daq_x_combobox.addItem(str(daq))
        self.xyc_input_panel.layout().addWidget(self.daq_x_combobox, 1, 1, 1, 1)
        daq_y_header_label = QtWidgets.QLabel('DAQ Ch Y Data:', self)
        daq_y_header_label.setAlignment(QtCore.Qt.AlignRight)
        self.xyc_input_panel.layout().addWidget(daq_y_header_label, 1, 2, 1, 1)
        self.daq_y_combobox = QtWidgets.QComboBox(self)
        self.daq_y_combobox.currentIndexChanged.connect(self.xyc_display_daq_settings)
        for daq in range(0, 8):
            self.daq_y_combobox.addItem(str(daq))
        self.xyc_input_panel.layout().addWidget(self.daq_y_combobox, 1, 3, 1, 1)

    def xyc_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings
        self.xyc_display_daq_settings()

    def xyc_display_daq_settings(self):
        '''
        '''
        self.xyc_initialize_input()
        daq = self.xyc_daq_combobox.currentText()
        self.x_channel = self.daq_x_combobox.currentIndex()
        self.y_channel = self.daq_y_combobox.currentIndex()
        # X
        self.int_time_x = self.daq_settings[daq][str(self.x_channel)]['int_time']
        self.sample_rate_x = self.daq_settings[daq][str(self.x_channel)]['sample_rate']
        daq_settings_x_info = 'Int Time (ms): {0}\n'.format(self.int_time_x)
        daq_settings_x_info += 'Sample Rate (Hz): {0}'.format(str(self.sample_rate_x))
        daq_settings_x_label = QtWidgets.QLabel(daq_settings_x_info)
        self.xyc_input_panel.layout().addWidget(daq_settings_x_label, 2, 1, 1, 1)
        # Y
        self.int_time_y = self.daq_settings[daq][str(self.y_channel)]['int_time']
        self.sample_rate_y = self.daq_settings[daq][str(self.y_channel)]['sample_rate']
        daq_settings_y_info = 'Int Time (ms): {0}\n'.format(self.int_time_y)
        daq_settings_y_info += 'Sample Rate (Hz): {0}'.format(str(self.sample_rate_y))
        daq_settings_y_label = QtWidgets.QLabel(daq_settings_y_info)
        self.xyc_input_panel.layout().addWidget(daq_settings_y_label, 2, 3, 1, 1)

    def xyc_iv_config(self):
        '''
        '''
        # X Voltage Factor
        x_voltage_factor_header_label = QtWidgets.QLabel('Voltage Factor:', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(x_voltage_factor_header_label, 7, 0, 1, 1)
        self.x_correction_combobox = QtWidgets.QComboBox(self.xyc_input_panel)
        for index, voltage_reduction_factor in self.voltage_reduction_factor_dict.items():
            self.x_correction_combobox.addItem('{0}'.format(voltage_reduction_factor))
        self.xyc_input_panel.layout().addWidget(self.x_correction_combobox, 7, 1, 1, 1)
        # SQUID
        squid_header_label = QtWidgets.QLabel('SQUID (uA/V):', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(squid_header_label, 7, 2, 1, 1)
        self.y_correction_combobox = QtWidgets.QComboBox(self.xyc_input_panel)
        for squid, calibration in self.squid_calibration_dict.items():
            self.y_correction_combobox.addItem('{0} ::: {1:.1f} (uA/V)'.format(squid, float(calibration)))
        self.xyc_input_panel.layout().addWidget(self.y_correction_combobox, 7, 3, 1, 1)
        # Data Clip
        data_clip_lo_header_label = QtWidgets.QLabel('Data Clip Lo (uV):', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(data_clip_lo_header_label, 8, 0, 1, 1)
        data_clip_lo_lineedit = QtWidgets.QLineEdit('0.0', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(data_clip_lo_lineedit, 8, 1, 1, 1)
        self.data_clip_lo_lineedit = data_clip_lo_lineedit
        data_clip_hi_header_label = QtWidgets.QLabel('Data Clip Hi (uV):', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(data_clip_hi_header_label, 8, 2, 1, 1)
        data_clip_hi_lineedit = QtWidgets.QLineEdit('0.0', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(data_clip_hi_lineedit, 8, 3, 1, 1)
        self.data_clip_hi_lineedit = data_clip_hi_lineedit
        # Fit Clip
        fit_clip_lo_header_label = QtWidgets.QLabel('Fit Clip Lo (uV):', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(fit_clip_lo_header_label, 9, 0, 1, 1)
        fit_clip_lo_lineedit = QtWidgets.QLineEdit('0.0', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(fit_clip_lo_lineedit, 9, 1, 1, 1)
        self.fit_clip_lo_lineedit = fit_clip_lo_lineedit
        fit_clip_hi_header_label = QtWidgets.QLabel('Fit Clip Hi (uV):', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(fit_clip_hi_header_label, 9, 2, 1, 1)
        fit_clip_hi_lineedit = QtWidgets.QLineEdit('0.0', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(fit_clip_hi_lineedit, 9, 3, 1, 1)
        self.fit_clip_hi_lineedit = fit_clip_hi_lineedit
        # Extra information
        sample_temp_header_label = QtWidgets.QLabel('Sample Temp (K):', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(sample_temp_header_label, 10, 0, 1, 1)
        self.sample_temp_lineedit = QtWidgets.QLineEdit('', self.xyc_input_panel)
        self.sample_temp_lineedit.setValidator(QtGui.QDoubleValidator(0, 5, 8, self.sample_temp_lineedit))
        self.xyc_input_panel.layout().addWidget(self.sample_temp_lineedit, 10, 1, 1, 1)
        optical_load_header_label = QtWidgets.QLabel('Optical Load (K):', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(optical_load_header_label, 10, 2, 1, 1)
        self.optical_load_lineedit = QtWidgets.QLineEdit('', self.xyc_input_panel)
        self.optical_load_lineedit.setValidator(QtGui.QDoubleValidator(0, 5, 8, self.optical_load_lineedit))
        self.xyc_input_panel.layout().addWidget(self.optical_load_lineedit, 10, 3, 1, 1)
        sample_band_header_label = QtWidgets.QLabel('Sample Band (GHz):', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(sample_band_header_label, 11, 0, 1, 1)
        self.sample_band_combobox = QtWidgets.QComboBox(self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(self.sample_band_combobox, 11, 1, 1, 1)
        for sample_band in ['', 'MF-Sinuous1p5', 'MF-Sinuous0p8', '30', '40', '90', '150', '220', '270']:
            self.sample_band_combobox.addItem(sample_band)


    def xyc_rt_config(self):
        '''
        '''
        # GRT Serial 
        grt_serial_header_label = QtWidgets.QLabel('GRT SERIAL:', self)
        self.xyc_input_panel.layout().addWidget(grt_serial_header_label, 7, 0, 1, 1)
        self.x_correction_combobox = QtWidgets.QComboBox(self)
        for grt_serial in ['Lakeshore']:
            self.x_correction_combobox.addItem(grt_serial)
        self.xyc_input_panel.layout().addWidget(self.x_correction_combobox, 7, 1, 1, 1)
        # Y Voltage Factor 
        y_voltage_factor_header_label = QtWidgets.QLabel('Resistance Voltage Factor', self)
        self.xyc_input_panel.layout().addWidget(y_voltage_factor_header_label, 7, 2, 1, 1)
        self.y_correction_combobox = QtWidgets.QComboBox(self)
        for index, voltage_reduction_factor in self.voltage_reduction_factor_dict.items():
            self.y_correction_combobox.addItem('{0}'.format(voltage_reduction_factor))
        self.xyc_input_panel.layout().addWidget(self.y_correction_combobox, 7, 3, 1, 1)
        # Data Clip
        data_clip_lo_header_label = QtWidgets.QLabel('Data Clip Lo (mK):', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(data_clip_lo_header_label, 8, 0, 1, 1)
        data_clip_lo_lineedit = QtWidgets.QLineEdit('0.0', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(data_clip_lo_lineedit, 8, 1, 1, 1)
        self.data_clip_lo_lineedit = data_clip_lo_lineedit
        data_clip_hi_header_label = QtWidgets.QLabel('Data Clip Hi (mK):', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(data_clip_hi_header_label, 8, 2, 1, 1)
        data_clip_hi_lineedit = QtWidgets.QLineEdit('0.0', self.xyc_input_panel)
        self.xyc_input_panel.layout().addWidget(data_clip_hi_lineedit, 8, 3, 1, 1)
        self.data_clip_hi_lineedit = data_clip_hi_lineedit

    def xyc_initialize_input(self):
        '''
        '''
        # Init
        for x in range(2, 4):
            for y in range(0, 4):
                if self.xyc_input_panel.layout().itemAtPosition(x, y) is not None:
                    self.xyc_input_panel.layout().itemAtPosition(x, y).widget().setParent(None)

    #########################################################
    # Plotting
    #########################################################

    def xyc_make_plot_panel(self):
        '''
        '''
        # X
        self.xyc_initialize_plot_panel()
        self.x_time_stream_label = QtWidgets.QLabel('', self)
        self.x_time_stream_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
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
        self.y_time_stream_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.xyc_plot_panel.layout().addWidget(self.y_time_stream_label, 0, 4, 3, 4)
        y_mean_header_label = QtWidgets.QLabel('Y Mean: ', self)
        self.xyc_plot_panel.layout().addWidget(y_mean_header_label, 4, 5, 1, 1)
        self.y_mean_label = QtWidgets.QLabel('', self)
        self.xyc_plot_panel.layout().addWidget(self.y_mean_label, 4, 6, 1, 1)
        y_std_header_label = QtWidgets.QLabel('Y STD: ', self)
        self.xyc_plot_panel.layout().addWidget(y_std_header_label, 4, 7, 1, 1)
        self.y_std_label = QtWidgets.QLabel('', self)
        self.xyc_plot_panel.layout().addWidget(self.y_std_label, 4, 8, 1, 1)
        # XY
        self.xy_scatter_label = QtWidgets.QLabel('', self)
        self.xy_scatter_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.xyc_plot_panel.layout().addWidget(self.xy_scatter_label, 8, 0, 3, 8)

    def xyc_initialize_plot_panel(self):
        for x in range(0, 4):
            for y in (3, 7):
                if self.xyc_plot_panel.layout().itemAtPosition(x, y) is not None:
                    self.xyc_plot_panel.layout().itemAtPosition(x, y).widget().setParent(None)

    #########################################################
    # Running
    #########################################################

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
        device = self.xyc_daq_combobox.currentText()
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
            self.xyc_plot_running()
            QtWidgets.QApplication.processEvents()
            self.repaint()

    ###################################################
    # Saving and Plotting
    ###################################################

    def xyc_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            file_name = '{0}_{1}.txt'.format(self.sample_name_lineedit.text(), str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def xyc_save(self):
        '''
        '''
        save_path = self.xyc_index_file_name()
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter=',*.txt,*.dat')[0]
        if len(save_path) > 0:
            with open(save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_data):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_data[i], self.x_stds[i], self.y_data[i], self.y_stds[i])
                    save_handle.write(line)
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')
        self.xyc_plot_final()


    def xyc_plot_running(self):
        '''
        '''
        self.xyc_plot_x()
        self.xyc_plot_y()
        self.xyc_plot_xy()

    def xyc_plot_x(self):
        '''
        '''
        fig, ax = self.xyc_create_blank_fig(frac_screen_width=0.35, frac_screen_height=0.35, left=0.23)
        ax.set_xlabel('Sample', fontsize=12)
        ax.set_ylabel('X ($V$)', fontsize=12)
        ax.errorbar(range(len(self.x_data)), self.x_data, self.x_stds, marker='.', linestyle='None')
        fig.savefig('temp_x.png', transparent=True)
        pl.close('all')
        image_to_display = QtGui.QPixmap('temp_x.png')
        self.x_time_stream_label.setPixmap(image_to_display)
        os.remove('temp_x.png')

    def xyc_plot_y(self):
        '''
        '''
        fig, ax = self.xyc_create_blank_fig(frac_screen_width=0.35, frac_screen_height=0.35, left=0.23)
        ax.set_xlabel('Sample', fontsize=12)
        ax.set_ylabel('Y ($V$)', fontsize=12)
        ax.errorbar(range(len(self.y_data)), self.y_data, self.y_stds, marker='.', linestyle='None')
        fig.savefig('temp_y.png', transparent=True)
        pl.close('all')
        image_to_display = QtGui.QPixmap('temp_y.png')
        self.y_time_stream_label.setPixmap(image_to_display)
        os.remove('temp_y.png')

    def xyc_plot_xy(self):
        '''
        '''
        fig, ax = self.xyc_create_blank_fig(frac_screen_width=0.7, frac_screen_height=0.5)
        if self.mode == 'iv':
            ax.set_xlabel('Bias Voltage ($\mu V$)', fontsize=14)
            ax.set_ylabel('TES Current ($\mu A$)', fontsize=14)
        else:
            ax.set_xlabel('Temperature ($mK$)', fontsize=14)
            ax.set_ylabel('Resistance ($\Omega$)', fontsize=14)
        ax.errorbar(self.x_data, self.y_data, self.y_stds, marker='.', linestyle='-')
        fig.savefig('temp_xy.png', transparent=True)
        pl.close('all')
        image_to_display = QtGui.QPixmap('temp_xy.png')
        self.xy_scatter_label.setPixmap(image_to_display)
        os.remove('temp_xy.png')

    def xyc_plot_final(self):
        '''
        '''
        fig, ax = self.xyc_create_blank_fig(frac_screen_width=0.5, frac_screen_height=0.5,
                                            left=0.2, right=0.98, top=0.9, bottom=0.13, multiple_axes=False,
                                            aspect=None)
        title, okPressed = self.gb_quick_info_gather(title='Plot Title', dialog='What is the title of this plot?')
        if self.mode == 'IV':
            if len(title) > 0:
                ax.set_title(title)
            else:
                ax.set_title('I vs V Curve')
            ax.set_xlabel('Bias Voltage (uV)')
            ax.set_ylabel('SQUID Out (uA)')
        elif self.mode == 'RT':
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

    def xyc_adjust_x_data(self):
        '''
        '''
        x_correciton = self.x_correction_combobox.currentText()
        y_correction = self.y_correction_combobox.currentText()
        if self.mode == 'IV':
            voltage_reduction_factor = float(x_correciton)
            self.x_data = np.asarray(self.x_data) * voltage_reduction_factor
            self.x_data = list(self.x_data)
            import ipdb;ipdb.set_trace()
            squid_index = self.y_correction_combobox.currentIndex()
            squid_calibration = self.squid_calibration_dict[self.squid_calibration_dict.keys()[squid_index]]
            self.y_data = np.asarray(self.y_data) * float(squid_calibration)
        elif self.mode == 'RT':
            grt_serial = self.grt_serial_combobox.currentText()
            if grt_serial == 'Lakeshore':
                self.x_data = np.asarray(self.x_data) * 100

    def xyc_adjust_y_data(self, voltage_reduction_factor=1.0e2):
        '''
        '''
        if self.mode == 'IV':
            squid = str(self.squid_combobox.currentIndex() + 1)
            calibration_factor = self.squid_calibration_dict[squid]
            self.y_data = np.asarray(self.y_data) * calibration_factor
            self.y_stds = np.asarray(self.y_stds) * calibration_factor
        elif self.mode == 'RT':
            self.y_data = np.asarray(self.y_data) * voltage_reduction_factor

    def xyc_update_fit_data(self, voltage_factor):
        '''
        Updates fit limits based on IV data
        '''
        fit_clip_hi = self.xdata[0] * float(voltage_factor) * 1e6 # uV
        data_clip_lo = self.xdata[-1] * float(voltage_factor) * 1e6 + self.data_clip_offset # uV
        data_clip_hi = fit_clip_hi # uV
        fit_clip_lo = data_clip_lo + self.fit_clip_offset # uV

    def xyc_final_iv_plot(self):
        '''
        '''
        # Data fitting and clipping
        fit_clip_hi = self.fit_clip_hi_lineedit.text()
        fit_clip_lo = self.fit_clip_lo_lineedit.text()
        data_clip_lo = self.data_clip_lo_lineedit.text()
        data_clip_hi = self.data_clip_hi_lineedit.text()
        fit_clip = (fit_clip_lo, fit_clip_hi)
        data_clip = (data_clip_lo, data_clip_hi)
        # Extra parameters 
        sample_temp = self.sample_temp_lineedit.text()
        optical_load = self.optical_load_lineedit.text()
        sample_band = self.sample_band_lineedit.currentText()
        # Extra parameters 
        label = self.sample_name_lineedit.text()
        title = '{0} @ {1} w {2} Load'.format(label, sample_temp, optical_load)
        v_bias_real, i_bolo_real, i_bolo_std = ivc.convert_IV_to_real_units(np.asarray(self.x_data), np.asarray(self.y_data),
                                                                            stds=np.asarray(self.y_std),
                                                                            squid_conv=squid_conversion,
                                                                            v_bias_multiplier=voltage_factor,
                                                                            determine_calibration=False,
                                                                            clip=fit_clip, label=label)

    def bd_final_rt_plot(self):
        '''
        '''
        meta_data = self.bd_get_all_meta_data(popup='xy_collector')
        plot_params = self.bd_get_all_params(meta_data, settings.xy_collector_plot_params, 'xy_collector')
        rtc = RTCurve([])
        invert = getattr(self, '_xy_collector_popup_invert_output_checkbox').isChecked()
        normal_res = str(getattr(self, '_xy_collector_popup_sample_res_lineedit').text())
        if self.gb_is_float(normal_res, enforce_positive=True):
            normal_res = float(normal_res)
        else:
            normal_res = np.nan
        pprint(plot_params)
        title = '{0} R vs. T'.format(plot_params['sample_name'])
        label = '{0}-{1}'.format(plot_params['sample_name'], plot_params['sample_drift_direction'])
        data_clip_lo = float(plot_params['data_clip_lo'])
        data_clip_hi = float(plot_params['data_clip_hi'])
        if len(self.xdata) > 2:
            xlim_range = data_clip_hi - data_clip_lo
            xlim = (data_clip_lo - 0.01 * xlim_range, data_clip_hi + 0.01 * xlim_range)
            input_dict = {'invert': invert, 'normal_res': normal_res, 'label': label,
                          'title': title, 'xlim': xlim}
            sample_res_vector = rtc.normalize_squid_output(self.ydata, input_dict)
            selector = np.logical_and(np.asarray(self.xdata) > data_clip_lo, np.asarray(self.xdata) < data_clip_hi)
            self.active_fig = rtc.plot_rt_curves(np.asarray(self.xdata)[selector], np.asarray(sample_res_vector)[selector],
                                                 in_millikelvin=True, fig=None, input_dict=input_dict)
            self.temp_plot_path = './temp_files/temp_rt_png.png'
            self.active_fig.savefig(self.temp_plot_path)
        self.bd_adjust_final_plot_popup('RT', xlabel='Sample Temp (mK)', ylabel='Sample Res ($\Omega$)', title=title)

    def xyc_create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.25,
                             left=0.15, right=0.98, top=0.9, bottom=0.23, multiple_axes=False,
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
        ax.tick_params(axis='x', labelsize=16)
        ax.tick_params(axis='y', labelsize=16)
        return fig, ax
