import time
import shutil
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
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        for i, config in enumerate(['samples', 'squids', 'comports']):
            path = os.path.join('bd_settings', '{0}_settings.json'.format(config))
            if os.path.exists(path):
                with open(path, 'r') as fh:
                    loaded_dict = simplejson.load(fh)
                    setattr(self, '{0}_dict'.format(config.lower()), loaded_dict)
                with open(path, 'w') as fh:
                    simplejson.dump(getattr(self, '{0}_dict'.format(config.lower())), fh,
                                    indent=4, sort_keys=True)
                with open(path, 'r') as fh:
                    loaded_dict = simplejson.load(fh)
                    setattr(self, '{0}_dict'.format(config.lower()), loaded_dict)
            else:
                setattr(self, '{0}_dict'.format(config.lower()), {})
                with open(path, 'w') as fh:
                    simplejson.dump({}, fh)
        self.cbd_gui_input_panel()

    def cbd_gui_input_panel(self):
        '''
        '''
        welcome_header_label = QtWidgets.QLabel('Configure Bolo DAQ GUI', self)
        self.layout().addWidget(welcome_header_label, 0, 0, 1, 2)
        j = 0
        settings_column_header_label = QtWidgets.QLabel('SETTING', self)
        self.layout().addWidget(settings_column_header_label, 1, 0, 1, 1)
        loaded_column_header_label = QtWidgets.QLabel('CURRENTLY LOADED', self)
        self.layout().addWidget(loaded_column_header_label, 1, 1, 1, 1)
        loaded_column_header_label = QtWidgets.QLabel('SETTING VALUE', self)
        self.layout().addWidget(loaded_column_header_label, 1, 2, 1, 1)
        loaded_column_header_label = QtWidgets.QLabel('Controls', self)
        self.layout().addWidget(loaded_column_header_label, 1, 3, 1, 1)
        for i, config in enumerate(['Samples', 'SQUIDs', 'COMPORTS']):
            header_label = QtWidgets.QLabel('{0}: '.format(config), self)
            self.layout().addWidget(header_label, i + 2, 0, 1, 1)
            combobox = QtWidgets.QComboBox(self)
            combobox.setWhatsThis('{0}_commbobox'.format(config.lower()))
            for item in getattr(self, '{0}_dict'.format(config.lower())):
                combobox.addItem(item)
            setattr(self, '{0}_combobox'.format(config.lower()), combobox)
            self.layout().addWidget(combobox, i + 2, 1, 1, 1)
            lineedit = QtWidgets.QLineEdit('', self)
            setattr(self, '{0}_lineedit'.format(config.lower()), lineedit)
            self.layout().addWidget(lineedit, i + 2, 2, 1, 1)
            modify_pushbutton = QtWidgets.QPushButton('Modify', self)
            modify_pushbutton.setWhatsThis('{0}_modify_pushbutton'.format(config.lower()))
            setattr(self, '{0}_modify_pushbutton'.format(config.lower()), modify_pushbutton)
            self.layout().addWidget(modify_pushbutton, i + 2, 3, 1, 1)
            add_pushbutton = QtWidgets.QPushButton('Add', self)
            add_pushbutton.setWhatsThis('{0}_add_pushbutton'.format(config.lower()))
            self.layout().addWidget(add_pushbutton, i + 2, 4, 1, 1)
            setattr(self, '{0}_add_pushbutton'.format(config.lower()), add_pushbutton)
            remove_pushbutton = QtWidgets.QPushButton('Remove', self)
            remove_pushbutton.setWhatsThis('{0}_remove_pushbutton'.format(config.lower()))
            setattr(self, '{0}_remove_pushbutton'.format(config.lower()), remove_pushbutton)
            self.layout().addWidget(remove_pushbutton, i + 2, 5, 1, 1)
            # Save
            save_pushbutton = QtWidgets.QPushButton('Save', self)
            save_pushbutton.setWhatsThis('{0}_save_pushbutton'.format(config.lower()))
            setattr(self, '{0}_save_pushbutton'.format(config.lower()), save_pushbutton)
            self.layout().addWidget(save_pushbutton, i + 2, 6, 1, 1)
            # Load
            load_pushbutton = QtWidgets.QPushButton('Load', self)
            load_pushbutton.setWhatsThis('{0}_load_pushbutton'.format(config.lower()))
            setattr(self, '{0}_load_pushbutton'.format(config.lower()), save_pushbutton)
            self.layout().addWidget(load_pushbutton, i + 2, 7, 1, 1)
            # Connect to slots
            add_pushbutton.clicked.connect(self.cbd_add_item)
            remove_pushbutton.clicked.connect(self.cbd_delete_item)
            modify_pushbutton.clicked.connect(self.cbd_modify_dict)
            save_pushbutton.clicked.connect(self.cbd_save_dict)
            load_pushbutton.clicked.connect(self.cbd_load_dict)
            j += 1
        self.cbd_populate_combobox('comports')
        self.cbd_populate_combobox('squids')
        self.cbd_populate_combobox('samples')

    def cbd_populate_combobox(self, setting):
        '''
        '''
        combobox = getattr(self, '{0}_combobox'.format(setting))
        lineedit = getattr(self, '{0}_lineedit'.format(setting))
        dict_to_edit = getattr(self, '{0}_dict'.format(setting))
        combobox.clear()
        existing_items = []
        for i in range(combobox.count()):
            existing_items.append(combobox.itemText(i))
        if setting == 'samples':
            items = [x for x in dict_to_edit.keys()]
        else:
            items = dict_to_edit.keys()
        for item in sorted(items):
            if items not in existing_items:
                combobox.addItem(str(item))
        combobox.currentIndexChanged.connect(self.cbd_update_label)
        combobox.setCurrentIndex(-1)
        combobox.setCurrentIndex(0)

    def cbd_load_dict(self):
        '''
        '''
        setting = self.sender().whatsThis().split('_')[0]
        load_path = QtWidgets.QFileDialog.getOpenFileName(self, 'bd_settings', '')[0]

        with open(load_path, 'r') as file_handle:
            saved_settings = simplejson.load(file_handle)
        default_path = os.path.join('bd_settings', '{0}_settings.json'.format(setting))
        with open(default_path, 'w') as file_handle:
            simplejson.dump(saved_settings, file_handle)

    def cbd_save_dict(self):
        '''
        '''
        setting = self.sender().whatsThis().split('_')[0]
        setting_file_name = os.path.join('bd_settings', '{0}_settings_{1}.json'.format(setting, self.today_str))
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'bd_settings\\', setting_file_name, filter='.json')[0]
        if len(save_path) == 0:
            return None
        default_path = os.path.join('bd_settings', '{0}_settings.json'.format(setting))
        print(default_path, save_path)
        shutil.copy(default_path, save_path)

    def cbd_modify_dict(self, index=0):
        '''
        '''
        setting = self.sender().whatsThis().split('_')[0]
        dict_to_modify = getattr(self, '{0}_dict'.format(setting))
        key_to_modify = getattr(self, '{0}_combobox'.format(setting.lower())).currentText()
        new_value = getattr(self, '{0}_lineedit'.format(setting.lower())).text()
        msg = 'Update "{0}"\nKey: {1}\nNew Value: "{2}"'.format(setting, key_to_modify, new_value)
        response = self.gb_quick_message(msg=msg, add_cancel=True, add_yes=True)
        if response == QtWidgets.QMessageBox.Yes:
            dict_to_modify[key_to_modify] = new_value
            path = os.path.join('bd_settings', '{0}_settings.json'.format(setting))
            index = getattr(self, '{0}_combobox'.format(setting)).findText(key_to_modify)
            self.cbd_update_label(index)
            with open(path, 'w') as fh:
                simplejson.dump(dict_to_modify, fh)

    def cbd_add_item(self):
        '''
        '''
        function = self.sender().text().lower()
        setting = self.sender().whatsThis().split('_')[0]
        dict_to_edit = getattr(self, '{0}_dict'.format(setting))
        key, okPressed1 = self.gb_quick_info_gather(dialog='{0} key to add'.format(setting))
        value, okPressed2 = self.gb_quick_info_gather(dialog='Value for {0}'.format(setting))
        if okPressed1 and okPressed2:
            dict_to_edit[key] = value
            getattr(self, '{0}_combobox'.format(setting)).addItem(key)
            index = getattr(self, '{0}_combobox'.format(setting)).findText(key)
            getattr(self, '{0}_combobox'.format(setting)).setCurrentIndex(index)
            if setting == 'squids':
                getattr(self, '{0}_lineedit'.format(setting)).setText('{0} (uA/V)'.format(value))
            else:
                getattr(self, '{0}_lineedit'.format(setting)).setText(value)
            setattr(self, '{0}_dict'.format(setting), dict_to_edit)
            path = os.path.join('bd_settings', '{0}_settings.json'.format(setting))
            with open(path, 'w') as fh:
                simplejson.dump(dict_to_edit, fh)
        else:
            self.gb_quick_message('Please supply an key and value for the setting', msg_type='Warning')

    def cbd_update_settings(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'daq_settings.json'), 'r') as json_handle:
            self.daq_settings = simplejson.load(json_handle)
        return self.daq_settings

    def cbd_delete_item(self):
        '''
        '''
        setting = self.sender().whatsThis().split('_')[0]
        dict_to_edit = getattr(self, '{0}_dict'.format(setting))
        key_to_delete, okPressed1 = self.gb_quick_static_info_gather(dialog='{0} to delete'.format(setting), items=dict_to_edit.keys())
        if okPressed1:
            if key_to_delete in dict_to_edit:
                dict_to_edit.pop(key_to_delete)
                path = os.path.join('bd_settings', '{0}_settings.json'.format(setting))
                with open(path, 'w') as fh:
                    simplejson.dump(dict_to_edit, fh)
        self.cbd_populate_combobox(setting)

    def cbd_update_label(self, index):
        '''
        '''
        setting = self.sender().whatsThis().split('_')[0]
        dict_to_edit = getattr(self, '{0}_dict'.format(setting))
        combobox = getattr(self, '{0}_combobox'.format(setting))
        lineedit = getattr(self, '{0}_lineedit'.format(setting))
        if combobox.itemText(index) in dict_to_edit:
            value = dict_to_edit[combobox.itemText(index)]
            if setting == 'squids':
                lineedit.setText('{0} (uA/V)'.format(value))
            else:
                lineedit.setText(value)


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
