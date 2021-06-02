import time
import shutil
import os
import simplejson
import pylab as pl
import numpy as np
import pickle as pkl
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from bd_lib.iv_curve_lib import IVCurveLib
from bd_lib.saving_manager import SavingManager
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class IVCollector(QtWidgets.QWidget, GuiBuilder, IVCurveLib):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, data_folder):
        '''
        '''
        super(IVCollector, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        with open(os.path.join('bd_settings', 'squids_settings.json'), 'r') as fh:
            self.squid_calibration_dict = simplejson.load(fh)
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)
        self.cold_bias_resistor_dict  = {
            '1': 20e-3, # 20mOhm
            '2': 250e-6, # 250microOhm
            }
        self.voltage_reduction_factor_dict  = {
            '1': 9.09e-8,
            '2': 4.28e-7,
            '3': 9.09e-7,
            '4': 1e-6,
            '5': 1e-4,
            '6': 1e-5,
            '7': 100,
            '8': 1e3,
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
        self.data_folder = data_folder
        self.saving_manager = SavingManager(self, self.data_folder, self.ivc_save, 'IV')
        self.ivc_populate()
        self.ivc_plot_running()
        self.qthreadpool = QtCore.QThreadPool()

    #########################################################
    # GUI and Input Handling
    #########################################################

    def ivc_update_samples(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)

    def ivc_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings
        self.ivc_display_daq_settings()

    def ivc_populate(self):
        '''
        '''
        self.gb_initialize_panel('self')
        self.layout().addWidget(self.ivc_plot_panel, 0, 2, 19, 1)
        self.gb_initialize_panel('ivc_plot_panel')
        self.ivc_daq_panel()
        self.ivc_iv_config()
        self.ivc_add_common_widgets()
        self.ivc_make_plot_panel()
        self.ivc_display_daq_settings()
        self.ivc_plot_running()
        self.ivc_daq_combobox.setCurrentIndex(1)
        self.daq_x_combobox.setCurrentIndex(0)
        self.daq_y_combobox.setCurrentIndex(1)

    def ivc_display_daq_settings(self):
        '''
        '''
        daq = self.ivc_daq_combobox.currentText()
        self.x_channel = self.daq_x_combobox.currentIndex()
        self.y_channel = self.daq_y_combobox.currentIndex()

    def ivc_daq_panel(self):
        '''
        '''
        # Device
        self.ivc_daq_combobox = self.gb_make_labeled_combobox(label_text='DAQ Device')
        for daq in self.daq_settings:
            self.ivc_daq_combobox.addItem(daq)
        self.layout().addWidget(self.ivc_daq_combobox, 0, 0, 1, 1)
        # DAQ X
        self.daq_x_combobox = self.gb_make_labeled_combobox(label_text='DAQ X Data:')
        for daq in range(0, 8):
            self.daq_x_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_x_combobox, 1, 0, 1, 1)
        self.daq_settings_x_label = QtWidgets.QLabel('', self)
        self.daq_settings_x_label.setAlignment(QtCore.Qt.AlignLeft)
        self.layout().addWidget(self.daq_settings_x_label, 2, 0, 1, 1)
        # DAQ Y
        self.daq_y_combobox = self.gb_make_labeled_combobox(label_text='DAQ Y Data:')
        for daq in range(0, 8):
            self.daq_y_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_y_combobox, 4, 0, 1, 1)
        self.daq_settings_y_label = QtWidgets.QLabel('', self)
        self.daq_settings_y_label.setAlignment(QtCore.Qt.AlignLeft)
        self.daq_y_combobox.setCurrentIndex(1)
        self.layout().addWidget(self.daq_settings_y_label, 5, 0, 1, 1)
        self.daq_y_combobox.currentIndexChanged.connect(self.ivc_display_daq_settings)
        self.daq_x_combobox.currentIndexChanged.connect(self.ivc_display_daq_settings)
        self.ivc_daq_combobox.currentIndexChanged.connect(self.ivc_display_daq_settings)
        self.ivc_daq_combobox.setCurrentIndex(1)
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Int Time')
        self.int_time_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.int_time_lineedit))
        self.layout().addWidget(self.int_time_lineedit, 6, 0, 1, 1)
        self.int_time_lineedit.setText('100')
        self.int_time = self.int_time_lineedit.text()
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Rate (Hz)')
        self.sample_rate_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.sample_rate_lineedit))
        self.layout().addWidget(self.sample_rate_lineedit, 6, 1, 1, 1)
        self.sample_rate_lineedit.setText('5000')
        self.sample_rate = self.sample_rate_lineedit.text()

    def ivc_calc_x_correction(self):
        '''
        '''
        if len(self.warm_bias_resistor_lineedit.text()) == 0:
            return None
        warm_bias_r = float(self.warm_bias_resistor_lineedit.text())
        cold_bias_r = float(self.cold_bias_resistor_combobox.currentText())
        x_correction_factor = cold_bias_r / warm_bias_r
        self.x_correction_label.setText('X_CORRECTION {0:.8f}'.format(x_correction_factor))


    def ivc_iv_config(self):
        '''
        '''
        self.x_correction_label = QtWidgets.QLabel(self)
        # X Voltage Factor
        self.layout().addWidget(self.x_correction_label, 8, 1, 1, 1)
        self.cold_bias_resistor_combobox = self.gb_make_labeled_combobox(label_text='Cold Bias Resistor:')
        for index, cold_bias_resistance in self.cold_bias_resistor_dict.items():
            self.cold_bias_resistor_combobox.addItem('{0}'.format(cold_bias_resistance))
        self.cold_bias_resistor_combobox.activated.connect(self.ivc_calc_x_correction)
        self.cold_bias_resistor_combobox.setCurrentIndex(0)
        self.layout().addWidget(self.cold_bias_resistor_combobox, 7, 0, 1, 1)
        self.warm_bias_resistor_lineedit = self.gb_make_labeled_lineedit(label_text='Warm Bias Resistor:')
        self.warm_bias_resistor_lineedit.textChanged.connect(self.ivc_calc_x_correction)
        self.warm_bias_resistor_lineedit.setText('20000')
        self.warm_bias_resistor_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e12, 2, self.warm_bias_resistor_lineedit))
        self.layout().addWidget(self.warm_bias_resistor_lineedit, 7, 1, 1, 1)
        # SQUID
        self.squid_calibration_label = QtWidgets.QLabel('', self)
        self.squid_calibration_label.setAlignment(QtCore.Qt.AlignRight)
        self.layout().addWidget(self.squid_calibration_label, 10, 1, 1, 1)
        self.squid_select_combobox = self.gb_make_labeled_combobox(label_text='Select SQUID')
        for squid, calibration in self.squid_calibration_dict.items():
            self.squid_select_combobox.addItem('{0}'.format(squid))
        self.squid_select_combobox.setCurrentIndex(1)
        self.squid_select_combobox.setCurrentIndex(0)
        self.squid_select_combobox.currentIndexChanged.connect(self.ivc_update_squid_calibration)
        self.layout().addWidget(self.squid_select_combobox, 10, 0, 1, 1)
        # Data Clip
        self.data_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Lo (uV)', lineedit_text='0.0')
        self.data_clip_lo_lineedit.returnPressed.connect(self.ivc_plot_running)
        self.data_clip_lo_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.data_clip_lo_lineedit))
        self.layout().addWidget(self.data_clip_lo_lineedit, 11, 0, 1, 1)
        self.data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Hi (uV)', lineedit_text='100.0')
        self.data_clip_hi_lineedit.returnPressed.connect(self.ivc_plot_running)
        self.data_clip_hi_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.data_clip_hi_lineedit))
        self.layout().addWidget(self.data_clip_hi_lineedit, 12, 0, 1, 1)
        # Fit Clip
        self.fit_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Fit Clip Lo (uV)', lineedit_text='0.0')
        self.fit_clip_lo_lineedit.returnPressed.connect(self.ivc_plot_running)
        self.layout().addWidget(self.fit_clip_lo_lineedit, 11, 1, 1, 1)
        self.fit_clip_lo_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.fit_clip_lo_lineedit))
        self.fit_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Fit Clip Hi (uV)', lineedit_text='100.0')
        self.fit_clip_hi_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.fit_clip_hi_lineedit))
        self.fit_clip_hi_lineedit.returnPressed.connect(self.ivc_plot_running)
        self.layout().addWidget(self.fit_clip_hi_lineedit, 12, 1, 1, 1)
        # Extra information
        self.t_bath_lineedit = self.gb_make_labeled_lineedit(label_text='T Bath (mK)')
        self.t_bath_lineedit.setText('275')
        self.t_bath_lineedit.returnPressed.connect(self.ivc_plot_running)
        self.t_bath_lineedit.setValidator(QtGui.QDoubleValidator(0, 10000, 8, self.t_bath_lineedit))
        self.layout().addWidget(self.t_bath_lineedit, 15, 0, 1, 1)
        self.t_load_lineedit = self.gb_make_labeled_lineedit(label_text='T Load (K)')
        self.t_load_lineedit.setText('300')
        self.t_load_lineedit.returnPressed.connect(self.ivc_plot_running)
        self.t_load_lineedit.setValidator(QtGui.QDoubleValidator(0, 500, 8, self.t_load_lineedit))
        self.layout().addWidget(self.t_load_lineedit, 15, 1, 1, 1)
        self.sample_band_combobox = self.gb_make_labeled_combobox(label_text='Sample Band (GHz)')
        self.layout().addWidget(self.sample_band_combobox, 17, 0, 1, 1)
        for sample_band in ['', 'MF-Sinuous1p5', 'MF-Sinuous0p8', '30', '40', '90', '150', '220', '270']:
            self.sample_band_combobox.addItem(sample_band)

    def ivc_add_common_widgets(self):
        '''
        '''
        # Sample Name
        self.sample_name_combobox = self.gb_make_labeled_combobox(label_text='Select Sample')
        for sample in self.samples_settings:
            self.sample_name_combobox.addItem(sample)
        self.sample_name_combobox.currentIndexChanged.connect(self.ivc_update_sample_name)
        self.layout().addWidget(self.sample_name_combobox, 18, 0, 1, 1)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name')
        self.layout().addWidget(self.sample_name_lineedit, 19, 0, 1, 1)
        # Buttons
        start_pushbutton = QtWidgets.QPushButton('Start', self)
        start_pushbutton.clicked.connect(self.ivc_start_stop)
        self.layout().addWidget(start_pushbutton, 20, 0, 1, 1)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        save_pushbutton.clicked.connect(self.ivc_save)
        self.layout().addWidget(save_pushbutton, 21, 0, 1, 1)

    def ivc_update_sample_name(self, index):
        '''
        '''
        sample_key = self.sample_name_combobox.currentText()
        sample_name = self.samples_settings[sample_key]
        squid = sample_key.split('-')[1]
        self.sample_name_lineedit.setText(sample_name)
        for index in range(self.squid_select_combobox.count()):
            if squid in self.squid_select_combobox.itemText(index):
                self.squid_select_combobox.setCurrentIndex(index)
                break

        #import ipdb;ipdb.set_trace()

    def ivc_update_squid_calibration(self, index):
        '''
        '''
        squid_key = self.squid_select_combobox.currentText()
        calibration_value = float(self.squid_calibration_dict[squid_key])
        self.squid_calibration_label.setText('SQ_Correction: {0:.2f} uA/V'.format(calibration_value))
        squid = squid_key.split('-')[1]
        print(squid)
        print(squid)
        print(squid)
        for index in range(self.sample_name_combobox.count()):
            print(index)
            if squid in self.sample_name_combobox.itemText(index):
                self.sample_name_combobox.setCurrentIndex(index)
                break

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
        self.ivc_plot_panel.layout().addWidget(self.x_time_stream_label, 0, 0, 1, 1)
        self.x_data_label = QtWidgets.QLabel('X Data: X STD:', self)
        self.ivc_plot_panel.layout().addWidget(self.x_data_label, 1, 0, 1, 1)

        # Y
        self.y_time_stream_label = QtWidgets.QLabel('', self)
        self.y_time_stream_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.ivc_plot_panel.layout().addWidget(self.y_time_stream_label, 0, 1, 1, 1)
        self.y_data_label = QtWidgets.QLabel('Y Data: Y STD:', self)
        self.ivc_plot_panel.layout().addWidget(self.y_data_label, 1, 1, 1, 1)

        # XY
        self.xy_scatter_label = QtWidgets.QLabel('', self)
        self.xy_scatter_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.ivc_plot_panel.layout().addWidget(self.xy_scatter_label, 2, 0, 1, 2)


    #########################################################
    # Running
    #########################################################

    def ivc_start_stop(self):
        '''
        '''
        if 'Start' in self.sender().text():
            self.data_clip_lo_lineedit.setText('0')
            self.sender().setText('Stop DAQ')
            self.started = True
            self.ivc_collecter()
        else:
            self.sender().setText('Start DAQ')
            self.started = False
            save_path = self.ivc_index_file_name()
            self.ivc_save(save_path)
            self.ivc_plot_xy(file_name=save_path.replace('txt', 'png'))

    def ivc_collecter(self):
        '''
        '''
        device = self.ivc_daq_combobox.currentText()
        self.int_time = self.int_time_lineedit.text()
        self.sample_rate = self.sample_rate_lineedit.text()
        self.x_data, self.x_stds = [], []
        self.y_data, self.y_stds = [], []
        signal_channels = [self.x_channel, self.y_channel]
        daq = BoloDAQ(signal_channels=signal_channels,
                      int_time=self.int_time,
                      sample_rate=self.sample_rate,
                      device=device)
        while self.started:
            data_dict = daq.run()
            x_ts = data_dict[self.x_channel]['ts']
            x_mean = data_dict[self.x_channel]['mean']
            x_min = data_dict[self.x_channel]['min']
            x_max = data_dict[self.x_channel]['max']
            x_std = data_dict[self.x_channel]['std']
            y_ts = data_dict[self.y_channel]['ts']
            y_mean = data_dict[self.y_channel]['mean']
            y_min = data_dict[self.y_channel]['min']
            y_max = data_dict[self.y_channel]['max']
            y_std = data_dict[self.y_channel]['std']
            if x_mean < 0:
                x_mean *= -1
                x_std *= -1
                x_min *= -1
                x_max *= -1
            self.x_data.append(x_mean)
            self.x_stds.append(x_std)
            self.y_data.append(y_mean)
            self.y_stds.append(y_std)
            self.ivc_plot_running()
            self.current_x_mean = x_mean
            self.current_x_std = x_std
            self.current_y_mean = y_mean
            self.current_y_std = y_std
            self.ivc_display_current_data()
            QtWidgets.QApplication.processEvents()
            self.repaint()

    def ivc_display_current_data(self):
        '''
        '''
        x_data_label_str = 'X Mean: {0:.5f} ::: X STD: {1:.5f} (raw)\n'.format(self.current_x_mean, self.current_x_std)
        x_data_label_str += 'X Mean: {0:.5f} (uV) ::: X STD: {1:.5f} (uV)'.format(self.x_data_real[-1], self.x_stds_real[-1])
        y_data_label_str = 'Y Mean: {0:.5f} ::: Y STD: {1:.5f} (raw)\n'.format(self.current_y_mean, self.current_y_std)
        y_data_label_str += 'Y Mean: {0:.5f} (uA)::: Y STD: {1:.5f} (uA)'.format(self.y_data_real[-1], self.y_stds_real[-1])
        self.x_data_label.setText(x_data_label_str)
        self.y_data_label.setText(y_data_label_str)

    ###################################################
    # Saving and Plotting
    ###################################################

    def ivc_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            file_name = 'IV_{0}_Scan_{1}.txt'.format(self.sample_name_lineedit.text(), str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def ivc_save(self, save_path=None):
        '''
        '''
        if save_path is None or type(save_path) is bool:
            save_path = self.ivc_index_file_name()
            save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter='*.txt')[0]
        if len(save_path) > 0:
            ss_save_path = save_path.replace('.txt', '_meta.png')
            screen = QtWidgets.QApplication.primaryScreen()
            screenshot = screen.grabWindow(self.winId())
            screenshot.save(ss_save_path, 'png')
            calibrated_save_path = save_path.replace('.txt', '_calibrated.txt')
            with open(save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_data):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_data[i], self.x_stds[i], self.y_data[i], self.y_stds[i])
                    save_handle.write(line)
            with open(calibrated_save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_data_real):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_data_real[i], self.x_stds_real[i], self.y_data_real[i], self.y_stds_real[i])
                    save_handle.write(line)
            png_save_path = save_path.replace('.txt', '.png')
            shutil.copy('temp_iv_all.png', png_save_path)
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')
        self.ivc_plot_xy()

    def ivc_plot_running(self):
        '''
        '''
        self.ivc_plot_x()
        self.ivc_plot_y()
        self.ivc_plot_xy()

    def ivc_plot_x(self):
        '''
        '''
        fig, ax = self.ivc_create_blank_fig(frac_screen_width=0.4, frac_screen_height=0.3, left=0.15)
        ax.set_xlabel('Sample', fontsize=12)
        ax.set_ylabel('X ($V$)', fontsize=12)
        label = 'DAQ {0}'.format(self.x_channel)
        ax.errorbar(range(len(self.x_data)), self.x_data, self.x_stds, marker='.', linestyle='None', label=label)
        pl.legend(loc='best', fontsize=12)
        fig.savefig('temp_x.png', transparent=True)
        pl.close('all')
        image_to_display = QtGui.QPixmap('temp_x.png')
        self.x_time_stream_label.setPixmap(image_to_display)
        os.remove('temp_x.png')

    def ivc_plot_y(self):
        '''
        '''
        fig, ax = self.ivc_create_blank_fig(frac_screen_width=0.4, frac_screen_height=0.3, left=0.15)
        ax.set_xlabel('Sample', fontsize=12)
        ax.set_ylabel('Y ($V$)', fontsize=12)
        label = 'DAQ {0}'.format(self.y_channel)
        ax.errorbar(range(len(self.y_data)), self.y_data, self.y_stds, marker='.', linestyle='None', label=label)
        pl.legend(loc='best', fontsize=12)
        fig.savefig('temp_y.png', transparent=True)
        pl.close('all')
        image_to_display = QtGui.QPixmap('temp_y.png')
        self.y_time_stream_label.setPixmap(image_to_display)
        os.remove('temp_y.png')

    def ivc_plot_xy(self, file_name=''):
        '''
        '''
        if len(self.x_data) == 0:
            return None
        fig, ax = self.ivc_create_blank_fig(frac_screen_width=0.8, frac_screen_height=0.4, left=0.1, top=0.9)
        sample_name = self.sample_name_lineedit.text()
        t_bath = self.t_bath_lineedit.text()
        t_load = self.t_load_lineedit.text()
        data_clip_lo = float(self.data_clip_lo_lineedit.text())
        data_clip_hi = float(self.data_clip_hi_lineedit.text())
        fit_clip_lo = float(self.fit_clip_lo_lineedit.text())
        fit_clip_hi = float(self.fit_clip_hi_lineedit.text())
        squid_calibration_factor = float(self.squid_calibration_label.text().split(' ')[1])
        x_correction_factor = float(self.x_correction_label.text().split(' ')[1])
        i_bolo_real = self.ivc_fit_and_remove_squid_offset()
        i_bolo_std = np.asarray(self.y_stds) * squid_calibration_factor
        v_bias_real = np.asarray(self.x_data) * x_correction_factor * 1e6 #uV
        v_bias_std = np.asarray(self.x_stds) * x_correction_factor * 1e6 #uV
        #v_bias_real = np.asarray(self.x_data) * float(2e-6) * 1e6 #uV
        #v_bias_std = np.asarray(self.x_stds) * float(2e-6) * 1e6
        fit_selector = np.where(np.logical_and(fit_clip_lo < v_bias_real, v_bias_real < fit_clip_hi))
        try:
            fit_vals = np.polyfit(v_bias_real[fit_selector], i_bolo_real[fit_selector], 1)
            resistance = 1.0 / fit_vals[0]
            fit_vector = np.polyval(fit_vals, v_bias_real)
            ax.plot(v_bias_real[fit_selector], fit_vector[fit_selector], '-', lw=3, color='r', label='fit')
        except TypeError:
            resistance = np.nan
        selector =  np.where(np.logical_and(data_clip_lo < v_bias_real, v_bias_real < data_clip_hi))
        title = 'IV Curve for {0}'.format(self.sample_name_lineedit.text())
        label = 'R={0:.3f} ($\Omega$)'.format(resistance)
        self.x_data_real = v_bias_real
        self.x_stds_real = v_bias_std
        self.y_data_real = i_bolo_real
        self.y_stds_real = i_bolo_std
        #ax.errorbar(v_bias_real[selector], i_bolo_real[selector], xerr=v_bias_std[selector], yerr=i_bolo_std[selector], marker='.', linestyle='-', label=label)
        fig = self.ivlib_plot_all_curves(v_bias_real, i_bolo_real, bolo_current_stds=i_bolo_std,
                                         fit_clip=(fit_clip_lo, fit_clip_hi), plot_clip=(data_clip_lo, data_clip_hi),
                                         sample_name=sample_name, t_bath=t_bath, t_load=t_load)
        ax.set_xlabel('Bias Voltage ($\mu V$)', fontsize=14)
        ax.set_ylabel('TES Current ($\mu A$)', fontsize=14)
        ax.set_title(title, fontsize=14)
        pl.legend(loc='best', fontsize=14)
        fig.savefig('temp_iv_all.png', transparent=False)
        pl.close('all')
        image_to_display = QtGui.QPixmap('temp_iv_all.png')
        self.xy_scatter_label.setPixmap(image_to_display)

    def ivc_adjust_x_data(self):
        '''
        '''
        x_data = []
        x_stds = []
        voltage_reduction_factor = float(self.x_correction_label.text())
        x_data = np.asarray(self.x_data) * voltage_reduction_factor * 1e6 #uV
        x_stds = np.asarray(self.x_stds) * voltage_reduction_factor * 1e6 #uV
        return x_data, x_stds

    def ivc_adjust_y_data(self):
        '''
        '''
        y_data = []
        y_stds = []
        calibration_factor = float(self.squid_calibration_label.text().split(' ')[1])
        y_data = np.asarray(self.y_data) * calibration_factor
        y_stds = np.asarray(self.y_stds) * calibration_factor
        return y_data, y_stds

    def ivc_fit_and_remove_squid_offset(self, polyfit_n=1):
        '''
        '''
        calibration_factor = float(self.squid_calibration_label.text().split(' ')[1])
        y_vector = np.asarray(copy(self.y_data)) * calibration_factor# calibrated to uA from V
        scaled_x_vector = np.asarray(copy(self.x_data))
        scaled_x_vector *= float(self.x_correction_label.text().split(' ')[1])
        scaled_x_vector *= 1e6 # This is now in uV
        fit_clip_lo = float(self.fit_clip_lo_lineedit.text())
        fit_clip_hi = float(self.fit_clip_hi_lineedit.text())
        selector = np.logical_and(fit_clip_lo < scaled_x_vector, scaled_x_vector < fit_clip_hi)
        if len(scaled_x_vector[selector]) > 2:
            fit_vals = np.polyfit(scaled_x_vector[selector], y_vector[selector], polyfit_n)
            new_y_vector = y_vector - fit_vals[1]
            if fit_vals[0] < 0:
                new_y_vector = -1 * new_y_vector
        else:
            new_y_vector = np.array(y_vector)
        return new_y_vector

    def ivc_update_fit_data(self, voltage_factor):
        '''
        Updates fit limits based on IV data
        '''
        fit_clip_hi = self.xdata[0] * float(voltage_factor) * 1e6 # uV
        data_clip_lo = self.xdata[-1] * float(voltage_factor) * 1e6 + self.data_clip_offset # uV
        data_clip_hi = fit_clip_hi # uV
        fit_clip_lo = data_clip_lo + self.fit_clip_offset # uV

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
        ax.tick_params(axis='x', labelsize=10)
        ax.tick_params(axis='y', labelsize=10)
        return fig, ax
