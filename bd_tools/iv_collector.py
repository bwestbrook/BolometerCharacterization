import time
import os
import simplejson
import pylab as pl
import numpy as np
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from bd_lib.iv_curves import IVCurves
from bd_lib.saving_manager import SavingManager
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class IVCollector(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(IVCollector, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.daq = BoloDAQ()
        with open(os.path.join('bd_settings', 'squids_settings.json'), 'r') as fh:
            self.squid_calibration_dict = simplejson.load(fh)
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)
        self.voltage_reduction_factor_dict  = {
            '1': 1e-4,
            '2': 1e-5,
            '3': 100,
            '4': 1e3,
            }
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.ivc_plot_panel = QtWidgets.QWidget(self)
        grid_2 = QtWidgets.QGridLayout()
        self.ivc_plot_panel.setLayout(grid_2)
        self.x_data = []
        self.x_stds = []
        self.y_data = []
        self.y_stds = []
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = os.path.join('Data', '{0}'.format(self.today_str))
        self.saving_manager = SavingManager(self, self.data_folder)
        self.ivc_populate()
        self.ivc_plot_running()
        self.ivc = IVCurves()

    #########################################################
    # GUI and Input Handling
    #########################################################

    def ivc_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings
        self.ivc_display_daq_settings()

    def ivc_populate(self):
        '''
        '''
        self.gb_initialize_panel('self')
        self.layout().addWidget(self.ivc_plot_panel, 17, 0, 1, 16)
        self.gb_initialize_panel('ivc_plot_panel')
        self.ivc_daq_panel()
        self.ivc_iv_config()
        self.ivc_make_plot_panel()
        self.ivc_add_common_widgets()
        self.ivc_display_daq_settings()
        self.ivc_plot_running()

    def ivc_lakeshore_panel(self):
        '''
        '''
        # Temp Control
        temp_display_label = QtWidgets.QLabel('Current Temp (Set / Act) [mK]', self)
        self.layout().addWidget(temp_display_label, 0, 5, 1, 1)
        temp_set_point_lineedit = QtWidgets.QLineEdit('0', self)
        self.layout().addWidget(temp_set_point_lineedit, 0, 6, 1, 1)
        temp_set_point_pushbuton = QtWidgets.QPushButton('Set New', self)
        self.layout().addWidget(temp_set_point_pushbuton, 0, 7, 1, 1)
        pid_header_label = QtWidgets.QLabel('P I D', self)
        self.layout().addWidget(pid_header_label, 1, 5, 1, 1)
        self.p_lineedit = QtWidgets.QLineEdit('0', self)
        self.layout().addWidget(self.p_lineedit, 3, 5, 1, 1)
        self.i_lineedit = QtWidgets.QLineEdit('0', self)
        self.layout().addWidget(self.i_lineedit, 3, 6, 1, 1)
        self.d_lineedit = QtWidgets.QLineEdit('0', self)
        self.layout().addWidget(self.d_lineedit, 3, 7, 1, 1)

        # Control Buttons
        configure_channel_pushbutton = QtWidgets.QPushButton('Configure', self)
        self.layout().addWidget(configure_channel_pushbutton, 4, 7, 1, 1)
        configure_channel_pushbutton.clicked.connect(self.ivc_edit_lakeshore_channel)
        scan_and_readout_pushbutton = QtWidgets.QPushButton('Scan', self)
        self.layout().addWidget(scan_and_readout_pushbutton, 4, 6, 1, 1)
        self.channel_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.channel_combobox, 4, 5, 1, 1)
        for channel in range(1, 17):
            self.channel_combobox.addItem(str(channel))

        set_aux_analog_out_pushbutton = QtWidgets.QPushButton('Set Analog Out', self)
        set_aux_analog_out_pushbutton.clicked.connect(self.ivc_edit_lakeshore_aux_ouput)
        self.layout().addWidget(set_aux_analog_out_pushbutton, 5, 5, 1, 3)

        read_ls_372_settings_pushbutton = QtWidgets.QPushButton('Read Settings', self)
        self.layout().addWidget(read_ls_372_settings_pushbutton, 6, 5, 1, 3)
        update_ls_372_settings_pushbutton = QtWidgets.QPushButton('Update Settings', self)
        self.layout().addWidget(update_ls_372_settings_pushbutton, 7, 5, 1, 3)

    def ivc_edit_lakeshore_channel(self):
        '''
        '''
        channel = self.channel_combobox.currentText()
        self.ls_372_widget.ls372_edit_channel(clicked=True, index=channel)

    def ivc_edit_lakeshore_aux_ouput(self):
        '''
        '''
        self.ls_372_widget.ls372_edit_analog_output(clicked=True, analog_output='aux')

    def ivc_display_daq_settings(self):
        '''
        '''
        daq = self.ivc_daq_combobox.currentText()
        self.x_channel = self.daq_x_combobox.currentIndex()
        self.y_channel = self.daq_y_combobox.currentIndex()
        # X
        self.int_time_x = self.daq_settings[daq][str(self.x_channel)]['int_time']
        self.sample_rate_x = self.daq_settings[daq][str(self.x_channel)]['sample_rate']
        daq_settings_x_info = 'Int Time (ms): {0}\n'.format(self.int_time_x)
        daq_settings_x_info += 'Sample Rate (Hz): {0}'.format(str(self.sample_rate_x))
        self.daq_settings_x_label.setText(daq_settings_x_info)
        # Y
        self.int_time_y = self.daq_settings[daq][str(self.y_channel)]['int_time']
        self.sample_rate_y = self.daq_settings[daq][str(self.y_channel)]['sample_rate']
        daq_settings_y_info = 'Int Time (ms): {0}\n'.format(self.int_time_y)
        daq_settings_y_info += 'Sample Rate (Hz): {0}'.format(str(self.sample_rate_y))
        self.daq_settings_y_label.setText(daq_settings_y_info)

    def ivc_daq_panel(self):
        '''
        '''
        # Device
        ivc_daq_header_label = QtWidgets.QLabel('DAQ Device:', self)
        self.layout().addWidget(ivc_daq_header_label, 0, 0, 1, 1)
        self.ivc_daq_combobox = QtWidgets.QComboBox(self)
        for daq in self.daq_settings:
            self.ivc_daq_combobox.addItem(daq)
        self.layout().addWidget(self.ivc_daq_combobox, 0, 1, 1, 3)
        # DAQ Y
        daq_x_header_label = QtWidgets.QLabel('DAQ Ch X Data:', self)
        self.layout().addWidget(daq_x_header_label, 1, 0, 1, 1)
        self.daq_x_combobox = QtWidgets.QComboBox(self)
        for daq in range(0, 8):
            self.daq_x_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_x_combobox, 1, 1, 1, 1)
        self.daq_settings_x_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.daq_settings_x_label, 2, 1, 1, 1)
        # DAQ Y
        daq_y_header_label = QtWidgets.QLabel('DAQ Ch Y Data:', self)
        self.layout().addWidget(daq_y_header_label, 1, 2, 1, 1)
        self.daq_y_combobox = QtWidgets.QComboBox(self)
        for daq in range(0, 8):
            self.daq_y_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_y_combobox, 1, 3, 1, 1)
        self.daq_settings_y_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.daq_settings_y_label, 2, 3, 1, 1)
        self.daq_y_combobox.currentIndexChanged.connect(self.ivc_display_daq_settings)
        self.daq_x_combobox.currentIndexChanged.connect(self.ivc_display_daq_settings)
        self.ivc_daq_combobox.currentIndexChanged.connect(self.ivc_display_daq_settings)

    def ivc_iv_config(self):
        '''
        '''
        # X Voltage Factor
        x_voltage_factor_header_label = QtWidgets.QLabel('Voltage Factor:', self)
        self.layout().addWidget(x_voltage_factor_header_label, 3, 0, 1, 1)
        self.x_correction_combobox = QtWidgets.QComboBox(self)
        for index, voltage_factor in self.voltage_reduction_factor_dict.items():
            self.x_correction_combobox.addItem('{0}'.format(voltage_factor))
        self.layout().addWidget(self.x_correction_combobox, 3, 1, 1, 1)
        # SQUID
        self.squid_calibration_lineedit = QtWidgets.QLineEdit('', self)
        self.squid_calibration_lineedit.setValidator(QtGui.QDoubleValidator(0, 5, 8, self.squid_calibration_lineedit))
        self.layout().addWidget(self.squid_calibration_lineedit, 3, 3, 1, 1)
        self.y_correction_combobox = QtWidgets.QComboBox(self)
        for squid, calibration in self.squid_calibration_dict.items():
            self.y_correction_combobox.addItem('{0}'.format(squid))
        self.y_correction_combobox.setCurrentIndex(-1)
        self.y_correction_combobox.currentIndexChanged.connect(self.ivc_update_squid_calibration)
        self.y_correction_combobox.setCurrentIndex(0)
        self.layout().addWidget(self.y_correction_combobox, 3, 2, 1, 1)
        # Data Clip
        data_clip_lo_header_label = QtWidgets.QLabel('Data Clip Lo (uV):', self)
        self.layout().addWidget(data_clip_lo_header_label, 4, 0, 1, 1)
        data_clip_lo_lineedit = QtWidgets.QLineEdit('0.0', self)
        self.layout().addWidget(data_clip_lo_lineedit, 4, 1, 1, 1)
        self.data_clip_lo_lineedit = data_clip_lo_lineedit
        data_clip_hi_header_label = QtWidgets.QLabel('Data Clip Hi (uV):', self)
        self.layout().addWidget(data_clip_hi_header_label, 4, 2, 1, 1)
        data_clip_hi_lineedit = QtWidgets.QLineEdit('1000.0', self)
        self.layout().addWidget(data_clip_hi_lineedit, 4, 3, 1, 1)
        self.data_clip_hi_lineedit = data_clip_hi_lineedit
        # Fit Clip
        fit_clip_lo_header_label = QtWidgets.QLabel('Fit Clip Lo (uV):', self)
        self.layout().addWidget(fit_clip_lo_header_label, 5, 0, 1, 1)
        fit_clip_lo_lineedit = QtWidgets.QLineEdit('0.0', self)
        self.layout().addWidget(fit_clip_lo_lineedit, 5, 1, 1, 1)
        self.fit_clip_lo_lineedit = fit_clip_lo_lineedit
        fit_clip_hi_header_label = QtWidgets.QLabel('Fit Clip Hi (uV):', self)
        self.layout().addWidget(fit_clip_hi_header_label, 5, 2, 1, 1)
        fit_clip_hi_lineedit = QtWidgets.QLineEdit('1000.0', self)
        self.layout().addWidget(fit_clip_hi_lineedit, 5, 3, 1, 1)
        self.fit_clip_hi_lineedit = fit_clip_hi_lineedit
        # Extra information
        self.sample_temp_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Temp (K)', parent=self)
        self.sample_temp_lineedit.setValidator(QtGui.QDoubleValidator(0, 10000, 8, self.sample_temp_lineedit))
        self.layout().addWidget(self.sample_temp_lineedit, 6, 1, 1, 1)
        optical_load_header_label = QtWidgets.QLabel('Optical Load (K):', self)
        self.layout().addWidget(optical_load_header_label, 6, 2, 1, 1)
        self.optical_load_lineedit = QtWidgets.QLineEdit('', self)
        self.optical_load_lineedit.setValidator(QtGui.QDoubleValidator(0, 500, 8, self.optical_load_lineedit))
        self.layout().addWidget(self.optical_load_lineedit, 6, 3, 1, 1)
        sample_band_header_label = QtWidgets.QLabel('Sample Band (GHz):', self)
        self.layout().addWidget(sample_band_header_label, 7, 0, 1, 1)
        self.sample_band_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.sample_band_combobox, 7, 1, 1, 1)
        for sample_band in ['', 'MF-Sinuous1p5', 'MF-Sinuous0p8', '30', '40', '90', '150', '220', '270']:
            self.sample_band_combobox.addItem(sample_band)

    def ivc_add_common_widgets(self):
        '''
        '''
        row = 8
        # Sample Name
        self.sample_name_combobox = QtWidgets.QComboBox(self)
        for sample in self.samples_settings:
            self.sample_name_combobox.addItem(sample)
        self.sample_name_combobox.currentIndexChanged.connect(self.ivc_update_sample_name)
        self.layout().addWidget(self.sample_name_combobox, row, 3, 1, 1)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name')
        self.layout().addWidget(self.sample_name_lineedit, row, 1, 1, 2)
        row += 1
        # Buttons
        start_pushbutton = QtWidgets.QPushButton('Start', self)
        start_pushbutton.clicked.connect(self.ivc_start_stop)
        self.layout().addWidget(start_pushbutton, row, 0, 1, 4)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        save_pushbutton.clicked.connect(self.ivc_save)
        row += 1
        self.layout().addWidget(save_pushbutton, row, 0, 1, 4)
        row += 1
        spacer_label = QtWidgets.QLabel(' ', self)
        self.layout().addWidget(spacer_label, row, 0, 3, 4)

    def ivc_update_sample_name(self, index):
        '''
        '''
        sample_key = self.sample_name_combobox.currentText()
        sample_name = self.samples_settings[sample_key]
        self.sample_name_lineedit.setText(sample_name)

    def ivc_update_squid_calibration(self, index):
        '''
        '''
        squid_key = self.y_correction_combobox.currentText()
        calibration_value = self.squid_calibration_dict[squid_key]
        self.squid_calibration_lineedit.setText(calibration_value)

    def ivc_update_ls_372_widget(self, ls_372_widget):
        '''
        '''
        self.ls_372_widget = ls_372_widget

    #########################################################
    # Plotting
    #########################################################

    def ivc_make_plot_panel(self):
        '''
        '''
        # X
        self.x_time_stream_label = QtWidgets.QLabel('', self)
        self.x_time_stream_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.ivc_plot_panel.layout().addWidget(self.x_time_stream_label, 17, 0, 1, 1)
        self.x_data_label = QtWidgets.QLabel('X Data: X STD:', self)
        self.ivc_plot_panel.layout().addWidget(self.x_data_label, 18, 0, 1, 1)

        # Y
        self.y_time_stream_label = QtWidgets.QLabel('', self)
        self.y_time_stream_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.ivc_plot_panel.layout().addWidget(self.y_time_stream_label, 19, 0, 1, 1)
        self.y_data_label = QtWidgets.QLabel('Y Data: Y STD:', self)
        self.ivc_plot_panel.layout().addWidget(self.y_data_label, 20, 0, 1, 1)

        # XY
        self.xy_scatter_label = QtWidgets.QLabel('', self)
        self.xy_scatter_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.ivc_plot_panel.layout().addWidget(self.xy_scatter_label, 17, 1, 24, 1)

    #########################################################
    # Running
    #########################################################

    def ivc_start_stop(self):
        '''
        '''
        if 'Start' in self.sender().text():
            self.sender().setText('Stop DAQ')
            self.started = True
            self.ivc_collecter()
        else:
            self.sender().setText('Start DAQ')
            self.started = False
            self.saving_manager.auto_save()

    def ivc_collecter(self):
        '''
        '''
        device = self.ivc_daq_combobox.currentText()
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
            self.x_data_label.setText('X Mean: {0:.5f} ::: X STD: {0:.5f}'.format(x_mean, x_std))
            self.y_data_label.setText('Y Mean: {0:.5f} ::: Y STD: {0:.5f}'.format(y_mean, y_std))
            self.x_data.append(x_mean)
            self.x_stds.append(x_std)
            self.y_data.append(y_mean)
            self.y_stds.append(y_std)
            self.ivc_plot_running()
            QtWidgets.QApplication.processEvents()
            self.repaint()

    ###################################################
    # Saving and Plotting
    ###################################################

    def ivc_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            file_name = '{0}_{1}.txt'.format(self.sample_name_lineedit.text(), str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def ivc_save(self):
        '''
        '''
        save_path = self.ivc_index_file_name()
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter=',*.txt,*.dat')[0]
        if len(save_path) > 0:
            with open(save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_data):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_data[i], self.x_stds[i], self.y_data[i], self.y_stds[i])
                    save_handle.write(line)
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')
        self.ivc_plot_xy()

    def ivc_plot_running(self):
        '''
        '''
        self.ivc_plot_x()
        self.ivc_plot_y()
        self.ivc_plot_xy(running=True)

    def ivc_plot_x(self):
        '''
        '''
        fig, ax = self.ivc_create_blank_fig(frac_screen_width=0.4, frac_screen_height=0.28, left=0.23)
        ax.set_xlabel('Sample', fontsize=12)
        ax.set_ylabel('X ($V$)', fontsize=12)
        ax.errorbar(range(len(self.x_data)), self.x_data, self.x_stds, marker='.', linestyle='None')
        fig.savefig('temp_x.png', transparent=True)
        pl.close('all')
        image_to_display = QtGui.QPixmap('temp_x.png')
        self.x_time_stream_label.setPixmap(image_to_display)
        os.remove('temp_x.png')

    def ivc_plot_y(self):
        '''
        '''
        fig, ax = self.ivc_create_blank_fig(frac_screen_width=0.4, frac_screen_height=0.28, left=0.23)
        ax.set_xlabel('Sample', fontsize=12)
        ax.set_ylabel('Y ($V$)', fontsize=12)
        ax.errorbar(range(len(self.y_data)), self.y_data, self.y_stds, marker='.', linestyle='None')
        fig.savefig('temp_y.png', transparent=True)
        pl.close('all')
        image_to_display = QtGui.QPixmap('temp_y.png')
        self.y_time_stream_label.setPixmap(image_to_display)
        os.remove('temp_y.png')

    def ivc_plot_xy(self, running=False):
        '''
        '''
        fig, ax = self.ivc_create_blank_fig(frac_screen_width=0.65, frac_screen_height=0.65)
        y_data, y_stds = self.ivc_adjust_y_data()
        x_data, x_stds = self.ivc_adjust_x_data()
        ax.set_xlabel('Bias Voltage ($\mu V$)', fontsize=14)
        ax.set_ylabel('TES Current ($\mu A$)', fontsize=14)
        data_clip_lo = float(self.data_clip_lo_lineedit.text())
        data_clip_hi = float(self.data_clip_hi_lineedit.text())
        selector =  np.where(np.logical_and(data_clip_lo < x_data, x_data < data_clip_hi))
        sample_name = self.sample_name_lineedit.text()
        ax.errorbar(x_data[selector], y_data[selector], xerr=x_stds[selector], yerr=y_stds[selector], marker='.', linestyle='-', label=sample_name)
        if running:
            ax.set_xlabel('Bias Voltage ($\mu V$)', fontsize=14)
            ax.set_ylabel('TES Current ($\mu A$)', fontsize=14)
            fig.savefig('temp_xy.png', transparent=True)
            pl.legend(loc='best', fontsize=14)
            pl.close('all')
            image_to_display = QtGui.QPixmap('temp_xy.png')
            self.xy_scatter_label.setPixmap(image_to_display)
            os.remove('temp_xy.png')
        else:
            pl.show()

    def ivc_adjust_x_data(self):
        '''
        '''
        x_data = []
        x_stds = []
        voltage_reduction_factor = float(self.x_correction_combobox.currentText())
        x_data = np.asarray(self.x_data) * voltage_reduction_factor
        x_stds = np.asarray(self.x_stds) * voltage_reduction_factor
        return x_data, x_stds

    def ivc_adjust_y_data(self):
        '''
        '''
        y_data = []
        y_stds = []
        calibration_factor = float(self.squid_calibration_lineedit.text())
        y_data = np.asarray(self.y_data) * calibration_factor
        y_stds = np.asarray(self.y_stds) * calibration_factor
        return y_data, y_stds

    def ivc_update_fit_data(self, voltage_factor):
        '''
        Updates fit limits based on IV data
        '''
        fit_clip_hi = self.xdata[0] * float(voltage_factor) * 1e6 # uV
        data_clip_lo = self.xdata[-1] * float(voltage_factor) * 1e6 + self.data_clip_offset # uV
        data_clip_hi = fit_clip_hi # uV
        fit_clip_lo = data_clip_lo + self.fit_clip_offset # uV

    def ivc_final_iv_plot(self):
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

    def ivc_create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.25,
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
