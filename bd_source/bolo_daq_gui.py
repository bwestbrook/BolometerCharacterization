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
import pylab as pl
import matplotlib.pyplot as plt
import time
import threading
from PyPDF2 import PdfFileMerger
from pprint import pprint, pformat
from datetime import datetime
from copy import copy
from PyQt5 import QtCore, QtGui, QtWidgets

# Settings 
from bd_settings.bd_global_settings import settings

# Widgets
from bd_tools.cosmic_rays import CosmicRays
from bd_tools.beam_mapper import BeamMapper
from bd_tools.iv_collector import IVCollector
from bd_tools.rt_collector import RTCollector
from bd_tools.fridge_cycle import FridgeCycle
from bd_tools.data_plotter import DataPlotter
from bd_tools.lakeshore_372 import LakeShore372
from bd_tools.time_constant import TimeConstant
from bd_tools.agilent_e3634a import AgilentE3634A
from bd_tools.com_port_utility import ComPortUtility
from bd_tools.hewlett_packard_34401a import HewlettPackard34401A
from bd_tools.configure_ni_daq import ConfigureNIDAQ
from bd_tools.configure_bolo_daq_gui import ConfigureBoloDAQGui
from bd_tools.configure_stepper_motor import ConfigureStepperMotor
from bd_tools.polarization_efficiency import PolarizationEfficiency
from bd_tools.fourier_transform_spectrometer import FourierTransformSpectrometer
from bd_tools.stanford_research_systems_sr830_dsp import StanfordResearchSystemsSR830DSP
# Libraries
from bd_lib.fourier import Fourier
from bd_lib.bolo_daq import BoloDAQ
from bd_lib.bolo_serial import BoloSerial
from bd_lib.iv_curves import IVCurves

# Gui Biulder
from GuiBuilder.gui_builder import GuiBuilder

#from RT_Curves.plot_rt_curves import RTCurve
#from FTS_Curves.plot_fts_curves import FTSCurve
#from Beam_Maps.beam_mapper_tools import BeamMapperTools
#from POL_Curves.plot_pol_curves import PolCurve
#from TAU_Curves.plot_tau_curves import TAUCurve
#from FTS_DAQ.fts_daq import FTSDAQ
#from FTS_DAQ.analyzeFTS import FTSanalyzer
#from LockIn.lock_in import LockIn
#from PowerSupply.power_supply import PowerSupply
#from FridgeCycle.fridge_cycle import FridgeCycle

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
        self.monitor_dpi = 120.0
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = './Data/{0}'.format(self.today_str)
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        self.bd_setup_status_bar()
        self.com_port_utility_widget = ComPortUtility(self.splash_screen, self.screen_resolution, self.monitor_dpi)
        self.bd_get_available_daq_settings()
        self.splash_screen.close()
        #self.resize(int(0.95 * self.screen_resolution.width()), int(0.8 * self.screen_resolution.height()))
        self.move(0, 0)
        #getattr(self, 'action_Bolo_DAQ_Settings').trigger()
        self.show()
        getattr(self, 'action_Bolo_DAQ_Settings').trigger()
        #getattr(self, 'action_FTS').trigger()
        if os.getlogin() == 'BoloTester':
            self.dewar = '576'
        elif os.getlogin() == 'Bluefors_PC':
            self.dewar = 'BlueForsDR1'
        else:
            self.gb_quick_message('Computer not recgonized', message_type='Warning')
            os._exit(0)

    ##################################################################################
    #### Start up Tasks ##############################################################
    ##################################################################################

    def __apply_settings__(self, settings):
        for setting in dir(settings):
            if '__' not in setting:
                setattr(self, setting, getattr(settings, setting))

    ##################################################################################
    #### Global Gui     ##############################################################
    ##################################################################################

    def bd_setup_status_bar(self):
        '''
        '''
        custom_widgets = []
        #custom_widgets.append(custom_widget)
        permanant_messages = ['Bolo DAQ Benjamin Grey Westbrook 2020']
        self.gb_add_status_bar(permanant_messages=permanant_messages , add_saved=True, custom_widgets=custom_widgets)

    def bd_close_main(self):
        '''
        '''
        self.close()

    ##################################################################################
    #### Common DAQ     ##############################################################
    ##################################################################################

    def bd_get_available_daq_settings(self):
        '''
        '''
        if hasattr(self, 'available_daq_settings'):
            return None
        self.daq = BoloDAQ()
        if not hasattr(self, 'daq_settings'):
            self.bd_get_saved_daq_settings()
        self.available_daq_settings = {}
        self.splash_screen.showMessage('Configure NIDAQ: Deterimining all available daqs')
        QtWidgets.QApplication.processEvents()
        for device, configuration_dict in self.daq_settings.items():
            available = True
            for i in range(2):
                for j in range(8):
                    self.splash_screen.showMessage("Configuring NIDAQ: Checking if {0}:::ch{1} is available ({2}/2)".format(device, j, i + 1))
                    QtWidgets.QApplication.processEvents()
                    try:
                        vol_ts, vol_mean, vol_min, vol_max, vol_std = self.daq.get_data(signal_channel=j,
                                                                                        int_time=100,
                                                                                        sample_rate=1000,
                                                                                        device=device)
                    except nidaqmx.errors.DaqError:
                        self.splash_screen.showMessage("Configuring NIDAQ {0}:::ch{1} is not available".format(device, j))
                        QtWidgets.QApplication.processEvents()
                        available = False
                        break
            if available:
                self.available_daq_settings[device] = configuration_dict
        n_devices = len(self.available_daq_settings)
        devices = list(self.available_daq_settings.keys())
        self.status_bar.showMessage('Found {0} available devices: {1}'.format(n_devices, devices))

    def bd_get_saved_daq_settings(self):
        '''
        '''
        if os.path.exists(os.path.join('bd_settings', 'daq_settings.json')):
            with open(os.path.join('bd_settings', 'daq_settings.json'), 'r') as json_handle:
                self.daq_settings = simplejson.load(json_handle)
        else:
            print()
            print()
            print()
            print()
            print()
            print()
            self.daq_settings = self.daq.initialize_daqs()
            pprint(self.daq_settings)
            with open(os.path.join('bd_settings', 'daq_settings.json'), 'w') as json_handle:
                simplejson.dump(self.daq_settings, json_handle)


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
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching Fridge Cycle')
        QtWidgets.QApplication.processEvents()
        if not hasattr(self, 'fridge_cycle_widget'):
            self.fridge_cycle_widget = FridgeCycle(self.status_bar)
        self.central_widget.layout().addWidget(self.fridge_cycle_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Fridge Cycle')
        QtWidgets.QApplication.processEvents()
        self.showNormal()

    #################################################
    # Configure DAQ
    #################################################

    def bd_configure_ni_daq(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching Configure National Intruments DAQ')
        QtWidgets.QApplication.processEvents()
        self.bd_get_available_daq_settings()
        if not hasattr(self, 'configure_ni_daq_widget'):
            self.configure_ni_daq_widget = ConfigureNIDAQ(self.available_daq_settings, self.status_bar)
        self.central_widget.layout().addWidget(self.configure_ni_daq_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Configure National Intruments DAQ')
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
            self.configure_bolo_daq_gui_widget = ConfigureBoloDAQGui(self.available_daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi)
        #self.time_constant_widget.tc_display_daq_settings()
        self.central_widget.layout().addWidget(self.configure_bolo_daq_gui_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Bolo DAQ GUI Settings')
        QtWidgets.QApplication.processEvents()
        self.showNormal()

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
        dialog = 'Select the comport for the Lakeshore'
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
        self.showNormal()

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
        self.showNormal()

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
        com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM3'])
        if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
            serial_com = BoloSerial(com_port, device='HP_34401A', splash_screen=self.status_bar)
            setattr(self, 'ser_{0}'.format(com_port), serial_com)
            if not hasattr(self, 'hewlett_packard_34401a_widget'):
                self.hewlett_packard_34401a_widget = HewlettPackard34401A(serial_com, com_port, self.status_bar, self.screen_resolution, self.monitor_dpi)
            self.central_widget.layout().addWidget(self.hewlett_packard_34401a_widget, 0, 0, 1, 1)
        elif okPressed:
            self.hewlett_packard_34401a_widget.ae_update_serial_com(serial_com)
            self.central_widget.layout().addWidget(self.hewlett_packard_34401a_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Hewlett Packard 34401A Controller')
        QtWidgets.QApplication.processEvents()
        self.showNormal()

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
        self.showNormal()

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
        com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM6', 'COM4'])
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
        self.showNormal()

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
        if not hasattr(self, 'xyc_widget'):
            self.ivc_widget = IVCollector(self.available_daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi)
        else:
            self.ivc_widget.ivc_populate()
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
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Loading RT Curves')
        QtWidgets.QApplication.processEvents()
        dialog = 'Select the comport for the Temperature Lakeshore'
        if self.dewar == '576':
            ls_372_samples_widget = None
            ls_372_temp_widget = None
        elif self.dewar == 'BlueForsDR1':
            #com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM4'])
            com_port, okPressed = 'COM4', True
            if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
                serial_com = BoloSerial(com_port, device='Model372', splash_screen=self.status_bar)
                setattr(self, 'ser_{0}'.format(com_port), serial_com)
                if not hasattr(self, 'ls_372_widget_{0}'.format(com_port)):
                    ls_372_temp_widget = LakeShore372(serial_com, com_port, self.status_bar)
                    setattr(self, 'ls_372_widget_{0}'.format(com_port), ls_372_temp_widget)
            dialog = 'Select the comport for the Sample Lakeshore'
            #com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM6'])
            com_port, okPressed = 'COM6', True
            if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
                serial_com = BoloSerial(com_port, device='Model372', splash_screen=self.status_bar)
                setattr(self, 'ser_{0}'.format(com_port), serial_com)
                if not hasattr(self, 'ls_372_widget_{0}'.format(com_port)):
                    ls_372_samples_widget = LakeShore372(serial_com, com_port, self.status_bar)
                    setattr(self, 'ls_372_widget_{0}'.format(com_port), ls_372_samples_widget)
        if not hasattr(self, 'rtc_widget'):
            if self.dewar == 'BlueForsDR1':
                ls_372_samples_widget = getattr(self, 'ls_372_widget_{0}'.format(com_port))
            self.rtc_widget = RTCollector(self.available_daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi, ls_372_temp_widget, ls_372_samples_widget)
        else:
            self.rtc_widget.rtc_populate()
        self.central_widget.layout().addWidget(self.rtc_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('RT Curves')
        QtWidgets.QApplication.processEvents()
        self.resize(self.minimumSizeHint().width(), self.minimumSizeHint().height())

    #################################################
    # Configure Stepper Motors
    #################################################

    def bd_configure_stepper_motor(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        dialog = 'Select the comport for the stepper motor you wish to configure'
        stepper_motor_ports = ['COM12', 'COM13', 'COM14']
        com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=stepper_motor_ports)
        if not hasattr(self, 'csm_widget_{0}'.format(com_port)) and okPressed:
            csm_widget = ConfigureStepperMotor(com_port, self.status_bar)
            setattr(self, 'csm_widget_{0}'.format(com_port), csm_widget)
        elif okPressed:
            csm_widget = getattr(self, 'csm_widget_{0}'.format(com_port))
        else:
            return None
        csm_widget.csm_get_motor_state()
        self.central_widget.layout().addWidget(csm_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Configure Stepper Motors')
        QtWidgets.QApplication.processEvents()
        self.showNormal()

    #################################################
    # COSMIC RAYS
    #################################################

    def bd_cosmic_rays(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        if not hasattr(self, 'cosmic_ray_widget'):
            self.cosmic_ray_widget = CosmicRays(self.available_daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi)
        self.bd_get_saved_daq_settings()
        self.cosmic_ray_widget.cr_update_daq_settings(self.daq_settings)
        self.central_widget.layout().addWidget(self.cosmic_ray_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Cosmic Ray Data')
        QtWidgets.QApplication.processEvents()
        self.showNormal()

    #################################################
    # TIME CONSTANT 
    #################################################

    def bd_time_constant(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        if not hasattr(self, 'time_constant_widget'):
            self.time_constant_widget = TimeConstant(self.available_daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi)
        self.central_widget.layout().addWidget(self.time_constant_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Bolometer Time Constant')
        QtWidgets.QApplication.processEvents()
        self.showNormal()

    #################################################
    # BEAM MAPPER 
    #################################################

    def bd_beam_mapper(self):
        '''
        '''
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
                serial_com = BoloSerial(com_port, device='SRS_SR830_DSP', splash_screen=self.status_bar)
                setattr(self, 'ser_{0}'.format(com_port), serial_com)
                self.srs_sr830dsp_widget = StanfordResearchSystemsSR830DSP(serial_com, com_port, self.status_bar, self.screen_resolution, self.monitor_dpi)
        stepper_motor_ports = ['COM13', 'COM14']
        self.csm_widget_dict = {}
        for i, dim in enumerate(('X', 'Y')):
            dialog = 'Select the comport for the {0} stepper motor you wish to configure'.format(dim)
            #sm_com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=stepper_motor_ports)
            sm_com_port = stepper_motor_ports[0]
            okPressed = True
            if not hasattr(self, 'csm_widget_{0}'.format(sm_com_port)) and okPressed:
                csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar)
                setattr(self, 'csm_widget_{0}'.format(sm_com_port), csm_widget)
            elif okPressed:
                csm_widget = getattr(self, 'csm_widget_{0}'.format(sm_com_port))
            else:
                return None
            stepper_motor_ports.pop(stepper_motor_ports.index(sm_com_port))
            self.csm_widget_dict[dim] = {
                'widget': csm_widget,
                'com_port': sm_com_port
                }
        if not hasattr(self, 'beam_mapper_widget'):
            self.beam_mapper_widget = BeamMapper(self.available_daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi, self.csm_widget_dict, self.srs_sr830dsp_widget)
        self.bd_get_saved_daq_settings()
        self.beam_mapper_widget.bm_update_daq_settings(self.daq_settings)
        self.central_widget.layout().addWidget(self.beam_mapper_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Beam Mapper')
        QtWidgets.QApplication.processEvents()
        self.show()
        self.showMaximized()

    #################################################
    # Polarization Efficiency
    #################################################

    def bd_polarization_efficiency(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching Polarization Efficiency')
        QtWidgets.QApplication.processEvents()
        dialog = 'Select the comport for the SRS 830'
        #com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM10'])
        com_port, okPressed = 'COM10', True
        if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
            if not hasattr(self, 'srs_sr830dsp_widget'):
                self.status_bar.showMessage('Connecting to the SRS SR830 DSP')
                QtWidgets.QApplication.processEvents()
                serial_com = BoloSerial(com_port, device='SRS_SR830_DSP', splash_screen=self.status_bar)
                setattr(self, 'ser_{0}'.format(com_port), serial_com)
                self.srs_sr830dsp_widget = StanfordResearchSystemsSR830DSP(serial_com, com_port, self.status_bar, self.screen_resolution, self.monitor_dpi)
        dialog = 'Select the comport for the stepper motor you wish to configure'
        stepper_motor_ports = ['COM12']
        #sm_com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=stepper_motor_ports)
        sm_com_port, okPressed = 'COM12', True
        if not hasattr(self, 'csm_widget_{0}'.format(sm_com_port)) and okPressed:
            csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar)
            setattr(self, 'csm_widget_{0}'.format(sm_com_port), csm_widget)
        elif okPressed:
            csm_widget = getattr(self, 'csm_widget_{0}'.format(sm_com_port))
        else:
            return None
        if not hasattr(self, 'polarization_efficiency_widget'):
            self.polarization_efficiency_widget = PolarizationEfficiency(self.available_daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi, csm_widget, self.srs_sr830dsp_widget)
        self.bd_get_saved_daq_settings()
        self.polarization_efficiency_widget.pe_update_daq_settings(self.daq_settings)
        self.central_widget.layout().addWidget(self.polarization_efficiency_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Polarization Efficiency')
        QtWidgets.QApplication.processEvents()
        self.show()
        self.showMaximized()

    #################################################
    # SINGLE CHANNEL FTS BILLS
    #################################################

    def bd_fts(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.status_bar.showMessage('Launching FTS')
        QtWidgets.QApplication.processEvents()
        dialog = 'Select the comport for the SRS 830'
        #com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=['COM10'])
        com_port, okPressed = 'COM10', True
        if not hasattr(self, 'ser_{0}'.format(com_port)) and okPressed:
            if not hasattr(self, 'srs_sr830dsp_widget'):
                self.status_bar.showMessage('Connecting to the SRS SR830 DSP')
                QtWidgets.QApplication.processEvents()
                serial_com = BoloSerial(com_port, device='SRS_SR830_DSP', splash_screen=self.status_bar)
                setattr(self, 'ser_{0}'.format(com_port), serial_com)
                self.srs_sr830dsp_widget = StanfordResearchSystemsSR830DSP(serial_com, com_port, self.status_bar, self.screen_resolution, self.monitor_dpi)
        dialog = 'Select the comport for the stepper motor you wish to configure'
        stepper_motor_ports = ['COM12']
        #sm_com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=stepper_motor_ports)
        sm_com_port, okPressed = 'COM12', True
        if not hasattr(self, 'csm_widget_{0}'.format(sm_com_port)) and okPressed:
            csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar)
            setattr(self, 'csm_widget_{0}'.format(sm_com_port), csm_widget)
        elif okPressed:
            csm_widget = getattr(self, 'csm_widget_{0}'.format(sm_com_port))
        else:
            return None
        if not hasattr(self, 'fts_widget'):
            self.fts_widget = FourierTransformSpectrometer(self.available_daq_settings, self.status_bar, self.screen_resolution, self.monitor_dpi, csm_widget, self.srs_sr830dsp_widget)
        self.bd_get_saved_daq_settings()
        self.fts_widget.fts_update_daq_settings(self.daq_settings)
        self.central_widget.layout().addWidget(self.fts_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('FTS')
        QtWidgets.QApplication.processEvents()
        self.show()
        self.showMaximized()


if __name__ == '__main__':
    qt_app = QtWidgets.QApplication(sys.argv)
    qt_app.setFont(QtGui.QFont('SansSerif', 10))
    screen_resolution = qt_app.desktop().availableGeometry()
    screen_resolution = qt_app.desktop().screenGeometry()
    gui = BoloDAQGui(screen_resolution, qt_app)
    gui.show()
    exit(qt_app.exec_())

