from PyQt4 import QtCore, QtGui
from libraries.gen_class import Class
from main_panel import main_panel_settings
from RT_popup import rtcurve_settings_popup_settings
from IV_popup import ivcurve_settings_popup_settings
from FTS_popup import ftscurve_settings_popup_settings
from POL_popup import polcurve_settings_popup_settings
from TAU_popup import taucurve_settings_popup_settings
from daq_main_panel import daq_main_panel_settings
from user_move_stepper import user_move_stepper_settings
from time_constant import time_constant_settings
from single_channel_fts import single_channel_fts_settings
from pol_efficiency import pol_efficiency_settings
from beam_mapper import beam_mapper_settings
from final_plot import final_plot_settings
from xy_collector import xy_collector_settings
from cosmic_rays import cosmic_rays_settings
from multimeter import multimeter_settings


settings = Class()

# Settings need for general GUI management

settings.small_font = QtGui.QFont("Times", 8)
settings.med_font = QtGui.QFont("Times", 11)
settings.large_font = QtGui.QFont("Times", 14)
settings.larger_font = QtGui.QFont("Times", 16)
settings.huge_font = QtGui.QFont("Times", 24)
settings.giant_font = QtGui.QFont("Times", 32)

settings.widget_to_object_dict = {
                                  'textedit': 'QTextEdit',
                                  'lineedit': 'QLineEdit',
                                  'combobox': 'QComboBox',
                                  'widget': 'QWidget',
                                  'slider': 'QSlider',
                                  'label': 'QLabel',
                                  'panel': 'QWidget',
                                  'popup': 'QWidget',
                                  'toolbutton': 'QToolButton',
                                  'pushbutton': 'QPushButton',
                                  'checkbox': 'QCheckBox'
                                 }

# Individual files for various panels

list_of_extra_settings = [main_panel_settings, rtcurve_settings_popup_settings,
                          ivcurve_settings_popup_settings, ftscurve_settings_popup_settings,
                          polcurve_settings_popup_settings, daq_main_panel_settings,
                          user_move_stepper_settings, single_channel_fts_settings,
                          beam_mapper_settings, pol_efficiency_settings, final_plot_settings,
                          taucurve_settings_popup_settings, xy_collector_settings,
                          time_constant_settings, multimeter_settings, cosmic_rays_settings]


for extra_settings in list_of_extra_settings:
    for attribute in dir(extra_settings):
        if '__' not in attribute:
            setattr(settings, attribute, getattr(extra_settings, attribute))


settings.squid_calibration_dict  = {'1': 30.0, '2': 27.3, '3': 30.0,
                                    '4': 30.1, '5': 25.9, '6': 25.0}
