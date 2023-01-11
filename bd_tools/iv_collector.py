import time
import shutil
import os
import simplejson
import numpy as np
import pickle as pkl
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from bd_lib.mpl_canvas import MplCanvas
from bd_lib.iv_curve_lib import IVCurveLib
from bd_lib.saving_manager import SavingManager
from bd_lib.fourier_transform_spectroscopy import FourierTransformSpectroscopy
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class IVCollector(QtWidgets.QWidget, GuiBuilder, IVCurveLib, FourierTransformSpectroscopy):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, data_folder, dewar, ls_372_widget):
        '''
        '''
        super(IVCollector, self).__init__()
        self.mplc = MplCanvas(self, screen_resolution, monitor_dpi)
        self.bands = self.ftsy_get_bands()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.ls_372_widget = ls_372_widget
        self.dewar = dewar
        with open(os.path.join('bd_settings', 'squids_settings.json'), 'r') as fh:
            self.squid_calibration_dict = simplejson.load(fh)
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)
        self.squid_gains = {
            '5': 1e-2,
            '50': 1e-1,
            '500': 1,
            }
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
        self.ivc_get_t_bath()
        self.ivc_get_t_load()

    #########################################################
    # GUI and Input Handling
    #########################################################

    def ivc_update_samples(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)

    def ivc_update_squids_data(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'squids_settings.json'), 'r') as fh:
            self.squid_calibration_dict = simplejson.load(fh)

    def ivc_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings
        self.ivc_display_daq_settings()

    def ivc_populate(self):
        '''
        '''
        self.gb_initialize_panel('self')
        self.layout().addWidget(self.ivc_plot_panel, 0, 3, 19, 1)
        self.gb_initialize_panel('ivc_plot_panel')
        self.ivc_daq_panel()
        self.ivc_iv_config()
        self.ivc_add_common_widgets()
        self.ivc_make_plot_panel()
        self.ivc_display_daq_settings()
        self.ivc_plot_running()
        self.daq_x_combobox.setCurrentIndex(0)
        self.daq_y_combobox.setCurrentIndex(1)
        self.squid_select_combobox.currentIndexChanged.connect(self.ivc_update_squid_calibration)
        self.squid_select_combobox.setCurrentIndex(1)
        self.squid_select_combobox.setCurrentIndex(0)

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
        self.layout().addWidget(self.daq_x_combobox, 0, 1, 1, 1)
        # DAQ Y
        self.daq_y_combobox = self.gb_make_labeled_combobox(label_text='DAQ Y Data:')
        for daq in range(0, 8):
            self.daq_y_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_y_combobox, 0, 2, 1, 1)
        self.daq_y_combobox.setCurrentIndex(1)
        self.daq_y_combobox.currentIndexChanged.connect(self.ivc_display_daq_settings)
        self.daq_x_combobox.currentIndexChanged.connect(self.ivc_display_daq_settings)
        self.ivc_daq_combobox.currentIndexChanged.connect(self.ivc_display_daq_settings)
        if self.dewar == '576':
            self.ivc_daq_combobox.setCurrentIndex(0)
        else:
            self.ivc_daq_combobox.setCurrentIndex(1)
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Int Time')
        self.int_time_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.int_time_lineedit))
        self.layout().addWidget(self.int_time_lineedit, 1, 1, 1, 1)
        self.int_time_lineedit.setText('100')
        self.int_time = self.int_time_lineedit.text()
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Rate (Hz)')
        self.sample_rate_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.sample_rate_lineedit))
        self.layout().addWidget(self.sample_rate_lineedit, 1, 2, 1, 1)
        self.sample_rate_lineedit.setText('5000')
        self.sample_rate = self.sample_rate_lineedit.text()

    def ivc_calc_x_correction(self):
        '''
        '''
        if len(self.warm_bias_resistor_lineedit.text()) == 0:
            return None
        if int(self.warm_bias_resistor_lineedit.text()) == 0:
            return None
        warm_bias_r = float(self.warm_bias_resistor_lineedit.text())
        cold_bias_r = float(self.cold_bias_resistor_combobox.currentText())
        x_correction_factor = cold_bias_r / warm_bias_r
        self.x_correction_label.setText('X_CORRECTION {0:.8f}'.format(x_correction_factor))

    def ivc_iv_config(self):
        '''
        '''
        # X Voltage Factor
        self.x_correction_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.x_correction_label, 3, 2, 1, 1)
        self.cold_bias_resistor_combobox = self.gb_make_labeled_combobox(label_text='Cold Bias Resistor:')
        for index, cold_bias_resistance in self.cold_bias_resistor_dict.items():
            self.cold_bias_resistor_combobox.addItem('{0}'.format(cold_bias_resistance))
        self.cold_bias_resistor_combobox.activated.connect(self.ivc_calc_x_correction)
        self.cold_bias_resistor_combobox.setCurrentIndex(0)
        self.layout().addWidget(self.cold_bias_resistor_combobox, 3, 0, 1, 1)
        self.warm_bias_resistor_lineedit = self.gb_make_labeled_lineedit(label_text='Warm Bias Resistor:')
        self.warm_bias_resistor_lineedit.textChanged.connect(self.ivc_calc_x_correction)
        self.warm_bias_resistor_lineedit.setText('2000')
        self.warm_bias_resistor_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e12, 2, self.warm_bias_resistor_lineedit))
        self.warm_bias_resistor_lineedit.returnPressed.connect(self.ivc_plot_running)
        self.layout().addWidget(self.warm_bias_resistor_lineedit, 3, 1, 1, 1)
        # SQUID
        self.squid_calibration_lineedit = self.gb_make_labeled_lineedit(label_text='Squid Conv (uA/V)')
        self.squid_calibration_lineedit.returnPressed.connect(self.ivc_plot_running)
        self.layout().addWidget(self.squid_calibration_lineedit, 4, 2, 1, 1)
        self.squid_select_combobox = self.gb_make_labeled_combobox(label_text='Select SQUID')
        for squid, calibration in self.squid_calibration_dict.items():
            self.squid_select_combobox.addItem('{0}'.format(squid))
        self.layout().addWidget(self.squid_select_combobox, 4, 0, 1, 1)
        self.squid_gain_select_combobox = self.gb_make_labeled_combobox(label_text='SQUID Gain')
        for gain in self.squid_gains:
            self.squid_gain_select_combobox.addItem(gain)
        self.layout().addWidget(self.squid_gain_select_combobox, 4, 1, 1, 1)
        self.squid_gain_select_combobox.setCurrentIndex(2)
        self.squid_gain_select_combobox.currentIndexChanged.connect(self.ivc_update_squid_calibration)
        # Temperature 
        if self.dewar == '576':
            self.t_bath_lineedit = self.gb_make_labeled_lineedit(label_text='T_bath (mK)')
            self.t_load_lineedit = self.gb_make_labeled_lineedit(label_text='T_load (K)')
            self.t_bath_lineedit.returnPressed.connect(self.ivc_plot_running)
            self.t_bath_lineedit.setValidator(QtGui.QDoubleValidator(0, 10000, 8, self.t_bath_lineedit))
            self.t_load_lineedit.returnPressed.connect(self.ivc_plot_running)
            self.t_load_lineedit.setValidator(QtGui.QDoubleValidator(0, 500, 8, self.t_load_lineedit))
        elif self.dewar == 'BlueForsDR1':
            self.t_bath_lineedit = self.gb_make_labeled_label(label_text='T_bath (mK)')
            self.t_load_lineedit = self.gb_make_labeled_label(label_text='T_load (K)')
        self.t_bath_lineedit.setText('275')
        self.layout().addWidget(self.t_bath_lineedit, 8, 0, 1, 1)
        self.t_load_lineedit.setText('300')
        self.layout().addWidget(self.t_load_lineedit, 8, 1, 1, 1)
        self.absorber_type_lineedit = self.gb_make_labeled_lineedit(label_text='Absorber Type:')
        self.layout().addWidget(self.absorber_type_lineedit, 8, 2, 1, 1)

        self.t_bath_set_lineedit = self.gb_make_labeled_lineedit(label_text='T_bath set (mK)', lineedit_text='100')
        self.t_bath_set_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.t_bath_set_lineedit))
        self.layout().addWidget(self.t_bath_set_lineedit, 9, 0, 1, 1)
        self.t_load_set_lineedit = self.gb_make_labeled_lineedit(label_text='T_load set, (K)', lineedit_text='10')
        self.t_load_set_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.t_load_set_lineedit))
        self.layout().addWidget(self.t_load_set_lineedit, 9, 1, 1, 1)
        self.t_bath_set_pushbutton = QtWidgets.QPushButton(text='Set T_bath')
        self.t_bath_set_pushbutton.clicked.connect(self.ivc_set_t_bath)
        self.t_bath_set_lineedit.returnPressed.connect(self.ivc_set_t_bath)
        self.layout().addWidget(self.t_bath_set_pushbutton, 10, 0, 1, 1)
        self.t_load_set_pushbutton = QtWidgets.QPushButton(text='Set T_load')
        self.t_load_set_lineedit.returnPressed.connect(self.ivc_set_t_load)
        self.t_load_set_pushbutton.clicked.connect(self.ivc_set_t_load)
        self.layout().addWidget(self.t_load_set_pushbutton, 10, 1, 1, 1)

        # Band information
        self.sample_band_combobox = self.gb_make_labeled_combobox(label_text='Sample Band (GHz)')
        self.layout().addWidget(self.sample_band_combobox, 11, 1, 1, 1)
        for sample_band in self.bands:
            self.sample_band_combobox.addItem(sample_band)

    def ivc_add_common_widgets(self):
        '''
        '''
        # Sample Name
        self.sample_name_combobox = self.gb_make_labeled_combobox(label_text='Select Sample')
        for sample in self.samples_settings:
            self.sample_name_combobox.addItem(sample)
        self.sample_name_combobox.currentIndexChanged.connect(self.ivc_update_sample_name)
        self.layout().addWidget(self.sample_name_combobox, 1, 0, 1, 1)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name')
        self.layout().addWidget(self.sample_name_lineedit, 11, 0, 1, 1)
        self.notes_lineedit = self.gb_make_labeled_lineedit(label_text='Notes:')
        self.layout().addWidget(self.notes_lineedit, 11, 2, 1, 1)
        # Buttons
        self.start_pushbutton = QtWidgets.QPushButton('Start', self)
        self.start_pushbutton.clicked.connect(self.ivc_start_stop)
        self.layout().addWidget(self.start_pushbutton, 13, 0, 1, 3)
        self.load_pushbutton = QtWidgets.QPushButton('Load', self)
        self.load_pushbutton.clicked.connect(self.ivc_load)
        self.layout().addWidget(self.load_pushbutton, 14, 0, 1, 3)
        self.save_pushbutton = QtWidgets.QPushButton('Save', self)
        self.save_pushbutton.clicked.connect(self.ivc_save)
        self.layout().addWidget(self.save_pushbutton, 15, 0, 1, 3)

    def ivc_update_sample_name(self, index):
        '''
        '''
        sample_key = self.sample_name_combobox.currentText()
        if len(sample_key) == 0:
            return None
        #import ipdb;ipdb.set_trace()
        sample_name = self.samples_settings[sample_key]
        squid = sample_key.split('-')[1]
        self.sample_name_lineedit.setText(sample_name)
        for index in range(self.squid_select_combobox.count()):
            if squid in self.squid_select_combobox.itemText(index):
                self.squid_select_combobox.setCurrentIndex(index)
                break

    def ivc_update_squid_calibration(self, index):
        '''
        '''
        self.ivc_update_squids_data()
        gain = self.squid_gains[self.squid_gain_select_combobox.currentText()]
        squid_key = self.squid_select_combobox.currentText()
        calibration_value = float(self.squid_calibration_dict[squid_key].split(' ')[0]) * gain
        self.squid_calibration_lineedit.setText('{0:.2f}'.format(calibration_value))
        squid = squid_key.split('-')[1]
        for index in range(self.sample_name_combobox.count()):
            if squid in self.sample_name_combobox.itemText(index):
                self.sample_name_combobox.setCurrentIndex(index)
                break


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

        # Data Clip
        self.data_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Lo (uV)', lineedit_text='0.0')
        self.data_clip_lo_lineedit.returnPressed.connect(self.ivc_plot_running)
        self.data_clip_lo_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.data_clip_lo_lineedit))
        self.ivc_plot_panel.layout().addWidget(self.data_clip_lo_lineedit, 6, 0, 1, 1)
        self.data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Hi (uV)', lineedit_text='10.0')
        self.data_clip_hi_lineedit.returnPressed.connect(self.ivc_plot_running)
        self.data_clip_hi_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.data_clip_hi_lineedit))
        self.ivc_plot_panel.layout().addWidget(self.data_clip_hi_lineedit, 6, 1, 1, 1)
        # Fit Clip
        self.fit_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Fit Clip Lo (uV)', lineedit_text='1.0')
        self.fit_clip_lo_lineedit.returnPressed.connect(self.ivc_plot_running)
        self.ivc_plot_panel.layout().addWidget(self.fit_clip_lo_lineedit, 7, 0, 1, 1)
        self.fit_clip_lo_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.fit_clip_lo_lineedit))
        self.fit_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Fit Clip Hi (uV)', lineedit_text='4.0')
        self.fit_clip_hi_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.fit_clip_hi_lineedit))
        self.fit_clip_hi_lineedit.returnPressed.connect(self.ivc_plot_running)
        self.ivc_plot_panel.layout().addWidget(self.fit_clip_hi_lineedit, 7, 1, 1, 1)

    #########################################################
    # Temperature regulation
    #########################################################

    def ivc_get_t_bath(self):
        '''
        '''
        channel_readout_info = self.ls_372_widget.channels.ls372_get_channel_value(6, reading='kelvin') # 6 is MXC
        temperature = '{0:.3f}'.format(float(channel_readout_info) * 1e3) # mK
        self.t_bath_lineedit.setText(temperature)

    def ivc_set_t_bath(self):
        '''
        '''
        temp = float(self.t_bath_set_lineedit.text())
        self.status_bar.showMessage('Setting T_bath to {0:.2f}'.format(temp))


    def ivc_get_t_load(self):
        '''
        '''
        channel_readout_info = self.ls_372_widget.channels.ls372_get_channel_value(5, reading='kelvin') # 5 is 50K
        temperature = '{0:.3f}'.format(float(channel_readout_info) * 1e3) # mK
        self.t_load_lineedit.setText(temperature)

    def ivc_set_t_load(self):
        '''
        '''
        temp = float(self.t_load_set_lineedit.text())
        self.ls_372_widget.temp_control.ls372_set_temp_set_point(temp)
        self.status_bar.showMessage('Setting T_load to {0:.2f}'.format(temp))

    def ivc_update_ls_372_widget(self, ls_372_widget):
        '''
        '''
        self.ls_372_widget = ls_372_widget

    def ivc_set_temperature(self):
        '''
        '''
        temperature = float(self.t_load_lineedit.text()) * 1e-3 #K
        self.ls372_widget.temp_control.ls372_set_ramp(0.1, use_ramp=0)
        self.ls372_widget.temp_control.ls372_set_temp_set_point(temperature)

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
        absorber = self.absorber_type_lineedit.text()
        t_bath = self.t_bath_lineedit.text()
        t_load = self.t_load_lineedit.text()
        for i in range(1, 1000):
            file_name = 'IV_{0}_tb_{1}mK_Tl_{2}K_{3}_{4}.txt'.format(self.sample_name_lineedit.text(), t_bath, t_load, absorber, str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def ivc_load(self):
        '''
        '''
        save_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select IF data', '.if')[0]
        self.meta_dict = self.gb_load_meta_data(save_path, 'txt')
        self.x_data, self.x_stds, self.y_data, self.y_stds = [], [], [], []
        if len(save_path) == 0:
            return None
        with open(save_path, 'r') as fh:
            lines = fh.readlines()
            for line in lines:
                line = line.replace('\t', ', ')
                x_data = float(line.split(', ')[0].strip())
                x_std = float(line.split(', ')[1].strip())
                y_data = float(line.split(', ')[2].strip())
                y_std = float(line.split(', ')[3].strip())
                self.x_data.append(x_data)
                self.x_stds.append(x_std)
                self.y_data.append(y_data)
                self.y_stds.append(y_std)
        self.ivc_plot_xy()

    def ivc_save(self, save_path=None):
        '''
        '''
        if save_path is None or type(save_path) is bool:
            save_path = self.ivc_index_file_name()
            save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter='*.txt')[0]
        if len(save_path) > 0:
            self.gb_save_meta_data(save_path, 'txt')
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
        fig, ax = self.mplc.mplc_create_basic_fig(
            name='x_fig',
            left=0.18,
            right=0.95,
            bottom=0.25,
            top=0.88,
            frac_screen_height=0.15,
            frac_screen_width=0.3)
        ax.set_xlabel('Sample', fontsize=14)
        ax.set_ylabel('X ($V$)', fontsize=14)
        label = 'DAQ {0}'.format(self.x_channel)
        if len(self.x_data) > 1:
            label = None
        ax.errorbar(range(len(self.x_data)), self.x_data, self.x_stds, marker='.', linestyle='None', label=label)
        if len(self.x_data) > 0:
            ax.legend(loc='best', fontsize=14)
        fig.savefig('temp_x.png', transparent=True)
        image_to_display = QtGui.QPixmap('temp_x.png')
        self.x_time_stream_label.setPixmap(image_to_display)
        os.remove('temp_x.png')

    def ivc_plot_y(self):
        '''
        '''
        fig, ax = self.mplc.mplc_create_basic_fig(
            name='x_fig',
            left=0.18,
            right=0.95,
            bottom=0.25,
            top=0.88,
            frac_screen_height=0.15,
            frac_screen_width=0.3)
        ax.set_xlabel('Sample', fontsize=14)
        ax.set_ylabel('Y ($V$)', fontsize=14)
        label = 'DAQ {0}'.format(self.y_channel)
        if len(self.x_data) > 1:
            label = None
        ax.errorbar(range(len(self.y_data)), self.y_data, self.y_stds, marker='.', linestyle='None', label=label)
        ax.legend(loc='best', fontsize=12)
        fig.savefig('temp_y.png', transparent=True)
        image_to_display = QtGui.QPixmap('temp_y.png')
        self.y_time_stream_label.setPixmap(image_to_display)
        os.remove('temp_y.png')

    def ivc_plot_xy(self, file_name=''):
        '''
        '''
        #####################################
        # Screen for bad input
        #####################################
        if len(self.x_data) == 0:
            return None
        if not self.gb_is_float(self.data_clip_lo_lineedit.text()):
            return None
        if not self.gb_is_float(self.data_clip_hi_lineedit.text()):
            return None
        if not self.gb_is_float(self.fit_clip_lo_lineedit.text()):
            return None
        if not self.gb_is_float(self.fit_clip_hi_lineedit.text()):
            return None

        #####################################
        # Plot creation labeling Plotting
        #####################################
        fig = self.mplc.mplc_create_iv_paneled_plot(
            name='xy_fig',
            left=0.1,
            right=0.95,
            bottom=0.25,
            top=0.8,
            frac_screen_height=0.4,
            frac_screen_width=0.4,
            hspace=0.99,
            wspace=0.25)

        ax1, ax2, ax3, ax4 = fig.get_axes()

        ax1.set_xlabel("Voltage ($\mu$V)", fontsize=14)
        ax1.set_ylabel("Current ($\mu$A)", fontsize=14)
        ax3.set_xlabel("Voltage ($\mu$V)", fontsize=14)
        ax3.set_ylabel("Res ($\Omega$)", fontsize=14)
        ax4.set_xlabel("Res ($\Omega$)", fontsize=14)
        ax4.set_ylabel("Power ($pW$)", fontsize=14)

        # Set the titles
        sample_name = self.sample_name_lineedit.text()
        ax1.set_title('IV of {0}'.format(sample_name), fontsize=14)
        ax3.set_title('RV of {0}'.format(sample_name), fontsize=14)
        ax4.set_title('PR of {0}'.format(sample_name), fontsize=14)
        t_bath = self.t_bath_lineedit.text()
        t_load = self.t_load_lineedit.text()
        title = '{0}\n@{1}mK with {2}K Load'.format(sample_name, t_bath, t_load)
        title = '{0}'.format(sample_name)
        ax1.set_title(title, fontsize=14)

        #####################################
        # Data Plotting
        #####################################

        data_clip_lo = float(self.data_clip_lo_lineedit.text())
        data_clip_hi = float(self.data_clip_hi_lineedit.text())
        fit_clip_lo = float(self.fit_clip_lo_lineedit.text())
        fit_clip_hi = float(self.fit_clip_hi_lineedit.text())

        v_bolo_real, v_bolo_stds = self.ivc_adjust_x_data()
        i_bolo_real, i_bolo_stds, fit_vals = self.ivc_adjust_y_data()



        resistance = 1.0 / fit_vals[0] # in Ohms

        p_bolo = v_bolo_real * i_bolo_real
        r_bolo = v_bolo_real / i_bolo_real

        x_fit_vector = np.arange(fit_clip_lo, fit_clip_hi, 0.005)
        y_fit_vector = np.polyval(fit_vals, x_fit_vector) - fit_vals[1]
        if fit_vals[0] < 0:
            y_fit_vector *= -1
        fit_selector = np.where(np.logical_and(fit_clip_lo < x_fit_vector, x_fit_vector < fit_clip_hi))

        plot_selector =  np.where(np.logical_and(data_clip_lo < v_bolo_real, v_bolo_real < data_clip_hi))

        label = 'R={0:.3f} ($\Omega$)'.format(resistance)
        if len(self.x_data) > 1:
            label = None

        ax1.plot(x_fit_vector[fit_selector], y_fit_vector[fit_selector], '-', lw=3, color='r', label='fit')
        ax1.plot(v_bolo_real[plot_selector], i_bolo_real[plot_selector], '.', label=label)
        if len(i_bolo_stds) > 0:
            ax1.errorbar(v_bolo_real[plot_selector], i_bolo_real[plot_selector], yerr=i_bolo_stds[plot_selector],
                         label='error', marker='.', linestyle='None', alpha=0.25)
        if len(v_bolo_real) > 2 and len(i_bolo_real[plot_selector]) > 0:
            pt_idx = np.where(i_bolo_real[plot_selector] == min(i_bolo_real[plot_selector]))[0][0]
            pl_idx = np.where(v_bolo_real[plot_selector] == min(v_bolo_real[plot_selector]))[0][0]
            pturn_pw = i_bolo_real[plot_selector][pt_idx] * v_bolo_real[plot_selector][pt_idx]
            plast_pw = i_bolo_real[plot_selector][pl_idx] * v_bolo_real[plot_selector][pl_idx]
            v_0 = v_bolo_real[plot_selector][pt_idx]
            v_1 = v_bolo_real[plot_selector][pt_idx - 1]
            i_0 = i_bolo_real[plot_selector][pt_idx]
            i_1 = i_bolo_real[plot_selector][pt_idx - 1]
            r_0 = v_0 / i_0
            r_1 = v_1 / i_1
            print(v_0, v_1, i_0, i_1, r_1, r_0)
            squid_inductance = 1e-9 #H
            warm_bias_resistance = 20e3 #Ohms
            derivative = (r_1 - r_0) / (i_1 - i_0)
            beta = (i_0 / r_0 ) * derivative
            beta_2 = -1 * (i_0 / r_0) * (v_0 / i_0 ** 2)
            print('beta', beta)
            print('beta_2', beta_2)
            t_el = squid_inductance / (warm_bias_resistance + r_0 * (1 + beta_2))
            print('t_el', t_el)
            loopgain = 1
            responsivity = -1 * (1 / v_0) * (squid_inductance / (t_el * r_0 * loopgain)) ** -1
            print('S_i', responsivity)
            ax1.plot(
                v_bolo_real[plot_selector][pt_idx],
                i_bolo_real[plot_selector][pt_idx],
                '*', markersize=10.0, color='g',
                label='Pturn = {0:.2f} pW $S_i$={1:.2f}e-6'.format(pturn_pw, responsivity * 1e6))
            ax1.plot(
                v_bolo_real[plot_selector][pl_idx],
                i_bolo_real[plot_selector][pl_idx],
                '*', markersize=10.0, color='m',
                label='Plast = {0:.2f} pW'.format(plast_pw))
        ax3.plot(v_bolo_real[plot_selector], r_bolo[plot_selector], 'b', label='Res {0:.2f} ($\Omega$)'.format(1.0 / fit_vals[0]))
        ax4.plot(r_bolo[plot_selector], p_bolo[plot_selector], 'r', label='Power (pW)')
        # Grab all the labels and combine them 
        handles, labels = ax1.get_legend_handles_labels()
        handles += ax3.get_legend_handles_labels()[0]
        labels += ax3.get_legend_handles_labels()[1]
        handles += ax4.get_legend_handles_labels()[0]
        labels += ax4.get_legend_handles_labels()[1]
        ax2.legend(handles, labels, numpoints=1, mode="expand", frameon=True, fontsize=10, bbox_to_anchor=(0, 0.1, 1, 1))
        #####################################
        # For Saving
        #####################################
        self.x_data_real = v_bolo_real
        self.x_stds_real = v_bolo_stds
        self.y_data_real = i_bolo_real
        self.y_stds_real = i_bolo_stds
        fig.savefig('temp_iv_all.png', transparent=False)
        image_to_display = QtGui.QPixmap('temp_iv_all.png')
        self.xy_scatter_label.setPixmap(image_to_display)

    def ivc_adjust_x_data(self):
        '''
        '''
        voltage_reduction_factor = (self.x_correction_label.text().split(' ')[1])
        if not self.gb_is_float(voltage_reduction_factor):
            return None
        voltage_reduction_factor = float(voltage_reduction_factor)
        v_bolo_real = np.asarray(self.x_data) * voltage_reduction_factor * 1e6 #uV
        v_bolo_stds = np.asarray(self.x_stds) * voltage_reduction_factor * 1e6 #uV
        return v_bolo_real, v_bolo_stds

    def ivc_adjust_y_data(self):
        '''
        '''
        i_bolo_real, i_bolo_stds, resistance = self.ivc_fit_and_remove_squid_offset()
        return i_bolo_real, i_bolo_stds, np.abs(resistance)

    def ivc_fit_and_remove_squid_offset(self, polyfit_n=1):
        '''
        '''
        if not self.gb_is_float(self.squid_calibration_lineedit.text()):
            return None
        squid_calibration_factor = float(self.squid_calibration_lineedit.text())
        i_bolo_stds = np.asarray(self.y_stds) * squid_calibration_factor
        scaled_y_vector = np.asarray(copy(self.y_data)) * squid_calibration_factor # in uA from V 
        scaled_x_vector = np.asarray(copy(self.x_data))
        scaled_x_vector *= float(self.x_correction_label.text().split(' ')[1])
        scaled_x_vector *= 1e6 # This is now in uV for the fit selector to make sense to user
        fit_clip_lo = float(self.fit_clip_lo_lineedit.text())
        fit_clip_hi = float(self.fit_clip_hi_lineedit.text())
        selector = np.logical_and(fit_clip_lo < scaled_x_vector, scaled_x_vector < fit_clip_hi)
        if len(scaled_x_vector[selector]) > 2:
            try:
                fit_vals = np.polyfit(scaled_x_vector[selector], scaled_y_vector[selector], polyfit_n)
                resistance, offset = 1.0 / fit_vals[0], fit_vals[1]
                i_bolo_real = scaled_y_vector - offset
                if fit_vals[0] < 0:
                    # invert the line if it's trend up toward zero due to polarity of squid readout
                    i_bolo_real = -1 * i_bolo_real
            except TypeError:
                fit_vals = (np.nan, np.nan)
                i_bolo_real = np.array(scaled_y_vector)
        else:
            i_bolo_real = np.array(scaled_y_vector)
            fit_vals = (np.nan, np.nan)
        return i_bolo_real, i_bolo_stds, fit_vals

    def ivc_plot_all_curves(self, fig, bolo_voltage_bias, bolo_current, bolo_current_stds=None, fit_clip=None, plot_clip=None,
                              label='', sample_name='', t_bath='275', t_load='300', pturn=True,
                              left=0.1, right=0.98, top=0.9, bottom=0.13, hspace=0.8,
                              show_plot=False):
        '''
        This function creates an x-y scatter plot with v_bolo on the x-axis and
        bolo curent on the y-axis.  The resistance value is reported as text annotation
        Inputs:
            bolo_votlage_bias: bolo_voltage in Volts
            bolo_current: bolo_current in Amps
        '''
        ax2.set_axis_off()
        fit_selector = np.logical_and(fit_clip[0] < bolo_voltage_bias, bolo_voltage_bias < fit_clip[1])
        plot_selector = np.logical_and(plot_clip[0] < bolo_voltage_bias, bolo_voltage_bias < plot_clip[1])
        add_fit = False
        fit_vals = (1, 1)
        if len(bolo_voltage_bias[fit_selector]) > 2:
            fit_vals = np.polyfit(bolo_voltage_bias[fit_selector], bolo_current[fit_selector], 1)
            v_fit_x_vector = np.arange(fit_clip[0], fit_clip[1], 0.02)
            selector_2 = np.logical_and(fit_clip[0] < v_fit_x_vector, v_fit_x_vector < fit_clip[1])
            poly_fit = np.polyval(fit_vals, v_fit_x_vector[selector_2]) + fit_vals[0]
            add_fit = True
        resistance_vector = bolo_voltage_bias / bolo_current
        power_vector = bolo_voltage_bias * bolo_current
        ax1.plot(bolo_voltage_bias[plot_selector], bolo_current[plot_selector], '.', label=label)
        if bolo_current_stds is not None:
            ax1.errorbar(bolo_voltage_bias[plot_selector], bolo_current[plot_selector], yerr=bolo_current_stds[plot_selector],
                         label='error', marker='.', linestyle='None', alpha=0.25)
        if pturn and len(bolo_voltage_bias) > 2 and len(bolo_current[plot_selector]) > 0:
            print(len(bolo_current[plot_selector]))
            print(len(bolo_current))
            pt_idx = np.where(bolo_current[plot_selector] == min(bolo_current[plot_selector]))[0][0]
            pl_idx = np.where(bolo_voltage_bias[plot_selector] == min(bolo_voltage_bias[plot_selector]))[0][0]
            pturn_pw = bolo_current[plot_selector][pt_idx] * bolo_voltage_bias[plot_selector][pt_idx]
            plast_pw = bolo_current[plot_selector][pl_idx] * bolo_voltage_bias[plot_selector][pl_idx]
            ax1.plot(bolo_voltage_bias[plot_selector][pt_idx], bolo_current[plot_selector][pt_idx],
                     '*', markersize=10.0, color='g', label='Pturn = {0:.2f} pW'.format(pturn_pw))
            ax1.plot(bolo_voltage_bias[plot_selector][pl_idx], bolo_current[plot_selector][pl_idx],
                     '*', markersize=10.0, color='m', label='Plast = {0:.2f} pW'.format(plast_pw))
        ax3.plot(bolo_voltage_bias[plot_selector], resistance_vector[plot_selector], 'b', label='Res {0:.4f} ($\Omega$)'.format(1.0 / fit_vals[0]))
        #ax4.plot(bolo_voltage_bias[power_selector], power_vector[power_selector], resitance_vector[plot_selector], 'r', label='Power (pW)')
        power_selector = np.logical_and(0 < power_vector, power_vector < 0.25 * np.max(power_vector))
        ax4.plot(resistance_vector[plot_selector], power_vector[plot_selector], 'r', label='Power (pW)')
        if add_fit:
            ax1.plot(v_fit_x_vector[selector_2], poly_fit, label='Fit: {0:.5f}$\Omega$'.format(1.0 / fit_vals[0]))
        # Label the axis
        ax1.set_xlabel("Voltage ($\mu$V)", fontsize=16)
        ax1.set_ylabel("Current ($\mu$A)", fontsize=16)
        ax3.set_xlabel("Voltage ($\mu$V)", fontsize=16)
        ax3.set_ylabel("Res ($\Omega$)", fontsize=16)
        ax4.set_xlabel("Res ($\Omega$)", fontsize=16)
        ax4.set_ylabel("Power ($pW$)", fontsize=16)
        # Set the titles
        ax1.set_title('IV of {0}'.format(title))
        ax3.set_title('RV of {0}'.format(title))
        ax4.set_title('PR of {0}'.format(title))
        # Grab all the labels and combine them 
        handles, labels = ax1.get_legend_handles_labels()
        handles += ax3.get_legend_handles_labels()[0]
        labels += ax3.get_legend_handles_labels()[1]
        handles += ax4.get_legend_handles_labels()[0]
        labels += ax4.get_legend_handles_labels()[1]
        ax2.legend(handles, labels, numpoints=1, mode="expand", bbox_to_anchor=(0, 0.1, 1, 1))
        xlim_range = max(plot_clip) - min(plot_clip)
        ax1.set_xlim((plot_clip[0] - 0.1 * xlim_range, plot_clip[1] + 0.1 * xlim_range))
        ax3.set_xlim((plot_clip[0] - 0.1 * xlim_range, plot_clip[1] + 0.1 * xlim_range))
        return fig



