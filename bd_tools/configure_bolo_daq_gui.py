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
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class ConfigureBoloDAQGui(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(ConfigureBoloDAQGui, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        for i, config in enumerate(['samples', 'squids', 'com']):
            setattr(self, '{0}_dict'.format(config.lower()), {})
            path = os.path.join('bd_settings', '{0}.json'.format(config))
            if os.path.exists(path):
                with open(path, 'r') as fh:
                    loaded_dict = json.load(fh)
                    setattr(self, '{0}_dict'.format(config.lower()), loaded_dict)
        self.cbd_gui_input_panel()

    def cbd_gui_input_panel(self):
        '''
        '''
        welcome_header_label = QtWidgets.QLabel('Configure Bolo DAQ GUI', self)
        self.layout().addWidget(welcome_header_label, 0, 0, 1, 2)
        for i, config in enumerate(['Samples', 'SQUIDs', 'COM']):
            header_label = QtWidgets.QLabel('{0}: '.format(config), self)
            self.layout().addWidget(header_label, i + 1, 0, 1, 1)
            combobox = QtWidgets.QComboBox(self)
            for item in getattr(self, '{0}_dict'.format(config.lower())):
                combobox.addItem(item)
            setattr(self, '{0}_combobox'.format(config.lower()), combobox)
            self.layout().addWidget(combobox, i + 1, 1, 1, 1)
            lineedit = QtWidgets.QLineEdit('', self)
            setattr(self, '{0}_lineedit'.format(config.lower()), lineedit)
            self.layout().addWidget(lineedit, i + 1, 2, 1, 1)
            update_pushbutton = QtWidgets.QPushButton('Update', self)
            update_pushbutton.setWhatsThis('{0}_update_pushbutton'.format(config.lower()))
            setattr(self, '{0}_update_pushbutton'.format(config.lower()), lineedit)
            self.layout().addWidget(update_pushbutton, i + 1, 3, 1, 1)
            add_pushbutton = QtWidgets.QPushButton('Add', self)
            add_pushbutton.setWhatsThis('{0}_add_pushbutton'.format(config.lower()))
            self.layout().addWidget(add_pushbutton, i + 1, 4, 1, 1)
            setattr(self, '{0}_add_pushbutton'.format(config.lower()), lineedit)
            remove_pushbutton = QtWidgets.QPushButton('Remove', self)
            remove_pushbutton.setWhatsThis('{0}_remove_pushbutton'.format(config.lower()))
            setattr(self, '{0}_remove_pushbutton'.format(config.lower()), lineedit)
            self.layout().addWidget(remove_pushbutton, i + 1, 5, 1, 1)
            add_pushbutton.clicked.connect(self.cbd_update_dict)
            update_pushbutton.clicked.connect(self.cbd_update_dict)
            remove_pushbutton.clicked.connect(self.cbd_update_dict)

    def cbd_update_dict(self):
        '''
        '''
        function = self.sender().text().lower()
        dict_to_edit = getattr(self, '{0}_dict'.format(self.sender().whatsThis().split('_')[0]))
        print()
        print(function, dict_to_edit)
        if function == 'add':
            index, okPressed1 = self.gb_quick_info_gather()
            value, okPressed2 = self.gb_quick_info_gather()
            if okPressed1 and okPressed2:
                dict_to_edit[index] = value


    def cbd_add_edit_squid(self):
        '''
        '''
        print(self.com_port_combobox.currentText())

    #################################################
    # Generica Control Function (Common to all DAQ Types)
    #################################################

    def bd_create_sample_dict_path(self):
        '''
        '''
        self.sample_dict = {}
        total_len_of_names = 0
        for i in range(1, 7):
            widget = '_daq_main_panel_set_sample_{0}_lineedit'.format(i)
            sample_name = str(getattr(self, widget).text())
            self.sample_dict[str(i)] = sample_name
            total_len_of_names += len(sample_name)
        pump_used = str(getattr(self, '_daq_main_panel_pump_lineedit').text())
        pump_oil_level = str(getattr(self, '_daq_main_panel_pump_oil_level_lineedit').text())
        self.sample_dict['Pump Used'] = pump_used
        self.sample_dict['Pump Oil Level'] = pump_oil_level
        if len(pump_used) == 0 or len(pump_oil_level) == 0:
            self.gb_quick_message('Please Record Pump and Oil Level\nNew info not saved!')
            return None
        sample_dict_path = './Sample_Dicts/{0}.json'.format(self.today_str)
        response = None
        if total_len_of_names == 0 and os.path.exists(sample_dict_path):
            warning_msg = 'Warning! {0} exists and you are '.format(sample_dict_path)
            warning_msg += 'going to overwrite with blank names for all channels'
            response = self.gb_quick_info_gather(warning_msg)
            if response == QtWidgets.QMessageBox.Save:
                with open(sample_dict_path, 'w') as sample_dict_file_handle:
                    simplejson.dump(self.sample_dict, sample_dict_file_handle)
                getattr(self, '_daq_main_panel_set_sample_dict_path_label').setText('Set Path @ {0}'.format(sample_dict_path))
        else:
            with open(sample_dict_path, 'w') as sample_dict_file_handle:
                simplejson.dump(self.sample_dict, sample_dict_file_handle)
            getattr(self, '_daq_main_panel_set_sample_dict_path_label').setText('Set Path @ {0}'.format(sample_dict_path))
