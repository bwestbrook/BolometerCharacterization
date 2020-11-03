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
        self.le_width = int(0.05 * self.screen_resolution.width())
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
        self.ivc = IVCurves()
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
        self.saving_manager = SavingManager(self, self.data_folder, self.ivc_save, 'IV')
        self.ivc_populate()
        self.ivc_plot_running()
        self.ivc = IVCurves()

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
        self.ivc_make_plot_panel()
        self.ivc_add_common_widgets()
        self.ivc_display_daq_settings()
        self.ivc_plot_running()

    def ivc_display_daq_settings(self):
        '''
        '''
        daq = self.ivc_daq_combobox.currentText()
        self.x_channel = self.daq_x_combobox.currentIndex()
        self.y_channel = self.daq_y_combobox.currentIndex()
        # X
        self.int_time_x = self.daq_settings[daq][str(self.x_channel)]['int_time']
        self.sample_rate_x = self.daq_settings[daq][str(self.x_channel)]['sample_rate']
        daq_settings_x_info = '\nDAQ X: Int Time (ms): {0} ::: '.format(self.int_time_x)
        daq_settings_x_info += 'Sample Rate (Hz): {0}'.format(str(self.sample_rate_x))
        self.daq_settings_x_label.setText(daq_settings_x_info)
        # Y
        self.int_time_y = self.daq_settings[daq][str(self.y_channel)]['int_time']
        self.sample_rate_y = self.daq_settings[daq][str(self.y_channel)]['sample_rate']
        daq_settings_y_info = '\nDAQ Y: Int Time (ms): {0} ::: '.format(self.int_time_y)
        daq_settings_y_info += 'Sample Rate (Hz): {0}'.format(str(self.sample_rate_y))
        self.daq_settings_y_label.setText(daq_settings_y_info)

    def ivc_daq_panel(self):
        '''
        '''
        # Device
        self.ivc_daq_combobox = self.gb_make_labeled_combobox(label_text='DAQ Device', width=self.le_width)
        for daq in self.daq_settings:
            self.ivc_daq_combobox.addItem(daq)
        self.layout().addWidget(self.ivc_daq_combobox, 0, 0, 1, 1)
        # DAQ X
        self.daq_x_combobox = self.gb_make_labeled_combobox(label_text='DAQ X Data:', width=self.le_width)
        for daq in range(0, 8):
            self.daq_x_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_x_combobox, 1, 0, 1, 1)
        self.daq_settings_x_label = QtWidgets.QLabel('', self)
        self.daq_settings_x_label.setAlignment(QtCore.Qt.AlignLeft)
        self.layout().addWidget(self.daq_settings_x_label, 2, 0, 1, 1)
        # DAQ Y
        self.daq_y_combobox = self.gb_make_labeled_combobox(label_text='DAQ Y Data:', width=self.le_width)
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

    def ivc_iv_config(self):
        '''
        '''
        # X Voltage Factor
        self.x_correction_combobox = self.gb_make_labeled_combobox(label_text='Bias Voltage Correction Factor:', width=self.le_width)
        for index, voltage_factor in self.voltage_reduction_factor_dict.items():
            self.x_correction_combobox.addItem('{0}'.format(voltage_factor))
        self.layout().addWidget(self.x_correction_combobox, 6, 0, 1, 1)
        # SQUID
        self.squid_calibration_label = QtWidgets.QLabel('', self)
        self.squid_calibration_label.setAlignment(QtCore.Qt.AlignRight)
        self.layout().addWidget(self.squid_calibration_label, 7, 0, 1, 1)
        self.y_correction_combobox = self.gb_make_labeled_combobox(label_text='Select SQUID')
        for squid, calibration in self.squid_calibration_dict.items():
            self.y_correction_combobox.addItem('{0}'.format(squid))
        self.y_correction_combobox.setCurrentIndex(-1)
        self.y_correction_combobox.currentIndexChanged.connect(self.ivc_update_squid_calibration)
        self.y_correction_combobox.setCurrentIndex(0)
        self.layout().addWidget(self.y_correction_combobox, 8, 0, 1, 1)
        # Data Clip
        self.data_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Lo (uV)', lineedit_text='0.0', width=self.le_width)
        self.layout().addWidget(self.data_clip_lo_lineedit, 9, 0, 1, 1)
        self.data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Hi (uV)', lineedit_text='100.0', width=self.le_width)
        self.layout().addWidget(self.data_clip_hi_lineedit, 10, 0, 1, 1)
        # Fit Clip
        self.data_fit_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Fit Clip Lo (uV)', lineedit_text='0.0', width=self.le_width)
        self.layout().addWidget(self.data_fit_lo_lineedit, 11, 0, 1, 1)
        self.data_fit_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Fit Clip Hi (uV)', lineedit_text='100.0', width=self.le_width)
        self.layout().addWidget(self.data_fit_hi_lineedit, 12, 0, 1, 1)
        # Extra information
        self.sample_temp_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Temp (K)', width=self.le_width)
        self.sample_temp_lineedit.setValidator(QtGui.QDoubleValidator(0, 10000, 8, self.sample_temp_lineedit))
        self.layout().addWidget(self.sample_temp_lineedit, 13, 0, 1, 1)
        self.optical_load_lineedit = self.gb_make_labeled_lineedit(label_text='Optical Load (K)', width=self.le_width)
        self.optical_load_lineedit.setValidator(QtGui.QDoubleValidator(0, 500, 8, self.optical_load_lineedit))
        self.layout().addWidget(self.optical_load_lineedit, 14, 0, 1, 1)
        self.sample_band_combobox = self.gb_make_labeled_combobox(label_text='Sample Band (GHz)', width=self.le_width)
        self.layout().addWidget(self.sample_band_combobox, 15, 0, 1, 1)
        for sample_band in ['', 'MF-Sinuous1p5', 'MF-Sinuous0p8', '30', '40', '90', '150', '220', '270']:
            self.sample_band_combobox.addItem(sample_band)

    def ivc_add_common_widgets(self):
        '''
        '''
        # Sample Name
        self.sample_name_combobox = self.gb_make_labeled_combobox(label_text='Select Sample', width=self.le_width)
        for sample in self.samples_settings:
            self.sample_name_combobox.addItem(sample)
        self.sample_name_combobox.currentIndexChanged.connect(self.ivc_update_sample_name)
        self.layout().addWidget(self.sample_name_combobox, 16, 0, 1, 1)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name')
        self.layout().addWidget(self.sample_name_lineedit, 17, 0, 1, 1)
        # Buttons
        start_pushbutton = QtWidgets.QPushButton('Start', self)
        start_pushbutton.clicked.connect(self.ivc_start_stop)
        self.layout().addWidget(start_pushbutton, 18, 0, 1, 1)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        save_pushbutton.clicked.connect(self.ivc_save)
        self.layout().addWidget(save_pushbutton, 19, 0, 1, 1)
        self.ivc_update_sample_name(0)

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
        self.squid_calibration_label.setText(calibration_value)

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
        self.x_data, self.x_stds = [], []
        self.y_data, self.y_stds = [], []
        signal_channels = [self.x_channel, self.y_channel]
        while self.started:
            data_dict = self.daq.get_data(signal_channels=signal_channels,
                                          int_time=self.int_time_x,
                                          sample_rate=self.sample_rate_x,
                                          device=device)
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

            self.x_data_label.setText('X Mean: {0:.5f} ::: X STD: {1:.5f}'.format(x_mean, x_std))
            self.y_data_label.setText('Y Mean: {0:.5f} ::: Y STD: {1:.5f}'.format(y_mean, y_std))
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
            file_name = 'IV_{0}_Scan_{1}.txt'.format(self.sample_name_lineedit.text(), str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def ivc_save(self, save_path=None):
        '''
        '''
        if save_path is None:
            save_path = self.ivc_index_file_name()
            save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter='*.txt,*.dat')[0]
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

    def ivc_plot_xy(self, running=False, file_name=''):
        '''
        '''
        if len(self.x_data) == 0:
            return None
        if running:
            fig, ax = self.ivc_create_blank_fig(frac_screen_width=0.8, frac_screen_height=0.4, left=0.1, top=0.9)
        else:
            fig, ax = self.ivc_create_blank_fig(frac_screen_width=0.6, frac_screen_height=0.5, left=0.1, top=0.9)
        data_clip_lo = float(self.data_clip_lo_lineedit.text())
        data_clip_hi = float(self.data_clip_hi_lineedit.text())
        data_fit_lo = float(self.data_fit_lo_lineedit.text())
        data_fit_hi = float(self.data_fit_hi_lineedit.text())
        squid_calibration_factor = float(self.squid_calibration_label.text())
        i_bolo_real = self.ivc_fit_and_remove_squid_offset()
        i_bolo_std = np.asarray(self.y_stds) * squid_calibration_factor
        v_bias_real = np.asarray(self.x_data) * float(self.x_correction_combobox.currentText()) * 1e6 #uV
        v_bias_std = np.asarray(self.x_stds) * float(self.x_correction_combobox.currentText()) * 1e6 #uV
        fit_selector = np.where(np.logical_and(data_fit_lo < v_bias_real, v_bias_real < data_fit_hi))
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
        ax.errorbar(v_bias_real[selector], i_bolo_real[selector], xerr=v_bias_std[selector], yerr=i_bolo_std[selector], marker='.', linestyle='-', label=label)
        if running:
            ax.set_xlabel('Bias Voltage ($\mu V$)', fontsize=14)
            ax.set_ylabel('TES Current ($\mu A$)', fontsize=14)
            ax.set_title(title, fontsize=14)
            pl.legend(loc='best', fontsize=14)
            fig.savefig('temp_xy.png', transparent=True)
            fig.savefig('temp_xy.png', transparent=False)
            pl.close('all')
            image_to_display = QtGui.QPixmap('temp_xy.png')
            self.xy_scatter_label.setPixmap(image_to_display)
            os.remove('temp_xy.png')
        else:
            ax.set_xlabel('Bias Voltage ($\mu V$)', fontsize=16)
            ax.set_ylabel('TES Current ($\mu A$)', fontsize=16)
            ax.set_title(title, fontsize=16)
            pl.legend(loc='best', fontsize=14)
            ax.tick_params(axis='x', labelsize=16)
            ax.tick_params(axis='y', labelsize=16)
            fig.savefig(file_name, transparent=False)
            pl.show()

    def ivc_adjust_x_data(self):
        '''
        '''
        x_data = []
        x_stds = []
        voltage_reduction_factor = float(self.x_correction_combobox.currentText())
        x_data = np.asarray(self.x_data) * voltage_reduction_factor * 1e6 #uV
        x_stds = np.asarray(self.x_stds) * voltage_reduction_factor * 1e6 #uV
        return x_data, x_stds

    def ivc_adjust_y_data(self):
        '''
        '''
        y_data = []
        y_stds = []
        calibration_factor = float(self.squid_calibration_label.text())
        y_data = np.asarray(self.y_data) * calibration_factor
        y_stds = np.asarray(self.y_stds) * calibration_factor
        return y_data, y_stds

    def ivc_fit_and_remove_squid_offset(self, polyfit_n=1):
        '''
        '''
        calibration_factor = float(self.squid_calibration_label.text())
        y_vector = np.asarray(copy(self.y_data)) * calibration_factor# calibrated to uA from V
        scaled_x_vector = np.asarray(copy(self.x_data))
        scaled_x_vector *= float(self.x_correction_combobox.currentText())
        scaled_x_vector *= 1e6 # This is now in uV
        data_clip_lo = float(self.data_clip_lo_lineedit.text())
        data_clip_hi = float(self.data_clip_hi_lineedit.text())
        selector = np.logical_and(data_clip_lo < scaled_x_vector, scaled_x_vector < data_clip_hi)
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
