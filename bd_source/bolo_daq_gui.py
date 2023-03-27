import sys
import nidaqmx
import chardet
import imageio
import smtplib
import serial
import simplejson
import os
import subprocess
import shutil
import time
import datetime
import numpy as np
import time
import threading

from PyPDF2 import PdfFileMerger
from pprint import pprint, pformat
from datetime import datetime
from copy import copy
from PyQt5 import QtCore, QtGui, QtWidgets

# Settings 
from bd_settings.bd_global_settings import settings

# Libraries
from bd_lib.bolo_daq import BoloDAQ
from bd_lib.bolo_serial import BoloSerial
from bd_lib.fourier_transform_spectroscopy import FourierTransformSpectroscopy

# Widgets
from bd_tools.com_port_utility import ComPortUtility
from bd_tools.configure_ni_daq import ConfigureNIDAQ
from bd_tools.configure_bolo_daq_gui import ConfigureBoloDAQGui
from bd_tools.iv_collector import IVCollector
from bd_tools.rt_collector import RTCollector
from bd_tools.lakeshore_372 import LakeShore372

from bd_tools.cosmic_rays import CosmicRays
from bd_tools.cosmic_ray_viewer import CosmicRayViewer
from bd_tools.beam_mapper import BeamMapper
from bd_tools.fridge_cycle import FridgeCycle
from bd_tools.difference_load_curves import DifferenceLoadCurves
from bd_tools.data_plotter import DataPlotter
from bd_tools.wafer_yield import WaferYield
from bd_tools.histogram_plotter import HistogramPlotter
from bd_tools.time_constant import TimeConstant
from bd_tools.agilent_e3634a import AgilentE3634A
from bd_tools.agilent_agc100 import AgilentAGC100
from bd_tools.noise_analyzer import NoiseAnalyzer
from bd_tools.dr_p_and_t_plotter import DilutionRefridgeratorPressureTemperatureLogPlotter
from bd_tools.hewlett_packard_34401a import HewlettPackard34401A
from bd_tools.configure_stepper_motor import ConfigureStepperMotor
from bd_tools.configure_sigma_koki import ConfigureSigmaKoki
from bd_tools.polarization_efficiency import PolarizationEfficiency
from bd_tools.fourier_transform_spectrometer import FourierTransformSpectrometer
from bd_tools.stanford_research_systems_sr830_dsp import StanfordResearchSystemsSR830DSP

# Gui Biulder
from GuiBuilder.gui_builder import GuiBuilder


class BoloDAQGui(QtWidgets.QMainWindow, GuiBuilder):

    def __init__(self, screen_resolution, qt_app):
        '''
        '''
        super(BoloDAQGui, self).__init__()
        self.qt_app = qt_app
        self.__apply_settings__(settings)
        self.screen_resolution = screen_resolution
        grid = QtWidgets.QGridLayout()
        self.splash_screen = QtWidgets.QSplashScreen()
        self.splash_screen_image_path = os.path.join('bd_settings', 'BoloPic.JPG')
        q_splash_image = QtGui.QPixmap(self.splash_screen_image_path)
        x_scale = int(self.screen_resolution.width() * 0.4)
        y_scale = int(self.screen_resolution.height() * 0.5)
        q_splash_image = q_splash_image.scaled(x_scale, y_scale, QtCore.Qt.KeepAspectRatio)
        self.splash_screen.setPixmap(q_splash_image)
        self.splash_screen.show()
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setWhatsThis('cw_panel')
        self.central_widget.setLayout(grid)
        self.setCentralWidget(self.central_widget)
        self.grid = self.central_widget.layout()
        grid = QtWidgets.QGridLayout()
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setWhatsThis('cw_panel')
        self.central_widget.setLayout(grid)
        self.setCentralWidget(self.central_widget)
        self.tool_and_menu_bar_json_path = os.path.join('bd_settings', 'tool_and_menu_bars.json')
        self.gb_setup_menu_and_tool_bars(self.tool_and_menu_bar_json_path, icon_size=25)
        self.selected_files = []
        self.user_desktop_path = os.path.expanduser('~')
        self.monitor_dpi = 92
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.login = os.getlogin()
        if self.login == 'BoloTester':
            self.data_folder = os.path.join('Data', '{0}'.format(self.today_str))
            self.dewar = '576'
        elif self.login in ['Bluefors_PC']:
            self.data_folder = os.path.join('Data', '{0}'.format(self.today_str))
            self.dewar = 'BlueForsDR1'
            self.samples_com_port = 'COM6'
            self.housekeeping_com_port = 'COM4'
        elif self.login in ['BolometerTesterDR']:
            self.data_folder = os.path.join('D:', 'Daily_Data', '{0}'.format(self.today_str))
            self.dewar = 'BlueForsDR1'
            self.samples_com_port = 'COM3'
            self.housekeeping_com_port = 'COM5'
        else:
            self.gb_quick_message('Computer not recgonized', msg_type='Warning')
            os._exit(0)
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        self.bd_setup_status_bar()
        self.squid_calibration_dict_path = os.path.join('bd_settings', 'squids_settings.json')
        self.com_port_dict_path = os.path.join('bd_settings', 'comports_settings.json')
        self.bd_load_squid_settings()
        self.bd_load_com_port_settings()
        self.com_port_utility_widget = ComPortUtility(self.splash_screen, self.screen_resolution, self.monitor_dpi)
        self.bd_get_daq_settings()
        self.splash_screen.close()
        self.move(0, 0)
        self.show()
        getattr(self, 'action_Bolo_DAQ_Settings').trigger()
        #if not hasattr(self, 'configure_ni_daq_widget'):
            #self.configure_ni_daq_widget = ConfigureNIDAQ(self.daq_settings, self.status_bar)

    ##################################################################################
    #### Start up Tasks ##############################################################
    ##################################################################################

    def __apply_settings__(self, settings):
        '''
        '''
        for setting in dir(settings):
            if '__' not in setting:
                setattr(self, setting, getattr(settings, setting))

    def bd_load_squid_settings(self):
        '''
        '''
        with open(self.squid_calibration_dict_path, 'r') as fh:
            self.squid_calibration_dict = simplejson.load(fh )

    def bd_load_com_port_settings(self):
        '''
        '''
        with open(self.com_port_dict_path, 'r') as fh:
            self.com_ports_dict = simplejson.load(fh )

    ##################################################################################
    #### Global Gui     ##############################################################
    ##################################################################################

    def bd_setup_status_bar(self):
        '''
        '''
        custom_widgets = []
        q_progress_bar = QtWidgets.QProgressBar(self)
        q_progress_bar.setValue(0)
        q_progress_bar.setAlignment(QtCore.Qt.AlignBottom)
        q_progress_bar.setFixedWidth(150)
        custom_widgets.append(q_progress_bar)
        self.progress_bar = q_progress_bar
        permanant_messages = ['BoloDAQ Benjamin Grey Westbrook 2020']
        self.gb_add_status_bar(
            permanant_messages=permanant_messages,
            add_saved=True,
            custom_widgets=custom_widgets
            )
        self.status_bar.progress_bar = self.progress_bar

    def bd_close_main(self):
        '''
        '''
        self.close()
        os._exit(0)

    ##################################################################################
    #### Common DAQ     ##############################################################
    ##################################################################################

    def bd_get_daq_settings(self):
        '''
        '''
        self.bolo_daq= BoloDAQ()
        self.daq_settings = self.bolo_daq.initialize_daqs()

    #################################################
    # Logging and File Management
    #################################################

    def bd_create_log(self):
        date_str = datetime.strftime(datetime.now(), '%Y_%m_%d')
        log_file_name = 'Data_Log_{0}.txt'.format(date_str)
        self.data_log_path = os.path.join(self.data_folder, log_file_name)
        if not os.path.exists(self.data_log_path):
            header = 'Data log for {0}\n'.format(date_str)
            with open(self.data_log_path, 'w') as data_log_handle:
                data_log_handle.write(header)

    def bd_update_log(self):
        if not hasattr(self, 'data_log_path'):
            self.bd_create_log()
        if hasattr(self, 'raw_data_path') and self.raw_data_path is not None:
            temp_log_file_name = 'temp_log.txt'
            notes = self.gb_quick_info_gather()
            response = self.gb_quick_message('Use Data in Analysis?', add_yes=True, add_no=True)
            if response == QtWidgets.QMessageBox.Yes:
                self.bd_copy_file_to_analysis_folder()
            with open(temp_log_file_name, 'w') as temp_log_handle:
                with open(self.data_log_path, 'r') as log_handle:
                    for line in log_handle.readlines():
                        temp_log_handle.write(line)
                    new_line = '{0}\t{1}\n'.format(self.raw_data_path[0], notes)
                    temp_log_handle.write(new_line)
            shutil.copy(temp_log_file_name, self.data_log_path)

    def bd_copy_file_to_analysis_folder(self):
        for_analysis_folder = os.path.join(self.data_folder, 'For_Analysis')
        if not os.path.exists(for_analysis_folder):
            os.makedirs(for_analysis_folder)
        data_path = self.raw_data_path[0]
        if '.if' in data_path:
            data_path = data_path.replace('.if', '.fft')
        shutil.copy(data_path, for_analysis_folder)

    #################################################
    #################################################
    # Utility WIDGETS 
    #################################################
    #################################################

    #################################################
    # Fridge Cycle
    #################################################

    def bd_fridge_cycle(self):
        '''
        '''

        dialog = 'Select the comport for the Agilent E3634A'
        com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM19'])
        if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
            serial_com = BoloSerial(com_port, device='Agilent E3634A', splash_screen=self.status_bar)
            setattr(self, 'ser_{0}'.format(com_port), serial_com)
            if not hasattr(self, 'agilent_e3634a_widget'):
                self.agilent_e3634a_widget = AgilentE3634A(serial_com, self.status_bar, self.screen_resolution, self.monitor_dpi)
        dialog = 'Select the comport for the HP 34401A'
        com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM3'])
        if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
            serial_com = BoloSerial(com_port, device='HP 34401A', splash_screen=self.status_bar)
            setattr(self, 'ser_{0}'.format(com_port), serial_com)
            if not hasattr(self, 'hp_34401a_widget'):
                self.hp_34401a_widget = HewlettPackard34401A(serial_com, com_port, self.status_bar, self.screen_resolution, self.monitor_dpi)
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching Fridge Cycle')
        QtWidgets.QApplication.processEvents()
        if not hasattr(self, 'fridge_cycle_widget'):
            self.fridge_cycle_widget = FridgeCycle(self.status_bar, self.agilent_e3634a_widget, self.hp_34401a_widget)
        self.central_widget.layout().addWidget(self.fridge_cycle_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Fridge Cycle')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

    #################################################
    # Configure DAQ
    #################################################

    def bd_configure_ni_daq(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching Configure National Intruments DAQ')
        QtWidgets.QApplication.processEvents()
        self.bd_get_daq_settings()
        if not hasattr(self, 'configure_ni_daq_widget'):
            self.configure_ni_daq_widget = ConfigureNIDAQ(self.daq_settings, self.status_bar)
        self.central_widget.layout().addWidget(self.configure_ni_daq_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Configure National Intruments DAQ')
        QtWidgets.QApplication.processEvents()
        self.showNormal()

    #################################################
    # Cosmic Ray Viewer 
    #################################################

    def bd_cosmic_ray_viewer(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching Cosmic Ray Viewer Plotter')
        QtWidgets.QApplication.processEvents()
        if not hasattr(self, 'cosmic_ray_viewer_widget'):
            self.cosmic_ray_viewer_widget = CosmicRayViewer(self.status_bar, self.screen_resolution, self.monitor_dpi, self.data_folder)
        self.central_widget.layout().addWidget(self.cosmic_ray_viewer_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Cosmic Ray View')
        QtWidgets.QApplication.processEvents()
        self.showNormal()

    #################################################
    # Wafer Yield 
    #################################################

    def bd_wafer_yield(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching Wafer Yield')
        QtWidgets.QApplication.processEvents()
        if not hasattr(self, 'wafer_yield_widget'):
            self.wafer_yield_widget = WaferYield(self.status_bar, self.screen_resolution, self.monitor_dpi)
        self.central_widget.layout().addWidget(self.wafer_yield_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Wafer Yield Widget')
        QtWidgets.QApplication.processEvents()
        self.showNormal()

    #################################################
    # Histogram Plotter 
    #################################################

    def bd_histogram_plotter(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching Histogram Plotter')
        QtWidgets.QApplication.processEvents()
        if not hasattr(self, 'histogram_plotter'):
            self.histogram_plotter_widget = HistogramPlotter(self.status_bar, self.screen_resolution, self.monitor_dpi, self.data_folder)
        self.central_widget.layout().addWidget(self.histogram_plotter_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Histogram Plotter')
        QtWidgets.QApplication.processEvents()
        self.showNormal()

    #################################################
    # Data Plotter 
    #################################################

    def bd_data_plotter(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching Data Plotter')
        QtWidgets.QApplication.processEvents()
        if not hasattr(self, 'data_plotter_widget'):
            self.data_plotter_widget = DataPlotter(self.status_bar, self.screen_resolution, self.monitor_dpi, self.data_folder)
        self.central_widget.layout().addWidget(self.data_plotter_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Data Plotter')
        QtWidgets.QApplication.processEvents()
        self.showNormal()

    #################################################
    # Configure the GUI
    #################################################

    def bd_configure_bolo_daq_gui(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching Bolo DAQ GUI Settings')
        QtWidgets.QApplication.processEvents()
        if not hasattr(self, 'configure_bolo_daq_gui_widget'):
            self.configure_bolo_daq_gui_widget = ConfigureBoloDAQGui(self.daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi, self.login)
        self.central_widget.layout().addWidget(self.configure_bolo_daq_gui_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Bolo DAQ GUI Settings')
        QtWidgets.QApplication.processEvents()
        self.resize(self.sizeHint())

    #################################################
    #################################################
    # Instrument Control 
    #################################################
    #################################################

    #################################################
    # Lock in SRS SR830 DSP
    #################################################

    def bd_stanford_research_systems_sr830_dsp(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching SRS SR830 Control')
        QtWidgets.QApplication.processEvents()
        dialog = 'Select the comport for the SRS SR830'
        com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM10'])
        if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
            serial_com = BoloSerial(com_port, device='SRS_SR830_DSP', splash_screen=self.status_bar)
            setattr(self, 'ser_{0}'.format(com_port), serial_com)
            if not hasattr(self, 'srs_sr830dsp_widget'):
                self.srs_sr830dsp_widget = StanfordResearchSystemsSR830DSP(serial_com, com_port, self.status_bar, self.screen_resolution, self.monitor_dpi)
            self.srs_sr830dsp_widget.srs_update_serial_com(serial_com)
            self.central_widget.layout().addWidget(self.srs_sr830dsp_widget, 0, 0, 1, 1)
        elif okPressed:
            self.central_widget.layout().addWidget(self.srs_sr830dsp_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('SRS SR830 Control')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

    #################################################
    # Comport Utility
    #################################################

    def bd_com_port_utility(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Setting up COM port utility')
        QtWidgets.QApplication.processEvents()
        if not hasattr(self, 'com_port_utility_widget'):
            self.com_port_utility_widget = ComPortUtility(self.status_bar, self.screen_resolution, self.monitor_dpi)
        self.central_widget.layout().addWidget(self.com_port_utility_widget, 0, 0, 1, 1)
        self.com_port_utility_widget.cpu_change_status_bar(self.status_bar)
        self.status_bar.showMessage('COM port utility')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

    #################################################
    # Hewlett Packard 34401A
    #################################################

    def bd_hewlett_packard_34401a(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Setting up Hewlett Packard 34401A Controller')
        QtWidgets.QApplication.processEvents()
        dialog = 'Select the comport for the HP 34401A'
        okPressed = True
        com_port = 'COM20'
        okPressed = True
        if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
            com_port = 'COM19'
            serial_com_hp1 = BoloSerial(com_port, device='HewlettPackard34401A', splash_screen=self.status_bar)
            setattr(self, 'ser_{0}'.format(com_port), serial_com_hp1)
            com_port = 'COM20'
            serial_com_hp2 = BoloSerial(com_port, device='HewlettPackard34401A', splash_screen=self.status_bar)
            setattr(self, 'ser_{0}'.format(com_port), serial_com_hp2)
            if not hasattr(self, 'hp_34401a_widget'):
                self.hp_34401a_widget = HewlettPackard34401A(serial_com_hp1, serial_com_hp2, self.status_bar, self.screen_resolution, self.monitor_dpi)
            self.central_widget.layout().addWidget(self.hp_34401a_widget, 0, 0, 1, 1)
        elif okPressed:
            self.central_widget.layout().addWidget(self.hp_34401a_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Hewlett Packard 34401A Controller')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

    #################################################
    # Pressure gague Agilent AGC 100
    #################################################

    def bd_agilent_agc100(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        dialog = 'Select the comport for the Agilent E3634A'
        #com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM5'])
        com_port = 'COM5'
        okPressed = True
        if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
            serial_com = BoloSerial(com_port, device='Agilent_AGC100', splash_screen=self.status_bar)
            setattr(self, 'ser_{0}'.format(com_port), serial_com)
            if not hasattr(self, 'agilent_agc100_widget'):
                self.agilent_agc100_widget = AgilentAGC100(serial_com, self.status_bar, self.screen_resolution, self.monitor_dpi)
            self.central_widget.layout().addWidget(self.agilent_agc100_widget, 0, 0, 1, 1)
        elif okPressed:
            self.central_widget.layout().addWidget(self.agilent_agc100_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Agilent AGC100 Pressure Gauge')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

    #################################################
    # Power Supply Agilent E3634A
    #################################################

    def bd_agilent_e3634a(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        dialog = 'Select the comport for the Agilent E3634A'
        com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM19'])
        if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
            serial_com = BoloSerial(com_port, device='Agilent_E3634A', splash_screen=self.status_bar)
            setattr(self, 'ser_{0}'.format(com_port), serial_com)
            if not hasattr(self, 'agilent_e3634a_widget'):
                self.agilent_e3634a_widget = AgilentE3634A(serial_com, self.status_bar, self.screen_resolution, self.monitor_dpi)
            self.central_widget.layout().addWidget(self.agilent_e3634a_widget, 0, 0, 1, 1)
        elif okPressed:
            serial_com = getattr(self, 'ser_{0}'.format(com_port))
            self.agilent_e3634a_widget.ae_update_serial_com(serial_com)
            self.central_widget.layout().addWidget(self.agilent_e3634a_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Agilent E3634A Controller')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

    #################################################
    # Lakeshore
    #################################################

    def bd_lakeshore_372(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Setting Up Lakeshore 372 Controller')
        QtWidgets.QApplication.processEvents()
        dialog = 'Select the comport for the Lakeshore'
        coms = [self.samples_com_port, self.housekeeping_com_port]
        com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=coms)
        if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
            serial_com = BoloSerial(com_port, device='Model372', splash_screen=self.status_bar)
            setattr(self, 'ser_{0}'.format(com_port), serial_com)
            if not hasattr(self, 'ls_372_widget'):
                ls_372_widget = LakeShore372(serial_com, com_port, self.status_bar)
                setattr(self, 'ls_372_widget_{0}'.format(com_port), ls_372_widget)
            self.central_widget.layout().addWidget(ls_372_widget, 0, 0, 1, 1)
        elif okPressed:
            serial_com = getattr(self, 'ser_{0}'.format(com_port))
            ls_372_widget = getattr(self, 'ls_372_widget_{0}'.format(com_port))
            ls_372_widget.ls372_update_serial_com(serial_com)
            self.central_widget.layout().addWidget(ls_372_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Lakeshore 372 Controller')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

    #################################################
    #################################################
    # Data Taking Widgets
    #################################################
    #################################################

    #################################################
    # IV Curves 
    #################################################

    def bd_iv_curves(self):
        '''
        Opens the panel and sets som defaults
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Loading IV Curves')
        QtWidgets.QApplication.processEvents()
        self.daq_settings = self.bolo_daq.initialize_daqs()
        if self.dewar == '576':
            ls_372_widget = None
        elif self.dewar =='BlueForsDR1':
            com_port = self.com_ports_dict[self.login]['Housekeeping Lakeshore']
            if not hasattr(self, 'ser_{0}'.format(com_port)):
                try:
                    serial_com = BoloSerial(com_port, device='Model372', splash_screen=self.status_bar)
                except:
                    response = self.gb_quick_message('Com port in use... Launch in data analysis mode?', add_yes=True, add_no=True)
                    if response == QtWidgets.QMessageBox.Yes:
                        serial_com = None
                    else:
                        return None
                setattr(self, 'ser_{0}'.format(com_port), serial_com)
                if not hasattr(self, 'ls_372_widget_{0}'.format(com_port)) and serial_com is not None:
                    ls_372_widget = LakeShore372(serial_com, com_port, self.status_bar)
                else:
                    ls_372_widget = None
                setattr(self, 'ls_372_widget_{0}'.format(com_port), ls_372_widget)
            else:
                ls_372_widget = getattr(self, 'ls_372_widget_{0}'.format(com_port))
        if not hasattr(self, 'ivc_widget'):
            self.ivc_widget = IVCollector(self.daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi, self.data_folder, self.dewar, ls_372_widget)
        self.ivc_widget.ivc_update_samples()
        self.ivc_widget.ivc_update_daq_settings(self.daq_settings)
        self.central_widget.layout().addWidget(self.ivc_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('IV Curves')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint().width(), self.minimumSizeHint().height())

    #################################################
    # RT Cruves
    #################################################

    def bd_rt_curves(self):
        '''
        Opens the panel and sets som defaults
        '''
        okPressed = True
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Loading RT Curves')
        QtWidgets.QApplication.processEvents()
        dialog = 'Select the comport for the Temperature Lakeshore'
        if self.dewar == '576':
            ls_372_samples_widget = None
            ls_372_temp_widget = None
        elif self.dewar == 'BlueForsDR1':
            com_port = self.com_ports_dict[self.login]['Housekeeping Lakeshore']
            if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
                try:
                    serial_com = BoloSerial(com_port, device='Model372', splash_screen=self.status_bar)
                except:
                    response = self.gb_quick_message('Com port in use... Launch in data analysis mode?', add_yes=True, add_no=True)
                    if response == QtWidgets.QMessageBox.Yes:
                        serial_com = None
                    else:
                        return None
                setattr(self, 'ser_{0}'.format(com_port), serial_com)
                if not hasattr(self, 'ls_372_widget_{0}'.format(com_port)) and serial_com is not None:
                    ls_372_temp_widget = LakeShore372(serial_com, com_port, self.status_bar)
                else:
                    ls_372_temp_widget = None
                setattr(self, 'ls_372_widget_{0}'.format(com_port), ls_372_temp_widget)
            com_port = self.com_ports_dict[self.login]['Samples Lakeshore']
            if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
                try:
                    serial_com = BoloSerial(com_port, device='Model372', splash_screen=self.status_bar)
                except:
                    response = self.gb_quick_message('Com port in use... Launch in data analysis mode?', add_yes=True, add_no=True)
                    if response == QtWidgets.QMessageBox.Yes:
                        serial_com = None
                    else:
                        return None
                setattr(self, 'ser_{0}'.format(com_port), serial_com)
                if not hasattr(self, 'ls_372_widget_{0}'.format(com_port)) and serial_com is not None:
                    ls_372_samples_widget = LakeShore372(serial_com, com_port, self.status_bar)
                else:
                    ls_372_samples_widget = None
                setattr(self, 'ls_372_widget_{0}'.format(com_port), ls_372_samples_widget)
        if not hasattr(self, 'rtc_widget'):
            if self.login == 'Bluefors_PC':
                ls_372_samples_widget = getattr(self, 'ls_372_widget_COM{0}'.format(6))
                ls_372_temp_widget = getattr(self, 'ls_372_widget_COM{0}'.format(4))
            elif self.login == 'BolometerTesterDR':
                ls_372_samples_widget = getattr(self, 'ls_372_widget_COM{0}'.format(3))
                ls_372_temp_widget = getattr(self, 'ls_372_widget_COM{0}'.format(5))
            self.rtc_widget = RTCollector(self.daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi, ls_372_temp_widget, ls_372_samples_widget, self.data_folder)
        else:
            self.daq_settings = self.bolo_daq.initialize_daqs()
            self.rtc_widget.rtc_update_samples()
        self.central_widget.layout().addWidget(self.rtc_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('RT Curves')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())


    #################################################
    # Difference Load Curves 
    #################################################

    def bd_difference_load_curves(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching Difference Load Curves')
        QtWidgets.QApplication.processEvents()
        if not hasattr(self, 'difference_load_curves_widget'):
            self.difference_load_curves_widget = DifferenceLoadCurves(self.daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi, self.data_folder)
        self.central_widget.layout().addWidget(self.difference_load_curves_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Difference Load Curves')
        QtWidgets.QApplication.processEvents()

    #################################################
    # Plot DR Logs 
    #################################################

    def bd_dr_p_and_t_plotter(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        if not hasattr(self, 'dr_p_and_t_plotter_widget'):
            dr_p_and_t_plotter_widget = DilutionRefridgeratorPressureTemperatureLogPlotter(self.status_bar, self.screen_resolution, self.monitor_dpi, self.data_folder)
            setattr(self, 'dr_p_and_t_plotter_widget', dr_p_and_t_plotter_widget)
        else:
            dr_p_and_t_plotter_widget = getattr(self, 'dr_p_and_t_plotter_widget')
        self.central_widget.layout().addWidget(dr_p_and_t_plotter_widget, 0, 0, 1, 1)

    #################################################
    # Configure Sigma Koki Rotation Stage
    #################################################

    def bd_sigma_koki(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        dialog = 'Select the comport for the sigma koki'
        com_port, okPressed = 'COM4', True
        if not hasattr(self, 'sk_widget_{0}'.format(com_port)) and okPressed:
            sk_widget = ConfigureSigmaKoki(com_port, self.status_bar)
            setattr(self, 'sk_widget_{0}'.format(com_port), sk_widget)
        elif okPressed:
            sk_widget = getattr(self, 'sk_widget_{0}'.format(com_port))
        else:
            return None
        self.central_widget.layout().addWidget(sk_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Configure Sigma Koki')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

    #################################################
    # Configure Stepper Motors
    #################################################

    def bd_configure_stepper_motor(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        dialog = 'Select the comport for the stepper motor you wish to configure'
        if self.dewar == '576':
            stepper_motor_ports = ['COM12', 'COM13', 'COM14']
        elif self.dewar == 'BlueForsDR1':
            stepper_motor_ports = ['COM12', 'COM13', 'COM14']
        else:
            stepper_motor_ports = []
        com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=stepper_motor_ports)
        if not hasattr(self, 'csm_widget_{0}'.format(com_port)) and okPressed:
            csm_widget = ConfigureStepperMotor(com_port, self.status_bar)
            setattr(self, 'csm_widget_{0}'.format(com_port), csm_widget)
        elif okPressed:
            csm_widget = getattr(self, 'csm_widget_{0}'.format(com_port))
        else:
            return None
        self.central_widget.layout().addWidget(csm_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Configure Stepper Motors')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

    #################################################
    # NOISE ANALYZER 
    #################################################

    def bd_noise_analyzer(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        if not hasattr(self, 'noise_analyzer_widget'):
            self.daq_settings = self.bolo_daq.initialize_daqs()
            self.noise_analyzer_widget = NoiseAnalyzer(self.daq_settings, self.squid_calibration_dict, self.status_bar, self.data_folder, self.screen_resolution, self.monitor_dpi)
        else:
            self.daq_settings = self.bolo_daq.initialize_daqs()
        self.noise_analyzer_widget.na_update_samples()
        self.central_widget.layout().addWidget(self.noise_analyzer_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Noise Analyzer')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

    #################################################
    # COSMIC RAYS
    #################################################

    def bd_cosmic_rays(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        if not hasattr(self, 'cosmic_ray_widget'):
            self.cosmic_ray_widget = CosmicRays(self.daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi, self.data_folder)
        else:
            self.daq_settings = self.bolo_daq.initialize_daqs()
            self.cosmic_ray_widget.cr_update_daq_settings(self.daq_settings)
        self.central_widget.layout().addWidget(self.cosmic_ray_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Cosmic Ray Data')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

    #################################################
    # TIME CONSTANT 
    #################################################

    def bd_time_constant(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        dialog = 'Select the comport for the SRS 830'
        #com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM10'])
        com_port, okPressed = 'COM10', True
        if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
            if not hasattr(self, 'srs_sr830dsp_widget'):
                self.status_bar.showMessage('Connecting to the SRS SR830 DSP')
                QtWidgets.QApplication.processEvents()
                try:
                    serial_com = BoloSerial(com_port, device='SRS_SR830_DSP', splash_screen=self.status_bar)
                except:
                    response = self.gb_quick_message('Com port in use... Launch in data analysis mode?', add_yes=True, add_no=True)
                    if response == QtWidgets.QMessageBox.Yes:
                        serial_com = None
                    else:
                        return None
                setattr(self, 'ser_{0}'.format(com_port), serial_com)
                if serial_com is not None:
                    self.srs_sr830dsp_widget = StanfordResearchSystemsSR830DSP(serial_com, com_port, self.status_bar, self.screen_resolution, self.monitor_dpi)
                else:
                    self.srs_sr830dsp_widget = None
        if not hasattr(self, 'time_constant_widget'):
            self.time_constant_widget = TimeConstant(self.daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi, self.srs_sr830dsp_widget)
        self.central_widget.layout().addWidget(self.time_constant_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Bolometer Time Constant')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())


    #################################################
    # Polarization Efficiency
    #################################################

    def bd_polarization_efficiency(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching Polarization Efficiency')
        QtWidgets.QApplication.processEvents()
        # SRS 830
        com_port, okPressed = 'COM10', True
        if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
            if not hasattr(self, 'srs_sr830dsp_widget'):
                self.status_bar.showMessage('Connecting to the SRS SR830 DSP')
                QtWidgets.QApplication.processEvents()
                try:
                    serial_com = BoloSerial(com_port, device='SRS_SR830_DSP', splash_screen=self.status_bar)
                except:
                    response = self.gb_quick_message('Com port in use... Launch in data analysis mode?', add_yes=True, add_no=True)
                    if response == QtWidgets.QMessageBox.Yes:
                        serial_com = None
                    else:
                        return None
                setattr(self, 'ser_{0}'.format(com_port), serial_com)
                if serial_com is not None:
                    self.srs_sr830dsp_widget = StanfordResearchSystemsSR830DSP(serial_com, com_port, self.status_bar, self.screen_resolution, self.monitor_dpi)
                else:
                    self.srs_sr830dsp_widget = None
        dialog = 'Select the comport for the stepper motor you wish to configure'
        # Stepper Motor 
        sm_com_port, okPressed = 'COM12', True
        if not hasattr(self, 'csm_widget_{0}'.format(sm_com_port)) and okPressed:
            if getattr(self, 'ser_{0}'.format(com_port)) is None:
                csm_widget = None
            else:
                csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar)
            setattr(self, 'csm_widget_{0}'.format(sm_com_port), csm_widget)
        elif okPressed:
            csm_widget = getattr(self, 'csm_widget_{0}'.format(sm_com_port))
        else:
            return None
        # Sigma Koki
        com_port, okPressed = 'COM4', True
        if not hasattr(self, 'sk_widget_{0}'.format(com_port)) and okPressed:
            sk_widget = ConfigureSigmaKoki(com_port, self.status_bar)
            setattr(self, 'sk_widget_{0}'.format(com_port), sk_widget)
        elif okPressed:
            sk_widget = getattr(self, 'sk_widget_{0}'.format(com_port))
        if not hasattr(self, 'polarization_efficiency_widget'):
            self.polarization_efficiency_widget = PolarizationEfficiency(self.daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi, csm_widget, self.srs_sr830dsp_widget, sk_widget, self.data_folder)
        self.polarization_efficiency_widget.pe_update_daq_settings(self.daq_settings)
        self.central_widget.layout().addWidget(self.polarization_efficiency_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Polarization Efficiency')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

    #################################################
    # SINGLE CHANNEL FTS BILLS
    #################################################

    def bd_fts(self):
        '''
        '''
        okPressed = True
        self.bd_load_com_port_settings()
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching FTS')
        QtWidgets.QApplication.processEvents()
        dialog = 'Select the comport for the SRS 830'
        #com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM10'])
        com_port = self.com_ports_dict[self.login]['SRS SR830DSP']
        #self.srs_sr830dsp_widget = None
        if not hasattr(self, 'ser_{0}'.format(com_port)) and com_port != 'None':
            if not hasattr(self, 'srs_sr830dsp_widget'):
                self.status_bar.showMessage('Connecting to the SRS SR830 DSP')
                QtWidgets.QApplication.processEvents()
                try:
                    serial_com = BoloSerial(com_port, device='SRS_SR830_DSP', splash_screen=self.status_bar)
                except:
                    response = self.gb_quick_message('Com port in use... Launch in data analysis mode?', add_yes=True, add_no=True)
                    if response == QtWidgets.QMessageBox.Yes:
                        serial_com = None
                    else:
                        return None
                setattr(self, 'ser_{0}'.format(com_port), serial_com)
                if serial_com is not None:
                    self.srs_sr830dsp_widget = StanfordResearchSystemsSR830DSP(serial_com, com_port, self.status_bar, self.screen_resolution, self.monitor_dpi)
                else:
                    self.srs_sr830dsp_widget = None
        dialog = 'Select the comport for the stepper motor you wish to configure'
        for motor in ['FTS Mirror Motor']:
            sm_com_port = self.com_ports_dict[self.login][motor]
            if not hasattr(self, 'csm_widget_{0}'.format(sm_com_port)) and okPressed:
                if getattr(self, 'ser_{0}'.format(com_port)) is None:
                    setattr(self, 'csm_widget_{0}'.format(sm_com_port), None)
                    csm_widget = None
                else:
                    csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar)
                setattr(self, 'csm_widget_{0}'.format(sm_com_port), csm_widget)
            elif okPressed:
                csm_widget = getattr(self, 'csm_widget_{0}'.format(sm_com_port))
            else:
                return None
            #self.srs_sr830dsp_widget = None
            if motor == 'FTS Mirror Motor':
                csm_mirror_widget = csm_widget
        #for motor in ['FTS Mirror Motor']:
        csm_input_widget = None
        csm_output_widget = None
        items = ['single mirror', 'input output']
        run_mode, okPressed = self.gb_quick_static_info_gather(
            title='',
            dialog=dialog,
            items=items)
        if run_mode == 'single mirror':
            motors = ['FTS Mirror Motor']
        elif run_mode == 'input output':
            motors = ['FTS Mirror Motor', 'FTS Input Polarizer', 'FTS Output Polarizer']
        for motor in motors:
            sm_com_port = self.com_ports_dict[self.login][motor]
            if not hasattr(self, 'csm_widget_{0}'.format(sm_com_port)) and okPressed:
                if getattr(self, 'ser_{0}'.format(com_port)) is None:
                    setattr(self, 'csm_widget_{0}'.format(sm_com_port), None)
                    csm_widget = None
                else:
                    csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar)
                setattr(self, 'csm_widget_{0}'.format(sm_com_port), csm_widget)
            elif okPressed:
                csm_widget = getattr(self, 'csm_widget_{0}'.format(sm_com_port))
            else:
                return None
            #self.srs_sr830dsp_widget = None
            if motor == 'FTS Mirror Motor':
                csm_mirror_widget = csm_widget
            elif motor == 'FTS Input Polarizer':
                csm_input_widget = csm_widget
            elif motor == 'FTS Output Polarizer':
                csm_output_widget = csm_widget
        if not hasattr(self, 'fts_widget'):
            self.fts_widget = FourierTransformSpectrometer(
                self.daq_settings,
                self.status_bar,
                self.screen_resolution,
                self.monitor_dpi,
                csm_mirror_widget,
                csm_input_widget,
                csm_output_widget,
                self.srs_sr830dsp_widget,
                self.data_folder)
        sm_com_port = self.com_ports_dict[self.login]['FTS Mirror Motor']
        if not hasattr(self, 'ser_{0}'.format(sm_com_port)):
            if hasattr(self, 'csm_widget_{0}'.format(sm_com_port)):
                csm_widget = getattr(self, 'csm_widget_{0}'.format(sm_com_port))
            elif okPressed:
                csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar)
            else:
                return None
            setattr(self, 'csm_widget_{0}'.format(sm_com_port), csm_widget)
            #self.srs_sr830dsp_widget = None
            if not hasattr(self, 'fts_widget'):
                self.fts_widget = FourierTransformSpectrometer(self.daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi, csm_widget, self.srs_sr830dsp_widget, self.data_folder)
        self.fts_widget.fts_update_samples()
        self.central_widget.layout().addWidget(self.fts_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('FTS')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

    #################################################
    # BEAM MAPPER 
    #################################################

    def bd_beam_mapper(self):
        '''
        '''
        self.bd_load_com_port_settings()
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching Beam Mapper')
        QtWidgets.QApplication.processEvents()
        dialog = 'Select the comport for the SRS 830'
        #com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM10'])
        com_port, okPressed = 'COM10', True
        if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
            if not hasattr(self, 'srs_sr830dsp_widget'):
                self.status_bar.showMessage('Connecting to the SRS SR830 DSP')
                QtWidgets.QApplication.processEvents()
                try:
                    serial_com = BoloSerial(com_port, device='SRS_SR830_DSP', splash_screen=self.status_bar)
                except:
                    response = self.gb_quick_message('Com port in use... Launch in data analysis mode?', add_yes=True, add_no=True)
                    if response == QtWidgets.QMessageBox.Yes:
                        serial_com = None
                    else:
                        return None
                setattr(self, 'ser_{0}'.format(com_port), serial_com)
            if serial_com is not None:
                self.srs_sr830dsp_widget = StanfordResearchSystemsSR830DSP(serial_com, com_port, self.status_bar, self.screen_resolution, self.monitor_dpi)
            else:
                self.srs_sr830dsp_widget = None
        stepper_motor_ports = ['COM13', 'COM14']
        self.csm_widget_dict = {}
        for i, dim in enumerate(('X', 'Y')):
            dialog = 'Select the comport for the {0} stepper motor you wish to configure'.format(dim)
            #sm_com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=stepper_motor_ports)
            sm_com_port = stepper_motor_ports[0]
            okPressed = True
            if not hasattr(self, 'csm_widget_{0}'.format(sm_com_port)) and okPressed:
                if getattr(self, 'ser_{0}'.format(com_port)) is None:
                    csm_widget = None
                else:
                    csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar)
                setattr(self, 'csm_widget_{0}'.format(sm_com_port), csm_widget)
            elif okPressed:
                #csm_widget = getattr(self, 'csm_widget_{0}'.format(sm_com_port))
                csm_widget = None
            else:
                return None
            stepper_motor_ports.pop(stepper_motor_ports.index(sm_com_port))
            self.csm_widget_dict[dim] = {
                'widget': csm_widget,
                'com_port': sm_com_port
                }
        if not hasattr(self, 'beam_mapper_widget'):
            self.beam_mapper_widget = BeamMapper(self.daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi, self.csm_widget_dict, self.srs_sr830dsp_widget, self.data_folder)
        self.beam_mapper_widget.bm_update_daq_settings(self.daq_settings)
        self.central_widget.layout().addWidget(self.beam_mapper_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Beam Mapper')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint())

if __name__ == '__main__':
    qt_app = QtWidgets.QApplication(sys.argv)
    qt_app.setFont(QtGui.QFont('SansSerif', 10))
    screen_resolution = qt_app.desktop().availableGeometry()
    screen_resolution = qt_app.desktop().screenGeometry()
    gui = BoloDAQGui(screen_resolution, qt_app)
    gui.show()
    exit(qt_app.exec_())
