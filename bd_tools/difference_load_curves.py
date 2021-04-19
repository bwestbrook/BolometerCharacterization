import time
import shutil
import os
import simplejson
import subprocess
import pylab as pl
import numpy as np
import scipy.optimize as opt
from scipy.signal import medfilt2d
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class DifferenceLoadCurves(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi,  data_folder):
        '''
        '''
        super(DifferenceLoadCurves, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = data_folder
        self.iv_1_path = None
        self.iv_2_path = None
        self.spectra_path = None
        self.bands = {
            'SO30': {
                'Band Center': 30,
                'Project': 'Simons Observatory',
                'Freq Column': 0,
                'Transmission Column': 3,
                'Header Lines': 2,
                'Path': os.path.join('bd_lib', 'simulated_bands', 'Nitride_Lumped_Diplexer_030_05_040_08_MoreWider20190226_300GHz.csv')
                },
            'SO40': {
                'Band Center': 40,
                'Project': 'Simons Observatory',
                'Freq Column': 0,
                'Transmission Column': 4,
                'Header Lines': 2,
                'Path': os.path.join('bd_lib', 'simulated_bands', 'Nitride_Lumped_Diplexer_030_05_040_08_MoreWider20190226_300GHz.csv')
                }
            }
        self.dlc_configure_panel()
        self.resize(self.minimumSizeHint())

    #################################################################################
    # Gui Config
    ##################################################################################

    def dlc_configure_panel(self):
        '''
        '''
        #############################################################
        # IV 1
        #############################################################
        self.load_iv_1_pushbutton = QtWidgets.QPushButton('Load IV 1')
        self.layout().addWidget(self.load_iv_1_pushbutton, 0, 0, 1, 4)
        self.load_iv_1_pushbutton.clicked.connect(self.dlc_load_iv_1)
        # IV 1 Fitting and Clipping
        self.iv_1_data_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Lo (uV):')
        self.iv_1_data_clip_lo_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_1_data_clip_lo_lineedit))
        self.iv_1_data_clip_lo_lineedit.setText('0')
        self.iv_1_data_clip_lo_lineedit.returnPressed.connect(self.dlc_load_iv_1)
        self.layout().addWidget(self.iv_1_data_clip_lo_lineedit, 1, 0, 1, 2)
        self.iv_1_data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Hi (uV):')
        self.iv_1_data_clip_hi_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_1_data_clip_hi_lineedit))
        self.iv_1_data_clip_hi_lineedit.setText('35')
        self.iv_1_data_clip_hi_lineedit.returnPressed.connect(self.dlc_load_iv_1)
        self.layout().addWidget(self.iv_1_data_clip_hi_lineedit, 1, 2, 1, 2)
        self.iv_1_fit_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Fit Clip Lo (uV):')
        self.iv_1_fit_clip_lo_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_1_fit_clip_lo_lineedit))
        self.iv_1_fit_clip_lo_lineedit.setText('13')
        self.iv_1_fit_clip_lo_lineedit.returnPressed.connect(self.dlc_load_iv_1)
        self.layout().addWidget(self.iv_1_fit_clip_lo_lineedit, 2, 0, 1, 2)
        self.iv_1_fit_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Fit Clip Hi (uV):')
        self.iv_1_fit_clip_hi_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_1_fit_clip_hi_lineedit))
        self.iv_1_fit_clip_hi_lineedit.setText('20')
        self.iv_1_fit_clip_hi_lineedit.returnPressed.connect(self.dlc_load_iv_1)
        self.layout().addWidget(self.iv_1_fit_clip_hi_lineedit, 2, 2, 1, 2)
        # IV 1 X/Y bath and load
        self.iv_1_t_bath_lineedit = self.gb_make_labeled_lineedit(label_text='IV 1 Bath Temp (mK)')
        self.iv_1_t_bath_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_1_t_bath_lineedit))
        self.iv_1_t_bath_lineedit.setText('275')
        self.iv_1_t_bath_lineedit.returnPressed.connect(self.dlc_load_iv_1)
        self.layout().addWidget(self.iv_1_t_bath_lineedit, 3, 0, 1, 2)
        self.iv_1_t_load_lineedit = self.gb_make_labeled_lineedit(label_text='IV 1 Load Temp (K)')
        self.iv_1_t_load_lineedit.setText('300')
        self.iv_1_t_load_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_1_t_load_lineedit))
        self.iv_1_t_load_lineedit.returnPressed.connect(self.dlc_load_iv_1)
        self.layout().addWidget(self.iv_1_t_load_lineedit, 3, 2, 1, 2)
        # IV 1 X/Y corrections
        self.iv_1_x_correction_lineedit = self.gb_make_labeled_lineedit(label_text='X Correction Factor')
        self.iv_1_x_correction_lineedit.setText('1e-4')
        self.iv_1_x_correction_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_1_x_correction_lineedit))
        self.iv_1_x_correction_lineedit.returnPressed.connect(self.dlc_load_iv_1)
        self.layout().addWidget(self.iv_1_x_correction_lineedit, 4, 0, 1, 2)
        self.iv_1_y_correction_lineedit = self.gb_make_labeled_lineedit(label_text='Y Correction Factor (uA/V)')
        self.iv_1_y_correction_lineedit.setText('30')
        self.iv_1_y_correction_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_1_y_correction_lineedit))
        self.iv_1_y_correction_lineedit.returnPressed.connect(self.dlc_load_iv_1)
        self.layout().addWidget(self.iv_1_y_correction_lineedit, 4, 2, 1, 2)

        # IV 1 Plotting
        self.iv_1_raw_plot_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.iv_1_raw_plot_label, 5, 0, 1, 4)
        self.iv_1_calibrated_plot_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.iv_1_calibrated_plot_label, 6, 0, 1, 4)
        self.iv_1_paneled_plot_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.iv_1_paneled_plot_label, 7, 0, 1, 4)

        # IV 1 Saving (in case new fit would liked to be saved)
        self.iv_1_save_plot_pushbutton = QtWidgets.QPushButton('Save IV 1 Plot')
        self.layout().addWidget(self.iv_1_save_plot_pushbutton, 8, 0, 1, 4)
        self.iv_1_save_plot_pushbutton.clicked.connect(self.dlc_save_iv_1)
        # High Load
        self.iv_1_high_load_label = QtWidgets.QLabel('High Load')
        self.layout().addWidget(self.iv_1_high_load_label, 9, 0, 1, 4)
        #############################################################
        # IV 2
        #############################################################
        self.load_iv_2_pushbutton = QtWidgets.QPushButton('Load IV 2')
        self.layout().addWidget(self.load_iv_2_pushbutton, 0, 4, 1, 4)
        self.load_iv_2_pushbutton.clicked.connect(self.dlc_load_iv_2)
        # IV 2 Fitting and Clipping
        self.iv_2_data_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Lo (uV):')
        self.iv_2_data_clip_lo_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_2_data_clip_lo_lineedit))
        self.iv_2_data_clip_lo_lineedit.setText('0')
        self.iv_2_data_clip_lo_lineedit.returnPressed.connect(self.dlc_load_iv_2)
        self.layout().addWidget(self.iv_2_data_clip_lo_lineedit, 1, 4, 1, 2)
        self.iv_2_data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Hi (uV):')
        self.iv_2_data_clip_hi_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_2_data_clip_hi_lineedit))
        self.iv_2_data_clip_hi_lineedit.setText('35')
        self.iv_2_data_clip_hi_lineedit.returnPressed.connect(self.dlc_load_iv_2)
        self.layout().addWidget(self.iv_2_data_clip_hi_lineedit, 1, 6, 1, 2)
        self.iv_2_fit_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Fit Clip Lo (uV):')
        self.iv_2_fit_clip_lo_lineedit.setText('5')
        self.iv_2_fit_clip_lo_lineedit.returnPressed.connect(self.dlc_load_iv_2)
        self.iv_2_fit_clip_lo_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_2_fit_clip_lo_lineedit))
        self.layout().addWidget(self.iv_2_fit_clip_lo_lineedit, 2, 4, 1, 2)
        self.iv_2_fit_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Fit Clip Hi (uV):')
        self.iv_2_fit_clip_hi_lineedit.setText('20')
        self.iv_2_fit_clip_hi_lineedit.returnPressed.connect(self.dlc_load_iv_2)
        self.iv_2_fit_clip_hi_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_2_fit_clip_hi_lineedit))
        self.layout().addWidget(self.iv_2_fit_clip_hi_lineedit, 2, 6, 1, 2)
        # IV 2 X/Y bath and load
        self.iv_2_t_bath_lineedit = self.gb_make_labeled_lineedit(label_text='IV 2 Bath Temp (mK)')
        self.iv_2_t_bath_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_2_t_bath_lineedit))
        self.iv_2_t_bath_lineedit.setText('275')
        self.iv_2_t_bath_lineedit.returnPressed.connect(self.dlc_load_iv_2)
        self.layout().addWidget(self.iv_2_t_bath_lineedit, 3, 4, 1, 2)
        self.iv_2_t_load_lineedit = self.gb_make_labeled_lineedit(label_text='IV 2 Load Temp (K)')
        self.iv_2_t_load_lineedit.setText('77')
        self.iv_2_t_load_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_2_t_load_lineedit))
        self.iv_2_t_load_lineedit.returnPressed.connect(self.dlc_load_iv_2)
        self.layout().addWidget(self.iv_2_t_load_lineedit, 3, 6, 1, 2)
        # IV 2 X/Y corrections
        self.iv_2_x_correction_lineedit = self.gb_make_labeled_lineedit(label_text='X Correction Factor')
        self.iv_2_x_correction_lineedit.setText('1e-5')
        self.iv_2_x_correction_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_2_x_correction_lineedit))
        self.iv_2_x_correction_lineedit.returnPressed.connect(self.dlc_load_iv_2)
        self.layout().addWidget(self.iv_2_x_correction_lineedit, 4, 4, 1, 2)
        self.iv_2_y_correction_lineedit = self.gb_make_labeled_lineedit(label_text='Y Correction Factor (uA/V)')
        self.iv_2_y_correction_lineedit.setText('30')
        self.iv_2_y_correction_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_2_y_correction_lineedit))
        self.iv_2_y_correction_lineedit.returnPressed.connect(self.dlc_load_iv_2)
        self.layout().addWidget(self.iv_2_y_correction_lineedit, 4, 6, 1, 2)
        # IV 2 Plotting
        self.iv_2_raw_plot_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.iv_2_raw_plot_label, 5, 4, 1, 4)
        self.iv_2_calibrated_plot_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.iv_2_calibrated_plot_label, 6, 4, 1, 4)
        self.iv_2_paneled_plot_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.iv_2_paneled_plot_label, 7, 4, 1, 4)
        # IV 2 Saving (in case new fit would liked to be saved)
        self.iv_2_save_plot_pushputton = QtWidgets.QPushButton('Save IV 2 Plot')
        self.layout().addWidget(self.iv_2_save_plot_pushputton, 8, 4, 1, 4)
        # Low Load
        self.iv_2_low_load_label = QtWidgets.QLabel('Low Load')
        self.layout().addWidget(self.iv_2_low_load_label, 9, 4, 1, 4)
        #############################################################
        # Spectra
        #############################################################
        self.load_spectra_pushbutton = QtWidgets.QPushButton('Load Spectra 2')
        self.layout().addWidget(self.load_spectra_pushbutton, 0, 8, 1, 4)
        self.load_spectra_pushbutton.clicked.connect(self.dlc_load_spectra)
        # Sample Name and Band Type
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name')
        self.layout().addWidget(self.sample_name_lineedit, 1, 8, 1, 4)
        # Data Clipping and Smoothing 
        self.band_select_combobox = self.gb_make_labeled_combobox(label_text='Detector Band')
        for band in self.bands:
            self.band_select_combobox.addItem(band)
        self.band_select_combobox.activated.connect(self.dlc_load_spectra)
        self.layout().addWidget(self.band_select_combobox, 2, 8, 1, 2)
        self.spectra_data_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Lo (GHz):')
        self.spectra_data_clip_lo_lineedit.returnPressed.connect(self.dlc_load_spectra)
        self.spectra_data_clip_lo_lineedit.setText('0')
        self.layout().addWidget(self.spectra_data_clip_lo_lineedit, 3, 8, 1, 2)
        self.spectra_data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Hi (GHz):')
        self.spectra_data_clip_hi_lineedit.setText('300')
        self.layout().addWidget(self.spectra_data_clip_hi_lineedit, 3, 10, 1, 2)
        self.spectra_data_clip_hi_lineedit.setText('300')
        self.spectra_data_clip_hi_lineedit.returnPressed.connect(self.dlc_load_spectra)
        self.smoothing_factor_lineedit = self.gb_make_labeled_lineedit(label_text='Smoothing Factor')
        self.smoothing_factor_lineedit.returnPressed.connect(self.dlc_load_spectra)
        self.smoothing_factor_lineedit.setText('0.01')
        self.layout().addWidget(self.smoothing_factor_lineedit, 4, 8, 1, 2)
        self.renormalize_checkbox = QtWidgets.QCheckBox('Renormalize post clip?')
        self.renormalize_checkbox.setChecked(True)
        self.layout().addWidget(self.renormalize_checkbox, 4, 10, 1, 2)
        # Spectra Plotting
        self.spectra_plot_raw_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.spectra_plot_raw_label, 5, 8, 1, 4)
        self.spectra_plot_calibrated = QtWidgets.QLabel('')
        self.layout().addWidget(self.spectra_plot_calibrated, 6, 8, 1, 4)
        # Spectra Saving (in case new fit would liked to be saved)
        self.save_spectra_pushbutton = QtWidgets.QPushButton('Save Processed Spectra')
        self.layout().addWidget(self.save_spectra_pushbutton, 8, 8, 1, 4)
        # Spectra Saving (in case new fit would liked to be saved)
        self.difference_load_curves_pushbutton = QtWidgets.QPushButton('Difference Load Curves')
        self.layout().addWidget(self.difference_load_curves_pushbutton, 10, 0, 1, 12)

    #################################################################################
    # IV Analysis
    ##################################################################################

    def dlc_save_iv_1(self):
        '''
        '''
        temp_paneled_iv_1_path = os.path.join('temp_files', 'temp_paneled_iv_1.png')
        suggested_save_path = self.iv_1_path.replace('.txt', '.png').replace('raw', 'paneled')
        iv_1_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Select Data File', suggested_save_path, filter=suggested_save_path)[0]
        if len(iv_1_path) > 0:
            shutil.copy(temp_paneled_iv_1_path, iv_1_path)

    def dlc_load_iv_1(self):
        '''
        '''
        data_clip_lo = float(self.iv_1_data_clip_lo_lineedit.text())
        data_clip_hi = float(self.iv_1_data_clip_hi_lineedit.text())
        fig, ax = self.dlc_create_blank_fig(frac_screen_height=0.2)
        if self.iv_1_path is None:
            iv_1_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
            if len(iv_1_path) == 0:
                return None
            self.iv_1_path = iv_1_path
        else:
            iv_1_path = self.iv_1_path
        # Calibration with Fit
        bias_voltage, squid_voltage = self.dlc_load_iv_data(iv_1_path)
        ax.plot(bias_voltage, squid_voltage, label='raw')
        temp_iv_1_path = os.path.join('temp_files', 'temp_iv_1.png')
        ax.set_xlabel('Bias Voltage Raw (V)')
        ax.set_ylabel('SQUID Outpu Voltage Raw (V)')
        ax.set_title('Raw IV data')
        fig.savefig(temp_iv_1_path)
        image_to_display = QtGui.QPixmap(temp_iv_1_path)
        self.iv_1_raw_plot_label.setPixmap(image_to_display)
        pl.close('all')
        # Calibration with Fit
        fig, ax = self.dlc_create_blank_fig(frac_screen_height=0.2)
        self.calibrated_bias_voltage, self.calibrated_squid_current, fit_clip_lo, fit_clip_hi = self.dlc_calibrate_raw_data(bias_voltage, squid_voltage, iv=1)
        selector = np.logical_and(fit_clip_lo < self.calibrated_bias_voltage, self.calibrated_bias_voltage < fit_clip_hi)
        ax.plot(self.calibrated_bias_voltage, self.calibrated_squid_current, label='raw')
        ax.plot(self.calibrated_bias_voltage[selector], self.calibrated_squid_current[selector], color='r', label='Fit')
        pl.legend()
        ax.set_xlabel('TES Bias Voltage (uV)')
        ax.set_ylabel('TES Current (uA)')
        ax.set_title('Calibrated IV data')
        temp_calibrated_iv_1_path = os.path.join('temp_files', 'temp_calibrated_iv_1.png')
        fig.savefig(temp_calibrated_iv_1_path)
        image_to_display = QtGui.QPixmap(temp_calibrated_iv_1_path)
        self.iv_1_calibrated_plot_label.setPixmap(image_to_display)
        pl.close('all')
        fig = self.dlc_plot_all_curves(self.calibrated_bias_voltage, self.calibrated_squid_current, iv=1, stds=None, label='', fit_clip=(fit_clip_lo, fit_clip_hi),
                                       plot_clip=(data_clip_lo, data_clip_hi), frac_screen_height=0.4, frac_screen_width=0.3)
        temp_paneled_iv_1_path = os.path.join('temp_files', 'temp_paneled_iv_1.png')
        fig.savefig(temp_paneled_iv_1_path)
        image_to_display = QtGui.QPixmap(temp_paneled_iv_1_path)
        self.iv_1_paneled_plot_label.setPixmap(image_to_display)
        pl.close('all')

    def dlc_save_iv_2(self):
        '''
        '''
        temp_paneled_iv_2_path = os.path.join('temp_files', 'temp_paneled_iv_1.png')
        suggested_save_path = self.iv_2_path.replace('.txt', '.png').replace('raw', 'paneled')
        iv_1_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Select Data File', suggested_save_path, filter=suggested_save_path)[0]
        if len(iv_2_path) > 0:
            shutil.copy(temp_paneled_iv_2_path, iv_2_path)

    def dlc_load_iv_2(self):
        '''
        '''
        data_clip_lo = float(self.iv_2_data_clip_lo_lineedit.text())
        data_clip_hi = float(self.iv_2_data_clip_hi_lineedit.text())
        fig, ax = self.dlc_create_blank_fig(frac_screen_height=0.2)
        if self.iv_2_path is None:
            iv_2_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
            if len(iv_2_path) == 0:
                return None
            self.iv_2_path = iv_2_path
        else:
            iv_2_path = self.iv_2_path
        # Calibration with Fit
        bias_voltage, squid_voltage = self.dlc_load_iv_data(iv_2_path)
        ax.plot(bias_voltage, squid_voltage, label='raw')
        temp_iv_2_path = os.path.join('temp_files', 'temp_iv_2.png')
        ax.set_xlabel('Bias Voltage Raw (V)')
        ax.set_ylabel('SQUID Outpu Voltage Raw (V)')
        ax.set_title('Raw IV data')
        fig.savefig(temp_iv_2_path)
        image_to_display = QtGui.QPixmap(temp_iv_2_path)
        self.iv_2_raw_plot_label.setPixmap(image_to_display)
        pl.close('all')
        # Calibration with Fit
        fig, ax = self.dlc_create_blank_fig(frac_screen_height=0.2)
        self.calibrated_bias_voltage, self.calibrated_squid_current, fit_clip_lo, fit_clip_hi = self.dlc_calibrate_raw_data(bias_voltage, squid_voltage, iv=2)
        selector = np.logical_and(fit_clip_lo < self.calibrated_bias_voltage, self.calibrated_bias_voltage < fit_clip_hi)
        ax.plot(self.calibrated_bias_voltage, self.calibrated_squid_current, label='raw')
        ax.plot(self.calibrated_bias_voltage[selector], self.calibrated_squid_current[selector], color='r', label='Fit')
        pl.legend()
        ax.set_xlabel('TES Bias Voltage (uV)')
        ax.set_ylabel('TES Current (uA)')
        ax.set_title('Calibrated IV data')
        temp_calibrated_iv_2_path = os.path.join('temp_files', 'temp_calibrated_iv_2.png')
        fig.savefig(temp_calibrated_iv_2_path)
        image_to_display = QtGui.QPixmap(temp_calibrated_iv_2_path)
        self.iv_2_calibrated_plot_label.setPixmap(image_to_display)
        pl.close('all')
        fig = self.dlc_plot_all_curves(self.calibrated_bias_voltage, self.calibrated_squid_current, iv=2, stds=None, label='', fit_clip=(fit_clip_lo, fit_clip_hi),
                                       plot_clip=(data_clip_lo, data_clip_hi), frac_screen_height=0.4, frac_screen_width=0.3)
        temp_paneled_iv_2_path = os.path.join('temp_files', 'temp_paneled_iv_2.png')
        fig.savefig(temp_paneled_iv_2_path)
        image_to_display = QtGui.QPixmap(temp_paneled_iv_2_path)
        self.iv_2_paneled_plot_label.setPixmap(image_to_display)
        pl.close('all')

    def dlc_load_iv_data(self, data_path):
        '''
        '''

        bias_voltage = []
        squid_voltage = []
        with open(data_path, 'r') as file_handle:
            for line in file_handle:
                squid_voltage_val = line.split(',')[2].strip()
                bias_voltage_val = line.split(',')[0].strip()
                if float(bias_voltage_val) < 0:
                    bias_voltage.append(-1 * float(bias_voltage_val))
                else:
                    bias_voltage.append(float(bias_voltage_val))
                squid_voltage.append(float(squid_voltage_val))
        return np.asarray(bias_voltage), np.asarray(squid_voltage)

    def dlc_calibrate_raw_data(self, x_data, y_data, iv=1, polyfit_n=1):
        '''
        '''
        voltage_correction_factor = float(getattr(self, 'iv_{0}_x_correction_lineedit'.format(iv)).text())
        calibrated_bias_voltage = np.asarray(copy(x_data))
        calibrated_bias_voltage *= voltage_correction_factor
        calibrated_bias_voltage *= 1e6 # This is now in uV
        calibration_factor = float(getattr(self, 'iv_{0}_y_correction_lineedit'.format(iv)).text())
        calibrated_squid_current = np.asarray(copy(y_data)) * calibration_factor # calibrated to uA from V
        fit_clip_lo = float(getattr(self, 'iv_{0}_fit_clip_lo_lineedit'.format(iv)).text())
        fit_clip_hi = float(getattr(self, 'iv_{0}_fit_clip_hi_lineedit'.format(iv)).text())
        selector = np.logical_and(fit_clip_lo < calibrated_bias_voltage, calibrated_bias_voltage < fit_clip_hi)
        if len(calibrated_bias_voltage[selector]) > 2:
            fit_vals = np.polyfit(calibrated_bias_voltage[selector], calibrated_squid_current[selector], polyfit_n)
            calibrated_squid_current = calibrated_squid_current - fit_vals[1]
            if fit_vals[0] < 0:
                calibrated_squid_current = -1 * calibrated_squid_current
        else:
            calibrated_squid_current = np.array(calibrated_squid_current)
        return calibrated_bias_voltage, calibrated_squid_current, fit_clip_lo, fit_clip_hi

    #################################################################################
    # Spectral Analysis
    ##################################################################################

    def dlc_load_spectra(self):
        '''
        '''
        data_clip_lo = float(self.spectra_data_clip_lo_lineedit.text()) * 1e9
        data_clip_hi = float(self.spectra_data_clip_hi_lineedit.text()) * 1e9
        band = self.band_select_combobox.currentText()
        if self.spectra_path is None:
            spectra_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
            if len(spectra_path) == 0:
                return None
            self.spectra_path = spectra_path
        else:
            spectra_path = self.spectra_path
        fft_frequency_vector, fft_vector, normalized_fft_vector = self.dlc_load_spectra_data(spectra_path, smoothing_factor=0.0)
        fft_frequency_vector_simulated, fft_vector_simulated = self.dlc_load_simulated_band()
        fig, ax = self.dlc_create_blank_fig(frac_screen_width=0.4, frac_screen_height=0.3)
        ax.plot(fft_frequency_vector * 1e-9, normalized_fft_vector, label='Raw Data')
        ax.plot(fft_frequency_vector_simulated, fft_vector_simulated, label='HFSS Data')
        ax.set_xlabel('Frequency (GHz)')
        spectra_png_save_path = os.path.join('temp_files', 'temp_spectra.png')
        pl.legend()
        fig.savefig(spectra_png_save_path)
        image_to_display = QtGui.QPixmap(spectra_png_save_path)
        self.spectra_plot_raw_label.setPixmap(image_to_display)
        pl.close('all')
        fig, ax = self.dlc_create_blank_fig(frac_screen_width=0.4, frac_screen_height=0.3)
        fft_frequency_vector_processed, fft_vector_processed, normalized_fft_vector_processed = self.dlc_load_spectra_data(spectra_path)
        delta_power, integrated_bandwidth = self.dlc_compute_delta_power_at_window(fft_frequency_vector_processed, normalized_fft_vector_processed)
        label='$\Delta(P)$ {0:.2f} pW\nBW {1:.2f} GHz '.format(delta_power * 1e12, integrated_bandwidth * 1e-9)
        ax.plot(fft_frequency_vector_processed * 1e-9, normalized_fft_vector_processed, label=label)
        ax.plot(fft_frequency_vector_simulated, fft_vector_simulated, label='HFSS Data')
        ax.set_xlabel('Frequency (GHz)')
        spectra_png_save_path = os.path.join('temp_files', 'temp_spectra.png')
        pl.legend()
        fig.savefig(spectra_png_save_path)
        image_to_display = QtGui.QPixmap(spectra_png_save_path)
        self.spectra_plot_calibrated.setPixmap(image_to_display)
        pl.close('all')

    def dlc_load_spectra_data(self, data_path, smoothing_factor=None):
        '''
        '''
        normalize_post_clip = self.renormalize_checkbox.isChecked()
        if smoothing_factor is None:
            smoothing_factor = float(self.smoothing_factor_lineedit.text())
        data_clip_lo = float(self.spectra_data_clip_lo_lineedit.text()) * 1e9
        data_clip_hi = float(self.spectra_data_clip_hi_lineedit.text()) * 1e9
        with open(data_path, 'r') as file_handle:
            lines = file_handle.readlines()
            frequency_vector = np.zeros(len(lines))
            transmission_vector = np.zeros(len(lines))
            for i, line in enumerate(lines):
                if ',' in line:
                    frequency = line.split(', ')[0]
                    transmission = line.split(', ')[1]
                else:
                    frequency = line.split('\t')[0]
                    transmission = line.split('\t')[1]
                if float(data_clip_lo) < float(frequency) < float(data_clip_hi):
                    np.put(frequency_vector, i, frequency)
                    np.put(transmission_vector, i, transmission)
        transmission_vector = transmission_vector[frequency_vector > 0.0]
        frequency_vector = frequency_vector[frequency_vector > 0.0]
        if smoothing_factor > 0.0:
            transmission_vector = self.dlc_running_mean(transmission_vector, smoothing_factor=smoothing_factor)
            normalized_transmission_vector = transmission_vector / max(transmission_vector)
            with open(data_path.replace('.fft', '_smoothed.fft'), 'w') as smoothed_data_handle:
                for i, transmission_value in enumerate(normalized_transmission_vector):
                    frequency_value = frequency_vector[i]
                    line = '{0:.4f}\t{1:.4f}\n'.format(frequency_value, transmission_value)
                    smoothed_data_handle.write(line)
        normalized_transmission_vector = transmission_vector
        if normalize_post_clip:
            normalized_transmission_vector = normalized_transmission_vector / np.max(normalized_transmission_vector)
        return frequency_vector, transmission_vector, normalized_transmission_vector

    def dlc_load_simulated_band(self):
        '''
        '''
        data_clip_lo = float(self.spectra_data_clip_lo_lineedit.text()) * 1e9
        data_clip_hi = float(self.spectra_data_clip_hi_lineedit.text()) * 1e9
        band = self.band_select_combobox.currentText()
        data_path = self.bands[band]['Path']
        freq_idx = self.bands[band]['Freq Column']
        trans_idx = self.bands[band]['Transmission Column']
        header_lines = self.bands[band]['Header Lines']
        with open(data_path, 'r') as file_handle:
            lines = file_handle.readlines()
            frequency_vector = np.zeros([])
            transmission_vector = np.zeros([])
            for i, line in enumerate(lines):
                if i > header_lines:
                    try:
                        if ',' in line:
                            frequency = line.split(',')[freq_idx].strip()
                            transmission = line.split(',')[trans_idx].strip()
                        else:
                            frequency = line.split('\t')[freq_idx].strip()
                            transmission = line.split('\t')[trans_idx].strip()
                        if float(data_clip_lo) < float(frequency) * 1e9 < float(data_clip_hi) and self.gb_is_float(transmission):
                            frequency_vector = np.append(frequency_vector, float(frequency))
                            transmission_vector = np.append(transmission_vector, float(transmission))
                    except ValueError:
                        pass
        #transmission_vector = np.asarray(transmission_vector) / np.max(np.asarray(transmission_vector))
        #frequency_vector = np.asarray(frequency_vector)
        return frequency_vector, transmission_vector

    def dlc_compute_delta_power_at_window(self, frequency_vector, normalized_transmission_vector, show_spectra=False):
        '''
        '''
        t_source_high = float(self.iv_1_t_load_lineedit.text())
        t_source_low = float(self.iv_2_t_load_lineedit.text())
        band_edge_low = float(self.spectra_data_clip_lo_lineedit.text()) * 1e9
        band_edge_high = float(self.spectra_data_clip_hi_lineedit.text()) * 1e9
        band = self.band_select_combobox.currentText()
        boltzmann_constant = 1.38e-23
        print(frequency_vector)
        selector = np.logical_and(np.where(frequency_vector > band_edge_low, True, False), np.where(frequency_vector < band_edge_high, True, False))
        integrated_bandwidth = np.trapz(normalized_transmission_vector[selector], frequency_vector[selector])
        delta_power = boltzmann_constant * (t_source_high - t_source_low) * integrated_bandwidth  # in W
        if show_spectra:
            pl.plot(frequency_vector, normalized_transmission_vector)
            pl.plot(normalized_transmission_vector)
            pl.show()
        return delta_power, integrated_bandwidth

    def dlc_running_mean(self, vector, smoothing_factor=0.01):
        '''
        '''
        N = int(smoothing_factor * len(vector))
        averaged_vector = np.zeros(len(vector))
        for i, value in enumerate(vector):
            low_index = i
            hi_index = i + N
            if hi_index > len(vector) - 1:
                hi_index = len(vector) - 1
            averaged_value = np.mean(vector[low_index:hi_index])
            if np.isnan(averaged_value):
                np.put(averaged_vector, i, 0.0)
            else:
                np.put(averaged_vector, i, averaged_value)
        return averaged_vector

    ####################
    # Plotting
    ####################

    def dlc_plot_all_curves(self, bolo_voltage_bias, bolo_current, iv=1, stds=None, label='', fit_clip=None, plot_clip=None,
                            show_plot=False, title='', pturn=True, frac_screen_width=0.3, frac_screen_height=0.35,
                            left=0.15, right=0.98, top=0.9, bottom=0.23, multiple_axes=False):
        '''
        This function creates an x-y scatter plot with V_bias on the x-axis and
        bolo curent on the y-axis.  The resistance value is reported as text annotation
        Inputs:
            bolo_votlage_bias: bolo_voltage in Volts
            bolo_current: bolo_current in Amps
        '''
        fig = pl.figure(figsize=(10, 5))
        width = (frac_screen_width * self.screen_resolution.width()) / self.monitor_dpi
        height = (frac_screen_height * self.screen_resolution.height()) / self.monitor_dpi
        fig = pl.figure(figsize=(width, height))
        fig.subplots_adjust(left=left, right=right, bottom=bottom, hspace=0.66)
        ax1 = fig.add_subplot(221)
        # Make Title from sample name T_bath and T_load
        t_bath = getattr(self, 'iv_1_t_bath_lineedit'.format(iv)).text()
        t_load = getattr(self, 'iv_1_t_load_lineedit'.format(iv)).text()
        sample_name = self.sample_name_lineedit.text()
        title = '{0}\n@{1}mK with {2}K Load'.format(sample_name, t_bath, t_load)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(223)
        ax4 = fig.add_subplot(224)
        ax2.set_axis_off()
        fit_selector = np.logical_and(fit_clip[0] < bolo_voltage_bias, bolo_voltage_bias < fit_clip[1])
        plot_selector = np.logical_and(plot_clip[0] < bolo_voltage_bias, bolo_voltage_bias < plot_clip[1])

        add_fit = False
        fit_vals = (1, 1)
        if len(bolo_voltage_bias[fit_selector]) > 2:
            fit_vals = np.polyfit(bolo_voltage_bias[fit_selector], bolo_current[fit_selector], 1)
            v_fit_x_vector = np.arange(fit_clip[0], fit_clip[1], 0.2)
            selector_2 = np.logical_and(fit_clip[0] < v_fit_x_vector, v_fit_x_vector < fit_clip[1])
            poly_fit = np.polyval(fit_vals, v_fit_x_vector[selector_2])
            add_fit = True
        resistance_vector = bolo_voltage_bias / bolo_current
        power_vector = bolo_voltage_bias * bolo_current
        ax1.plot(bolo_voltage_bias[plot_selector], bolo_current[plot_selector], '.', label=label)
        if stds is not None:
            ax1.errorbar(bolo_voltage_bias[plot_selector], bolo_current[plot_selector], yerr=stds[plot_selector],
                         label='error', marker='.', linestyle='None', alpha=0.25)
        if pturn and len(bolo_voltage_bias) > 2:
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
        ax1.set_xlabel("Voltage ($\mu$V)", fontsize=12)
        ax1.set_ylabel("Current ($\mu$A)", fontsize=12)
        ax3.set_xlabel("Voltage ($\mu$V)", fontsize=12)
        ax3.set_ylabel("Res ($\Omega$)", fontsize=12)
        ax4.set_xlabel("Res ($\Omega$)", fontsize=12)
        ax4.set_ylabel("Power ($pW$)", fontsize=12)
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
        #ax4.set_ylim(0, 0.5 * max(power_vector[plot_selector]))
        #ax4.set_xlim(0, 1.1 * max(power_vector[plot_selector]))
        #(max(power_vector[plot_selector]) - 0.8 * max(power_vector[plot_selector]),
        xlim_range = max(plot_clip) - min(plot_clip)
        ax1.set_xlim((plot_clip[0] - 0.1 * xlim_range, plot_clip[1] + 0.1 * xlim_range))
        ax3.set_xlim((plot_clip[0] - 0.1 * xlim_range, plot_clip[1] + 0.1 * xlim_range))
        #ax4.set_xlim((plot_clip[0], plot_clip[1]))
        if show_plot:
            pl.show()
        return fig

    def dlc_create_blank_fig(self, frac_screen_width=0.3, frac_screen_height=0.35,
                             left=0.15, right=0.98, top=0.9, bottom=0.23, multiple_axes=False,
                             aspect=None):
        '''
        '''
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
        ax.tick_params(axis='x', labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        return fig, ax
