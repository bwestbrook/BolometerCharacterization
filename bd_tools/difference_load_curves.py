import time
import shutil
import os
import simplejson
import subprocess
import pylab as pl
import numpy as np
import scipy.optimize as opt
from pprint import pprint
from scipy.signal import medfilt2d
from copy import copy
from datetime import datetime
from bd_lib.bolo_daq import BoloDAQ
from bd_lib.mpl_canvas import MplCanvas
from bd_lib.iv_curve_lib import IVCurveLib
from bd_lib.fourier_transform_spectroscopy import FourierTransformSpectroscopy
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib import rc
rc('text', usetex=False)


class DifferenceLoadCurves(QtWidgets.QWidget, GuiBuilder, IVCurveLib, FourierTransformSpectroscopy):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi,  data_folder):
        '''
        '''
        super(DifferenceLoadCurves, self).__init__()

        self.mplc = MplCanvas(self, screen_resolution, monitor_dpi)
        self.bands = self.ftsy_get_bands()
        self.optical_elements_dict = self.ftsy_get_optical_elements()
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
        self.dlc_configure_panel()
        self.resize(self.minimumSizeHint())
        with open(os.path.join('bd_settings', 'squids_settings.json'), 'r') as fh:
            self.squid_calibration_dict = simplejson.load(fh)

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
        self.iv_1_fit_clip_lo_lineedit.setText('14')
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
        # IV 1 Psat Override
        self.iv_1_psat_override_lineedit = self.gb_make_labeled_lineedit(label_text='Psat Override (pW)')
        self.iv_1_psat_override_lineedit.setText('')
        self.iv_1_psat_override_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_1_psat_override_lineedit))
        self.iv_1_psat_override_lineedit.returnPressed.connect(self.dlc_plot_differenced_load_curves)
        self.layout().addWidget(self.iv_1_psat_override_lineedit, 5, 0, 1, 4)
        # IV 1 Plotting
        self.iv_1_raw_plot_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.iv_1_raw_plot_label, 6, 0, 1, 4)
        self.iv_1_calibrated_plot_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.iv_1_calibrated_plot_label, 7, 0, 1, 4)
        self.iv_1_paneled_plot_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.iv_1_paneled_plot_label, 8, 0, 1, 4)
        # IV 1 Saving (in case new fit would liked to be saved)
        self.iv_1_save_plot_pushbutton = QtWidgets.QPushButton('Save IV 1 Plot')
        self.layout().addWidget(self.iv_1_save_plot_pushbutton, 9, 0, 1, 4)
        self.iv_1_save_plot_pushbutton.clicked.connect(self.dlc_save_iv_1)
        # High Load
        self.iv_1_high_load_label = QtWidgets.QLabel('High Load')
        self.layout().addWidget(self.iv_1_high_load_label, 10, 0, 1, 2)
        self.iv_1_high_load_metadata_checkbox = QtWidgets.QCheckBox('Load Meta')
        self.iv_1_high_load_metadata_checkbox.setChecked(True)
        self.layout().addWidget(self.iv_1_high_load_metadata_checkbox, 10, 2, 1, 2)
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
        self.iv_2_fit_clip_lo_lineedit.setText('14')
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
        self.iv_2_x_correction_lineedit.setText('1e-4')
        self.iv_2_x_correction_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_2_x_correction_lineedit))
        self.iv_2_x_correction_lineedit.returnPressed.connect(self.dlc_load_iv_2)
        self.layout().addWidget(self.iv_2_x_correction_lineedit, 4, 4, 1, 2)
        self.iv_2_y_correction_lineedit = self.gb_make_labeled_lineedit(label_text='Y Correction Factor (uA/V)')
        self.iv_2_y_correction_lineedit.setText('30')
        self.iv_2_y_correction_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_2_y_correction_lineedit))
        self.iv_2_y_correction_lineedit.returnPressed.connect(self.dlc_load_iv_2)
        self.layout().addWidget(self.iv_2_y_correction_lineedit, 4, 6, 1, 2)
        # IV 2 Psat Override
        self.iv_2_psat_override_lineedit = self.gb_make_labeled_lineedit(label_text='Psat Override (pW)')
        self.iv_2_psat_override_lineedit.setText('')
        self.iv_2_psat_override_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.iv_2_psat_override_lineedit))
        self.layout().addWidget(self.iv_2_psat_override_lineedit, 5, 4, 1, 4)
        self.iv_2_psat_override_lineedit.returnPressed.connect(self.dlc_plot_differenced_load_curves)
        # IV 2 Plotting
        self.iv_2_raw_plot_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.iv_2_raw_plot_label, 6, 4, 1, 4)
        self.iv_2_calibrated_plot_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.iv_2_calibrated_plot_label, 7, 4, 1, 4)
        self.iv_2_paneled_plot_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.iv_2_paneled_plot_label, 8, 4, 1, 4)
        # IV 2 Saving (in case new fit would liked to be saved)
        self.iv_2_save_plot_pushbutton = QtWidgets.QPushButton('Save IV 2 Plot')
        self.layout().addWidget(self.iv_2_save_plot_pushbutton, 9, 4, 1, 4)
        self.iv_2_save_plot_pushbutton.clicked.connect(self.dlc_save_iv_2)
        # Low Load
        self.iv_2_low_load_label = QtWidgets.QLabel('Low Load')
        self.layout().addWidget(self.iv_2_low_load_label, 10, 4, 1, 2)
        self.iv_2_high_load_metadata_checkbox = QtWidgets.QCheckBox('Load Meta')
        self.iv_2_high_load_metadata_checkbox.setChecked(True)
        self.layout().addWidget(self.iv_2_high_load_metadata_checkbox, 10, 6, 1, 2)
        #############################################################
        # Spectra
        #############################################################
        self.load_spectra_pushbutton = QtWidgets.QPushButton('Load Spectra 2')
        self.layout().addWidget(self.load_spectra_pushbutton, 0, 8, 1, 4)
        self.load_spectra_pushbutton.clicked.connect(self.dlc_load_spectra)
        # Sample Name and Band Type
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name')
        self.sample_name_lineedit.returnPressed.connect(self.dlc_difference_load_curves)
        self.layout().addWidget(self.sample_name_lineedit, 1, 8, 1, 4)
        # Data Clipping and Smoothing 
        self.band_select_combobox = self.gb_make_labeled_combobox(label_text='Detector Band')
        for band in self.bands:
            self.band_select_combobox.addItem(band)
        self.band_select_combobox.setCurrentIndex(1)
        self.band_select_combobox.activated.connect(self.dlc_load_spectra)
        self.layout().addWidget(self.band_select_combobox, 2, 8, 1, 1)
        self.dewar_transmission_lineedit = self.gb_make_labeled_lineedit(label_text='Dewar Eff', lineedit_text='0.5')
        self.dewar_transmission_lineedit.returnPressed.connect(self.dlc_load_spectra)
        self.dewar_transmission_lineedit.setValidator(QtGui.QDoubleValidator(0.001, 1, 6, self.dewar_transmission_lineedit))
        self.layout().addWidget(self.dewar_transmission_lineedit, 2, 9, 1, 1)
        self.frac_rn_lineedit = self.gb_make_labeled_lineedit(label_text='Frac Rn:')
        self.frac_rn_lineedit.returnPressed.connect(self.dlc_load_spectra)
        self.frac_rn_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.frac_rn_lineedit))
        self.frac_rn_lineedit.setText('0.75')
        self.layout().addWidget(self.frac_rn_lineedit, 2, 10, 1, 1)
        self.spectra_data_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Lo (GHz):')
        self.spectra_data_clip_lo_lineedit.returnPressed.connect(self.dlc_load_spectra)
        self.spectra_data_clip_lo_lineedit.setText('0')
        self.layout().addWidget(self.spectra_data_clip_lo_lineedit, 3, 8, 1, 1)
        #
        self.spectra_data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Hi (GHz):')
        self.layout().addWidget(self.spectra_data_clip_hi_lineedit, 3, 9, 1, 1)
        self.spectra_data_clip_hi_lineedit.setText('300')
        self.spectra_data_clip_hi_lineedit.returnPressed.connect(self.dlc_load_spectra)
        self.smoothing_factor_lineedit = self.gb_make_labeled_lineedit(label_text='Smoothing Factor:', lineedit_text='0.0')
        self.layout().addWidget(self.smoothing_factor_lineedit, 3, 10, 1, 2)
        # Buttons
        self.difference_load_curves_pushbutton = QtWidgets.QPushButton('Difference Load Curves')
        self.difference_load_curves_pushbutton.clicked.connect(self.dlc_difference_load_curves)
        self.layout().addWidget(self.difference_load_curves_pushbutton, 4, 8, 1, 4)
        self.reset_input_pushbutton = QtWidgets.QPushButton('Reset Input')
        self.reset_input_pushbutton.clicked.connect(self.dlc_reset_input)
        self.layout().addWidget(self.reset_input_pushbutton, 5, 8, 1, 4)
        # Spectra Plotting
        self.spectra_plot_raw_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.spectra_plot_raw_label, 6, 8, 1, 4)
        self.spectra_plot_calibrated = QtWidgets.QLabel('')
        self.layout().addWidget(self.spectra_plot_calibrated, 7, 8, 1, 4)
        self.differenced_load_curve_label = QtWidgets.QLabel('')
        self.layout().addWidget(self.differenced_load_curve_label, 8, 8, 1, 4)
        # Spectra Saving (in case new fit would liked to be saved)
        self.save_differenced_load_curves_pushbutton = QtWidgets.QPushButton('Save Differenced Load Curves')
        self.layout().addWidget(self.save_differenced_load_curves_pushbutton, 9, 8, 1, 4)
        self.save_differenced_load_curves_pushbutton.clicked.connect(self.dlc_save_differenced_load_curves)
        # Spectra Saving (in case new fit would liked to be saved)

    def dlc_show_active_optical_elements(self):
        '''
        '''
        optical_element = self.optical_elements_combobox.currentText()
        active = self.optical_elements_dict[optical_element]['Active']
        self.optical_element_active_checkbox.setChecked(active)

    def dlc_update_active_optical_elements(self):
        '''
        '''
        optical_element = self.optical_elements_combobox.currentText()
        self.optical_elements_dict[optical_element]['Active'] = self.optical_element_active_checkbox.isChecked()
        if self.optical_elements_dict[optical_element]['Active']:
            print(optical_element)

    #################################################################################
    # Differencing 
    ##################################################################################

    def dlc_save_differenced_load_curves(self):
        '''
        '''
        sample_name = self.sample_name_lineedit.text()
        temp_differenced_load_curve_path = os.path.join('temp_files', 'temp_differenced_load_curves.png')
        suggested_save_path = 'Optical_Efficiency_{0}.png'.format(sample_name)
        differenced_load_curves_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Select Data File', suggested_save_path, filter='.png')[0]
        if len(differenced_load_curves_path) > 0:
            shutil.copy(temp_differenced_load_curve_path, differenced_load_curves_path)

    def dlc_difference_load_curves(self):
        '''
        '''
        band = self.band_select_combobox.currentText()
        if len(band) == 0:
            self.gb_quick_message("Select a band first!")
            return None
        fig = self.dlc_plot_differenced_load_curves()
        differenced_load_curves_path = os.path.join('temp_files', 'temp_differenced_load_curves.png')
        fig.savefig(differenced_load_curves_path)
        image_to_display = QtGui.QPixmap(differenced_load_curves_path)
        image_to_display = image_to_display.scaled(self.spectra_size.width(), int(1.2 * self.spectra_size.height()))
        self.differenced_load_curve_label.setPixmap(image_to_display)
        pl.close('all')

    def dlc_plot_differenced_load_curves(self, frac_screen_width=0.5, frac_screen_height=0.5):
        '''
        '''
        fig, axes = self.dlc_create_differenced_load_curve_figure(frac_screen_width=frac_screen_width, frac_screen_height=frac_screen_height)
        self.dewar_transmission = float(self.dewar_transmission_lineedit.text())
        if self.dewar_transmission == 0:
            self.gb_quick_message('Warning Dewar Transmission Set to 0, using 1.0', msg_type='Warning')
            self.dewar_transmission = 1.0
            self.dewar_transmission_lineedit.setText('1.0')
        # Gather Gui Data
        t_source_high = float(self.iv_1_t_load_lineedit.text())
        t_source_low = float(self.iv_2_t_load_lineedit.text())
        sample_name = self.sample_name_lineedit.text()
        # Process IVs Gui Data
        v_bolo_hi, i_bolo_hi = self.dlc_load_iv_data(self.iv_1_path)
        fig, power_hi = self.dlc_plot_differenced_iv_data(v_bolo_hi, i_bolo_hi, fig, iv=1)
        v_bolo_lo, i_bolo_lo = self.dlc_load_iv_data(self.iv_2_path)
        if len(self.iv_1_psat_override_lineedit.text()) > 0:
            power_hi = float(self.iv_1_psat_override_lineedit.text())
        fig, power_lo = self.dlc_plot_differenced_iv_data(v_bolo_lo, i_bolo_lo, fig, iv=2)
        if len(self.iv_2_psat_override_lineedit.text()) > 0:
            power_lo = float(self.iv_2_psat_override_lineedit.text())
        fig, measured_delta_power, measured_integrated_bandwidth, simulated_delta_power, simulated_integrated_bandwidth = self.dlc_plot_differenced_spectra_data(fig)
        # Summarize Results
        p_sensed = power_lo - power_hi
        t_chop = t_source_high - t_source_low
        efficiency = 100.0 * p_sensed / (measured_delta_power * 1e12)
        simulated_efficiency = 100.0 * p_sensed / (simulated_delta_power * 1e12)
        #pix_efficiency = efficiency / self.dewar_transmission # Dewar transmission
        #simulated_pix_efficiency = efficiency / self.dewar_transmission # Dewar transmission
        pw_per_K_efficiency = p_sensed / (t_source_high - t_source_low)
        text = '{0} Optical Efficiency Data\n'.format(sample_name)
        #text_space = '-' * len(text) + '\n'
        text += 'QTY                  | Measured |  Simuated\n'
        #text += text_space
        text += 'Dew Eff          [%] | {0:7.2f}  | {0:7.2f}\n'.format(1e2 * self.dewar_transmission)
        text += 'T chop           [K] | {0:7.2f}  | {0:7.2f}\n'.format(t_chop)
        text += 'P sensed        [pW] | {0:7.2f}  | {0:7.2f} \n'.format(p_sensed)
        text += 'Abs Eff       [pW/K] | {0:7.3f}  | {0:7.2f}\n'.format(pw_per_K_efficiency)
        text += 'P window        [pW] | {0:7.2f}  | {1:7.2f}\n'.format(measured_delta_power * 1e12, simulated_delta_power * 1e12)
        text += 'Int BW         [GHz] | {0:7.2f}  | {1:7.2f}\n'.format(measured_integrated_bandwidth * 1e-9, simulated_integrated_bandwidth * 1e-9)
        text += 'Rel Eff (e2e)    [%] | {0:7.2f}  | {1:7.2f}\n'.format(efficiency, simulated_efficiency)
        text += 'Rel Eff (pix)    [%] | {0:7.2f}  | {1:7.2f}\n'.format(efficiency / self.dewar_transmission, simulated_efficiency / self.dewar_transmission)
        print(text)
        ax4 = fig.get_axes()[3]
        text = text.replace("%", "pct")
        ax4.annotate(text, xy=(0, 0), xytext=(-0.125, -0.3), fontfamily='monospace', fontsize=9)
        text = '\n\n\n\n$\eta_{dewar}$\n'
        text += '$T_{chop}$\n'
        text += '$P_{window}$\n'
        text += '$P_{sensed}$ [pW]       |\n'
        text += 'Int BW  [GHz]    |\n'
        text += '$\eta_{rel}$ (e2e) [%]    \n'
        text += '$\eta_{rel}$ (pix)\n'
        text += '$\eta_{abs}$ (pix) [pW/K] \n'
        #ax4.annotate(text, xy=(0.025, 0.0), fontfamily='monospace', fontsize=9)
        # Legend
        handles, labels = [], []
        for ax in fig.get_axes():
            hdls, lbls = ax.get_legend_handles_labels()
            handles.extend(hdls)
            labels.extend(lbls)
        #ax4.legend(handles, labels, fontsize=10, numpoints=1, mode="expand", bbox_to_anchor=(0.0, 0, 1, 1))
        ax2 = fig.get_axes()[1]
        ax2.legend(handles, labels, fontsize=9, numpoints=1, loc='best')
        pl.show()
        return fig

    def dlc_plot_differenced_spectra_data(self, fig):
        '''
        '''

        band = self.band_select_combobox.currentText()
        smoothing_factor = float(self.smoothing_factor_lineedit.text())
        t_source_high = float(self.iv_1_t_load_lineedit.text())
        t_source_low = float(self.iv_2_t_load_lineedit.text())
        data_clip_lo = float(self.spectra_data_clip_lo_lineedit.text()) * 1e9
        data_clip_hi = float(self.spectra_data_clip_hi_lineedit.text()) * 1e9
        ax2 = fig.get_axes()[1] # Spectra
        fft_frequency_vector_processed, normalized_fft_vector_processed = self.dlc_load_spectra_data(self.spectra_path)
        if smoothing_factor > 0:
            normalized_fft_vector_processed = self.ftsy_running_mean(normalized_fft_vector_processed, smoothing_factor=smoothing_factor)
        normalized_fft_vector_processed = normalized_fft_vector_processed / np.max(normalized_fft_vector_processed)
        if np.max(fft_frequency_vector_processed) < 1e6:
            fft_frequency_vector_processed *= 1e9
        measured_delta_power, measured_integrated_bandwidth = self.ftsy_compute_delta_power_and_bandwidth_at_window(fft_frequency_vector_processed, normalized_fft_vector_processed,
                                                                                                                    data_clip_lo=data_clip_lo, data_clip_hi=data_clip_hi,
                                                                                                                    t_source_low=t_source_low, t_source_high=t_source_high)
        band = self.band_select_combobox.currentText()
        fft_frequency_vector_simulated, fft_vector_simulated = self.ftsy_load_simulated_band(data_clip_lo, data_clip_hi, band)
        ax2.plot(fft_frequency_vector_simulated, fft_vector_simulated, label='Simulated Spectra')
        simulated_delta_power, simulated_integrated_bandwidth = self.ftsy_compute_delta_power_and_bandwidth_at_window(fft_frequency_vector_simulated * 1e9, fft_vector_simulated,
                                                                                                                      data_clip_lo=data_clip_lo, data_clip_hi=data_clip_hi,
                                                                                                                      t_source_low=t_source_low, t_source_high=t_source_high)
        print(data_clip_lo, data_clip_hi, fft_frequency_vector_processed)
        if np.max(fft_frequency_vector_processed) > 1e6:
            fft_frequency_vector_processed *= 1e-9
            data_clip_lo *= 1e-9
            data_clip_hi *= 1e-9
        data_selector = np.logical_and(data_clip_lo < fft_frequency_vector_processed, fft_frequency_vector_processed < data_clip_hi)
        ax2.plot(fft_frequency_vector_processed[data_selector], normalized_fft_vector_processed[data_selector], label='Measured Spectra')
        return fig, measured_delta_power, measured_integrated_bandwidth, simulated_delta_power, simulated_integrated_bandwidth

    def dlc_plot_differenced_iv_data(self, v_bolo, i_bolo, fig, iv=1):
        '''
        '''
        fracrn = float(self.frac_rn_lineedit.text())
        t_source_high = float(self.iv_1_t_load_lineedit.text())
        t_source_low = float(self.iv_2_t_load_lineedit.text())
        ax1 = fig.get_axes()[0] # IV
        ax3 = fig.get_axes()[2] # RP
        ax3.axvline(fracrn)
        v_bolo, i_bolo, fit_clip_lo, fit_clip_hi = self.dlc_calibrate_raw_data(v_bolo, i_bolo, iv=iv)
        data_clip_lo = float(getattr(self, 'iv_{0}_data_clip_lo_lineedit'.format(iv)).text())
        data_clip_hi = float(getattr(self, 'iv_{0}_data_clip_hi_lineedit'.format(iv)).text())
        fit_clip_lo = float(getattr(self, 'iv_{0}_fit_clip_lo_lineedit'.format(iv)).text())
        fit_clip_hi = float(getattr(self, 'iv_{0}_fit_clip_hi_lineedit'.format(iv)).text())
        data_selector = np.logical_and(data_clip_lo < v_bolo, v_bolo < data_clip_hi)
        fit_selector = np.logical_and(fit_clip_lo < v_bolo, v_bolo < fit_clip_hi)
        p_bolo = v_bolo * i_bolo
        r_bolo = v_bolo / i_bolo
        r_norm = np.mean(r_bolo[fit_selector])
        nearest_r_bolo_index = np.abs((r_bolo / r_norm) - fracrn).argmin()
        power = p_bolo[nearest_r_bolo_index]
        iv_label = 'IV Curve for {0:.1f}K'.format(t_source_high)
        pr_label = 'RP Curve for {0:.1f}K'.format(t_source_high)
        color = 'r'
        if iv == 2:
            iv_label = 'IV Curve for {0:.1f}K'.format(t_source_low)
            pr_label = 'RP Curve for {0:.1f}K'.format(t_source_low)
            color = 'b'
        ax1.plot(v_bolo[data_selector], i_bolo[data_selector], color=color, label=iv_label)
        ax3.plot(r_bolo[data_selector] / r_norm, p_bolo[data_selector], color=color)
        return fig, power

    def dlc_create_differenced_load_curve_figure(self, frac_screen_width=0.4, frac_screen_height=0.3):
        '''
        '''
        width = (frac_screen_width * self.screen_resolution.width()) / self.monitor_dpi
        height = (frac_screen_height * self.screen_resolution.height()) / self.monitor_dpi
        #fig = pl.figure(figsize=(width, height))
        fig = pl.figure(figsize=(9,4))
        ax1 = fig.add_subplot(221)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(223)
        ax4 = fig.add_subplot(224)
        ax4.set_axis_off()
        fig.subplots_adjust(right=0.98, left=0.1, bottom=0.15, top=0.93, wspace=0.22, hspace=0.41)
        ax1.set_ylabel('Current ($\mu$A)', fontsize=11)
        ax2.set_xlabel('Frequency(GHz)', fontsize=11)
        ax2.set_ylabel('Transmission', fontsize=11)
        ax3.set_xlabel('$V_{bias}$ ($\mu V$) / Normalized Resistance', fontsize=11)
        ax3.set_ylabel('Power ($pW$)', fontsize=11)
        return fig, (ax1, ax2, ax3, ax4)

    #################################################################################
    # IV Analysis
    ##################################################################################

    def dlc_reset_input(self):
        '''
        '''
        self.iv_1_path = None
        self.iv_2_path = None
        self.spectra_path = None
        self.differenced_load_curve_label.clear()
        self.spectra_plot_calibrated.clear()
        self.spectra_plot_raw_label.clear()
        self.iv_1_calibrated_plot_label.clear()
        self.iv_1_raw_plot_label.clear()
        self.iv_1_paneled_plot_label.clear()
        self.iv_2_calibrated_plot_label.clear()
        self.iv_2_raw_plot_label.clear()
        self.iv_2_paneled_plot_label.clear()
        self.dlc_configure_panel()

    def dlc_save_iv_1(self):
        '''
        '''
        temp_paneled_iv_1_path = os.path.join('temp_files', 'temp_paneled_iv_1.png')
        suggested_save_path = self.iv_1_path.replace('.txt', '.png').replace('raw', 'paneled')
        iv_1_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Select Data File', suggested_save_path, filter='.png')[0]
        if len(iv_1_path) > 0:
            shutil.copy(temp_paneled_iv_1_path, iv_1_path)

    def dlc_load_iv_1(self):
        '''
        '''
        if not self.iv_1_high_load_metadata_checkbox.isChecked:
            return None
        fig, ax = self.dlc_create_blank_fig(frac_screen_height=0.2)
        if self.iv_1_path is None:
            iv_1_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
            if len(iv_1_path) == 0:
                return None
            self.iv_1_path = iv_1_path
        else:
            iv_1_path = self.iv_1_path
        meta_data_path = iv_1_path.replace('txt', 'json')
        if os.path.exists(meta_data_path) and self.iv_1_high_load_metadata_checkbox.isChecked():
            with open(meta_data_path, 'r') as fh:
                meta_data = simplejson.load(fh)
            self.iv_1_data_clip_lo_lineedit.setText(meta_data['data_clip_lo_lineedit'])
            self.iv_1_data_clip_hi_lineedit.setText(meta_data['data_clip_hi_lineedit'])
            self.iv_1_fit_clip_lo_lineedit.setText(meta_data['fit_clip_lo_lineedit'])
            self.iv_1_fit_clip_hi_lineedit.setText(meta_data['fit_clip_hi_lineedit'])
            if 'x_correction_label' in meta_data:
                x_correction = meta_data['x_correction_label'].split(' ')[1]
            else:
                x_correction = '1e-5'
            self.iv_1_x_correction_lineedit.setText(x_correction)
            y_correction = self.squid_calibration_dict[meta_data['squid_select_combobox']]
            self.iv_1_y_correction_lineedit.setText(y_correction)
            self.iv_1_t_bath_lineedit.setText(meta_data['t_bath_lineedit'])
            self.iv_1_t_load_lineedit.setText(meta_data['t_load_lineedit'])
            self.sample_name_lineedit.setText(meta_data['sample_name_lineedit'])
            band_idx = self.band_select_combobox.findText(meta_data['sample_band_combobox'])
            self.band_select_combobox.setCurrentIndex(band_idx)
        data_clip_lo = float(self.iv_1_data_clip_lo_lineedit.text())
        data_clip_hi = float(self.iv_1_data_clip_hi_lineedit.text())
        # Calibration with Fit
        bias_voltage, squid_voltage = self.dlc_load_iv_data(iv_1_path)
        ax.plot(bias_voltage, squid_voltage, label='raw')
        temp_iv_1_path = os.path.join('temp_files', 'temp_iv_1.png')
        ax.set_xlabel('Bias Voltage Raw (V)')
        ax.set_ylabel('SQUID Outpu Voltage Raw (V)')
        ax.set_title('Raw IV data')
        fig.savefig(temp_iv_1_path)
        image_to_display = QtGui.QPixmap(temp_iv_1_path)
        #self.iv_1_raw_plot_label.setPixmap(image_to_display)
        pl.close('all')
        # Calibration with Fit
        fig, ax = self.dlc_create_blank_fig(frac_screen_height=0.2)
        self.calibrated_bias_voltage, self.calibrated_squid_current, fit_clip_lo, fit_clip_hi = self.dlc_calibrate_raw_data(bias_voltage, squid_voltage, iv=1)
        data_selector = np.logical_and(data_clip_lo < self.calibrated_bias_voltage, self.calibrated_bias_voltage < data_clip_hi)
        fit_selector = np.logical_and(fit_clip_lo < self.calibrated_bias_voltage, self.calibrated_bias_voltage < fit_clip_hi)
        ax.plot(self.calibrated_bias_voltage[data_selector], self.calibrated_squid_current[data_selector], label='raw')
        ax.plot(self.calibrated_bias_voltage[fit_selector], self.calibrated_squid_current[fit_selector], color='r', label='Fit')
        selector = np.logical_and(fit_clip_lo < self.calibrated_bias_voltage, self.calibrated_bias_voltage < fit_clip_hi)
        pl.legend()
        ax.set_xlabel('TES Bias Voltage (uV)')
        ax.set_ylabel('TES Current (uA)')
        ax.set_title('Calibrated IV data')
        temp_calibrated_iv_1_path = os.path.join('temp_files', 'temp_calibrated_iv_1.png')
        fig.savefig(temp_calibrated_iv_1_path)
        image_to_display = QtGui.QPixmap(temp_calibrated_iv_1_path)
        self.size = image_to_display.size()
        #self.iv_1_calibrated_plot_label.setPixmap(image_to_display)
        pl.close('all')
        sample_name = self.sample_name_lineedit.text()
        t_bath = self.iv_1_t_bath_lineedit.text()
        t_load = self.iv_1_t_load_lineedit.text()

        fig = self.mplc.mplc_create_iv_paneled_plot(
            name='xy_fig',
            left=0.18,
            right=0.95,
            bottom=0.25,
            top=0.8,
            frac_screen_height=0.4,
            frac_screen_width=0.4,
            hspace=0.9,
            wspace=0.25)
        fig.canvas = FigureCanvas(fig)
        fig = self.ivlib_plot_all_curves(fig, self.calibrated_bias_voltage, self.calibrated_squid_current, bolo_current_stds=None,
                                         fit_clip=(fit_clip_lo, fit_clip_hi), plot_clip=(data_clip_lo, data_clip_hi),
                                         sample_name=sample_name, t_bath=t_bath, t_load=t_load)
        temp_paneled_iv_1_path = os.path.join('temp_files', 'temp_paneled_iv_1.png')
        fig.savefig(temp_paneled_iv_1_path)
        image_to_display = QtGui.QPixmap(temp_paneled_iv_1_path)
        image_to_display = image_to_display.scaled(self.size.width(), int(1.2 * self.size.height()))
        self.iv_1_paneled_plot_label.setPixmap(image_to_display)
        pl.close('all')
        if self.spectra_path is not None and self.iv_2_path is not None:
            self.dlc_difference_load_curves()
        self.iv_1_high_load_metadata_checkbox.setChecked(False)

    def dlc_save_iv_2(self):
        '''
        '''
        temp_paneled_iv_2_path = os.path.join('temp_files', 'temp_paneled_iv_2.png')
        suggested_save_path = self.iv_2_path.replace('.txt', '.png').replace('raw', 'paneled')
        iv_2_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Select Data File', suggested_save_path, filter='.png')[0]
        if len(iv_2_path) > 0:
            shutil.copy(temp_paneled_iv_2_path, iv_2_path)

    def dlc_load_iv_2(self):
        '''
        '''
        if self.iv_2_path is None:
            iv_2_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
            if len(iv_2_path) == 0:
                return None
            self.iv_2_path = iv_2_path
        else:
            iv_2_path = self.iv_2_path
        meta_data_path = iv_2_path.replace('txt', 'json')
        if os.path.exists(meta_data_path) and self.iv_2_high_load_metadata_checkbox.isChecked():
            with open(meta_data_path, 'r') as fh:
                meta_data = simplejson.load(fh)
            self.iv_2_data_clip_lo_lineedit.setText(meta_data['data_clip_lo_lineedit'])
            self.iv_2_data_clip_hi_lineedit.setText(meta_data['data_clip_hi_lineedit'])
            self.iv_2_fit_clip_lo_lineedit.setText(meta_data['fit_clip_lo_lineedit'])
            self.iv_2_fit_clip_hi_lineedit.setText(meta_data['fit_clip_hi_lineedit'])
            if 'x_correction_label' in meta_data:
                x_correction = meta_data['x_correction_label'].split(' ')[1]
            else:
                x_correction = '1e-5'
            self.iv_2_x_correction_lineedit.setText(x_correction)
            y_correction = self.squid_calibration_dict[meta_data['squid_select_combobox']]
            self.iv_2_y_correction_lineedit.setText(y_correction)
            self.iv_2_t_bath_lineedit.setText(meta_data['t_bath_lineedit'])
            data_clip_lo = float(self.iv_2_data_clip_lo_lineedit.text())
            data_clip_hi = float(self.iv_2_data_clip_hi_lineedit.text())
            fig, ax = self.dlc_create_blank_fig(frac_screen_height=0.2)
            self.iv_2_t_load_lineedit.setText(meta_data['t_load_lineedit'])
            self.sample_name_lineedit.setText(meta_data['sample_name_lineedit'])
        # Calibration with Fit
        data_clip_lo = float(self.iv_2_data_clip_lo_lineedit.text())
        data_clip_hi = float(self.iv_2_data_clip_hi_lineedit.text())
        fig, ax = self.dlc_create_blank_fig(frac_screen_height=0.2)
        bias_voltage, squid_voltage = self.dlc_load_iv_data(iv_2_path)
        ax.plot(bias_voltage, squid_voltage, label='raw')
        temp_iv_2_path = os.path.join('temp_files', 'temp_iv_2.png')
        ax.set_xlabel('Bias Voltage Raw (V)')
        ax.set_ylabel('SQUID Outpu Voltage Raw (V)')
        ax.set_title('Raw IV data')
        fig.savefig(temp_iv_2_path)
        image_to_display = QtGui.QPixmap(temp_iv_2_path)
        #self.iv_2_raw_plot_label.setPixmap(image_to_display)
        pl.close('all')
        # Calibration with Fit
        fig, ax = self.dlc_create_blank_fig(frac_screen_height=0.2)
        self.calibrated_bias_voltage, self.calibrated_squid_current, fit_clip_lo, fit_clip_hi = self.dlc_calibrate_raw_data(bias_voltage, squid_voltage, iv=2)
        data_selector = np.logical_and(data_clip_lo < self.calibrated_bias_voltage, self.calibrated_bias_voltage < data_clip_hi)
        fit_selector = np.logical_and(fit_clip_lo < self.calibrated_bias_voltage, self.calibrated_bias_voltage < fit_clip_hi)
        ax.plot(self.calibrated_bias_voltage[data_selector], self.calibrated_squid_current[data_selector], label='raw')
        ax.plot(self.calibrated_bias_voltage[fit_selector], self.calibrated_squid_current[fit_selector], color='r', label='Fit')
        pl.legend()
        ax.set_xlabel('TES Bias Voltage (uV)')
        ax.set_ylabel('TES Current (uA)')
        ax.set_title('Calibrated IV data')
        temp_calibrated_iv_2_path = os.path.join('temp_files', 'temp_calibrated_iv_2.png')
        fig.savefig(temp_calibrated_iv_2_path)
        image_to_display = QtGui.QPixmap(temp_calibrated_iv_2_path)
        self.size = image_to_display.size()
        #self.iv_2_calibrated_plot_label.setPixmap(image_to_display)
        pl.close('all')
        sample_name = self.sample_name_lineedit.text()
        t_bath = self.iv_2_t_bath_lineedit.text()
        t_load = self.iv_2_t_load_lineedit.text()

        fig = self.mplc.mplc_create_iv_paneled_plot(
            name='xy_fig',
            left=0.18,
            right=0.95,
            bottom=0.25,
            top=0.8,
            frac_screen_height=0.4,
            frac_screen_width=0.4,
            hspace=0.9,
            wspace=0.25)
        fig.canvas = FigureCanvas(fig)
        fig = self.ivlib_plot_all_curves(fig, self.calibrated_bias_voltage, self.calibrated_squid_current, bolo_current_stds=None,
                                         fit_clip=(fit_clip_lo, fit_clip_hi), plot_clip=(data_clip_lo, data_clip_hi),
                                         sample_name=sample_name, t_bath=t_bath, t_load=t_load)
        temp_paneled_iv_2_path = os.path.join('temp_files', 'temp_paneled_iv_2.png')
        fig.savefig(temp_paneled_iv_2_path)
        image_to_display = QtGui.QPixmap(temp_paneled_iv_2_path)
        image_to_display = image_to_display.scaled(self.size.width(), int(1.2 * self.size.height()))
        self.iv_2_paneled_plot_label.setPixmap(image_to_display)
        pl.close('all')
        if self.spectra_path is not None and self.iv_1_path is not None:
            self.dlc_difference_load_curves()
        self.iv_2_high_load_metadata_checkbox.setChecked(False)

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
        smoothing_factor = float(self.smoothing_factor_lineedit.text())
        t_source_high = float(self.iv_1_t_load_lineedit.text())
        t_source_low = float(self.iv_2_t_load_lineedit.text())
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
        meta_data_path = spectra_path.replace('fft', 'json')
        if os.path.exists(meta_data_path):
            with open(meta_data_path, 'r') as fh:
                meta_data = simplejson.load(fh)
            self.sample_name_lineedit.setText(meta_data['sample_name_lineedit'])
        fig, ax = self.dlc_create_blank_fig(left=0.1, frac_screen_width=0.4, frac_screen_height=0.2)
        fft_frequency_vector, normalized_fft_vector = self.dlc_load_spectra_data(spectra_path)
        #print(fft_frequency_vector)
        #if np.max(fft_frequency_vector) > 1e6:
            #ax.plot(fft_frequency_vector * 1e-9, normalized_fft_vector, label='Raw Data')
        #else:
            #ax.plot(fft_frequency_vector, normalized_fft_vector, label='Raw Data')
        print(band)
        if len(band) > 0 and False:
            fft_frequency_vector_simulated, fft_vector_simulated = self.ftsy_load_simulated_band(data_clip_lo, data_clip_hi, band)
            print(fft_frequency_vector_simulated)
            ax.plot(fft_frequency_vector_simulated, fft_vector_simulated, label='HFSS Data')
        ax.set_xlabel('Frequency (GHz)')
        ax.set_ylabel('Normalized\nTransmission')
        spectra_png_save_path = os.path.join('temp_files', 'temp_spectra.png')
        pl.legend()
        fig.savefig(spectra_png_save_path)
        image_to_display = QtGui.QPixmap(spectra_png_save_path)
        #self.spectra_plot_raw_label.setPixmap(image_to_display)
        pl.close('all')
        fig, ax = self.dlc_create_blank_fig(left=0.1, frac_screen_width=0.4, frac_screen_height=0.2)
        fft_frequency_vector_processed, normalized_fft_vector_processed = self.dlc_load_spectra_data(spectra_path)
        print(data_clip_lo, data_clip_hi)
        delta_power, integrated_bandwidth = self.ftsy_compute_delta_power_and_bandwidth_at_window(fft_frequency_vector_processed, normalized_fft_vector_processed,
                                                                                                  data_clip_lo=data_clip_lo, data_clip_hi=data_clip_hi,
                                                                                                  t_source_low=t_source_low, t_source_high=t_source_high)
        label=None
        if self.iv_1_path is not None and self.iv_2_path is not None:
            label='$\Delta(P)$ {0:.2f} pW\nBW {1:.2f} GHz '.format(delta_power * 1e12, integrated_bandwidth * 1e-9)
        if smoothing_factor > 0:
            normalized_fft_vector_processed = self.ftsy_running_mean(normalized_fft_vector_processed, smoothing_factor=smoothing_factor)
        if np.max(fft_frequency_vector_processed) > 1e6:
            ax.plot(fft_frequency_vector_processed * 1e-9, normalized_fft_vector_processed, label=label)
        else:
            ax.plot(fft_frequency_vector_processed, normalized_fft_vector_processed, label=label)
        #ax.plot(fft_frequency_vector_simulated, fft_vector_simulated, label='HFSS Data')
        ax = self.dlc_plot_optical_elements(ax)
        ax.set_xlabel('Frequency (GHz)')
        ax.set_ylabel('Normalized\nTransmission')
        #ax.set_xlim((data_clip_lo, data_clip_hi))
        spectra_png_save_path = os.path.join('temp_files', 'temp_spectra.png')
        pl.legend()
        fig.savefig(spectra_png_save_path)
        image_to_display = QtGui.QPixmap(spectra_png_save_path)
        self.spectra_size = image_to_display.size()
        #self.spectra_plot_calibrated.setPixmap(image_to_display)
        pl.close('all')
        if self.spectra_path is not None and self.iv_1_path is not None and self.iv_2_path is not None:
            self.dlc_difference_load_curves()

    def dlc_plot_optical_elements(self, ax):
        '''
        '''
        data_clip_lo = float(self.spectra_data_clip_lo_lineedit.text()) * 1e9
        data_clip_hi = float(self.spectra_data_clip_hi_lineedit.text()) * 1e9
        for optical_element in self.optical_elements_dict:
            active = self.optical_elements_dict[optical_element]['Active']
            path = self.optical_elements_dict[optical_element]['Path']
            if active:
                element_frequency_vector, element_transmission_vector = self.ftsy_load_optical_element_response(path)
                selector = np.logical_and(data_clip_lo < np.asarray(element_frequency_vector), np.asarray(element_frequency_vector) < data_clip_hi)
                ax.plot(np.asarray(element_frequency_vector)[selector] * 1e-9, np.asarray(element_transmission_vector)[selector], label=optical_element)
        return ax


    def dlc_load_spectra_data(self, data_path):
        '''
        '''
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
        normalized_transmission_vector = transmission_vector / np.max(transmission_vector)
        return frequency_vector, normalized_transmission_vector

    ####################
    # Plotting
    ####################

    def dlc_plot_all_curves2(self, bolo_voltage_bias, bolo_current, iv=1, stds=None, label='', fit_clip=None, plot_clip=None,
                             show_plot=False, title='', pturn=True, frac_screen_width=0.3, frac_screen_height=0.35,
                             left=0.1, right=0.98, top=0.9, bottom=0.13, multiple_axes=False):
        '''
        This function creates an x-y scatter plot with v_bolo on the x-axis and
        bolo curent on the y-axis.  The resistance value is reported as text annotation
        Inputs:
            bolo_votlage_bias: bolo_voltage in Volts
            bolo_current: bolo_current in Amps
        '''
        width = (frac_screen_width * self.screen_resolution.width()) / self.monitor_dpi
        height = (frac_screen_height * self.screen_resolution.height()) / self.monitor_dpi
        fig = pl.figure(figsize=(9, 4))
        fig.subplots_adjust(left=left, right=right, bottom=bottom, hspace=0.8)
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
