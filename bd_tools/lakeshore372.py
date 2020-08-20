import os
from copy import copy
from pprint import pprint
from bd_lib.bolo_serial import BoloSerial
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class LakeShore372(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, com_port, status_bar):
        super(LakeShore372, self).__init__()
        self.status_bar = status_bar
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.serial_com = BoloSerial(com_port, device='Model372', splash_screen=status_bar)
        self.com_port = com_port
        self.channel_indicies = [str(x) for x in range(1, 17)]
        self.analog_output_indicies = [str(x) for x in range(1, 4)]
        self.analog_output_indicies = ['sample', 'warmup', 'aux']
        self.channels = LS372Channels(self.serial_com)
        self.analog_outputs = LS372AnalogOutputs(self.serial_com)
        self.lakeshore372_command_dict = {
            'autorange': {
                'False': 0,
                0: 'False',
                'True': 1,
                1: 'True'
                },
            'filter_on': {
                'False': 0,
                0: 'False',
                'True': 1,
                1: 'True'
                },
            'powerup_enable': {
                'False': 0,
                0: 'False',
                'True': 1,
                1: 'True'
                },
            'enabled': {
                'False': 0,
                0: 'False',
                'True': 1,
                1: 'True'
                },
            'analog_channel': {
                'warm_up': 0,
                0: 'warm_up',
                'sample': 1,
                1: 'sample',
                'aux': 2,
                2: 'aux'
                },
            'exc_mode': {
                'voltage': 0,
                0: 'voltage',
                'current': 1,
                1: 'current'
                },
            'analog_mode': {
                'output_off': 0,
                0: 'output_off',
                'monitor': 1,
                1: 'monitor',
                'open_loop': 2,
                2: 'open_loop',
                'zone': 3,
                3: 'zone',
                'still': 4,
                4: 'still',
                'closed_loop': 5,
                5: 'closed_loop',
                'warm_up': 6,
                6: 'warm_up',
                },
            'polarity': {
                'unipolar': 0,
                0: 'unipolar',
                'bipolar': 1,
                1: 'bipolar'
                },
            'filter': {
                'unfiltered': 0,
                0: 'unfiltered',
                'filtered': 1,
                1: 'filtered'
                },
            'source': {
                'kelvin': 1,
                1: 'kelvin',
                'ohms': 2,
                2: 'ohms',
                },
            'units': {
                'kelvin': 1,
                1: 'kelvin',
                'ohms': 2,
                2: 'ohms',
                },
            'resistance_range': {
                1: 2.0e-3,
                2.0e-3: 1,
                2: 6.32e-3,
                6.32e-3: 2,
                3: 20.0e-3,
                20.0e-3: 3,
                4: 63.2e-3,
                63.2e-3: 4,
                5: 200e-3,
                200e-3: 5,
                6: 632e-3,
                632e-3: 6,
                7: 2.00,
                2.00: 7,
                8: 6.32,
                6.32: 8,
                9: 20.001,
                20.001: 9,
                10: 63.2,
                63.2: 10,
                11: 200.001,
                200.001: 11,
                12: 632,
                632: 12,
                13: 2.00e3,
                2.00e3: 13,
                14: 6.32e3,
                6.32e3: 14,
                15: 20.0e3,
                20.0e3: 15,
                16: 63.2e3,
                63.2e3: 16,
                17: 200e3,
                200e3: 17,
                18: 632e3,
                632e3: 18,
                19: 2.00e6,
                2.00e6: 19,
                20: 6.32e6,
                6.32e6: 20,
                21: 20.0e6,
                20.0e6: 21,
                22: 63.2e6,
                63.2e6: 22
                },
            'excitation': {
                'voltage': {
                    1: 2.0e-6,
                    2.0e-6: 1,
                    2: 6.32e-6,
                    6.32e-6: 2,
                    3: 20.0e-6,
                    20.0e-6: 3,
                    4: 63.2e-6,
                    63.2e-6: 4,
                    5: 200.0e-6,
                    200.0e-6: 5,
                    6: 632.0e-6,
                    632.0e-6: 6,
                    7: 2.0e-3,
                    2.0e-3: 7,
                    8: 6.32e-3,
                    6.32e-3: 8,
                    9: 20.0e-3,
                    20.0e-3: 9,
                    10: 63.2e-3,
                    63.2e-3: 10,
                    11: 200.0e-3,
                    200.0e-3: 11,
                    12: 632.0e-3,
                    632.0e-3: 12,
                    },
                'current': {
                    1: 1.0e-12,
                    1.0e-12: 1,
                    2: 3.16e-12,
                    3.16e-12: 2,
                    3: 10.0e-12,
                    10.0e-12: 3,
                    4: 31.6e-12,
                    31.6e-12: 4,
                    5: 100.0e-12,
                    100.0e-12: 5,
                    6: 316.0e-12,
                    316.0e-12: 6,
                    7: 1.0e-9,
                    1.0e-9: 7,
                    8: 3.16e-9,
                    3.16e-9: 8,
                    9: 10.0e-9,
                    10.0e-9: 9,
                    10: 31.6e-9,
                    31.6e-9: 10,
                    11: 100.0e-9,
                    100.0e-9: 11,
                    12: 316.0e-9,
                    316.0e-9: 12,
                    13: 1.0e-6,
                    1.0e-6: 13,
                    14: 3.16e-6,
                    3.16e-6: 14,
                    15: 10.0e-6,
                    10.0e-6: 15,
                    16: 31.6e-6,
                    31.6e-6: 16,
                    17: 100.0e-6,
                    100.0e-6: 17,
                    18: 316.0e-6,
                    316.0e-6: 18,
                    19: 1.0e-3,
                    1.0e-3: 19,
                    20: 3.16e-3,
                    3.16e-3: 20,
                    21: 10.0e-3,
                    10.0e-3: 21,
                    22: 31.6e-3,
                    31.6e-3: 22
                    }
                }
            }
        self.exceptions = ['analog_output', 'channel', 'cs_shunt', 'curve_number', 'curve_tempco']
        self.ls372_get_idn()
        self.ls372_populate_gui()

    def ls372_populate_gui(self):
        '''
        '''
        self.gb_initialize_panel('self')
        self.ls372_display_basic_info()
        self.ls372_channels_panel()
        self.ls372_analog_output_panel()

    def ls372_get_idn(self):
        '''
        '''
        self.serial_com.write('*idn? ')
        self.serial_number = self.serial_com.read()

    def ls372_display_basic_info(self):
        '''
        '''
        info_str = 'Com Port: {0}\nSerial Number: {1}'.format(self.com_port, self.serial_number)
        info_header_label = QtWidgets.QLabel(info_str, self)

        self.layout().addWidget(info_header_label, 0, 0, 1, 17)
        channels_header_label = QtWidgets.QLabel('Input Channels', self)
        channels_header_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout().addWidget(channels_header_label, 1, 0, 1, 17)
        analog_outputs_header_label = QtWidgets.QLabel('Analog Outputs', self)
        analog_outputs_header_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout().addWidget(analog_outputs_header_label, 18, 0, 1, 17)

    def ls372_channels_panel(self):
        '''
        '''
        self.headers = ['channel']
        for item in [x for x in dir(self.channels.channel_1) if not x.startswith('_')]:
            if item not in self.exceptions:
                self.headers.append(item)
        self.headers.append('Current Value')
        for i, header in enumerate(self.headers):
            header_label = QtWidgets.QLabel('{0}: '.format(header.title()), self)
            self.layout().addWidget(header_label, 2 + i, 0, 1, 1)
        self.headers.remove('Current Value')
        self.channel_indicies = [str(x) for x in range(1, 17)]
        for index in self.channel_indicies:
            channel_object = getattr(self.channels, 'channel_{0}'.format(index))
            for i, header in enumerate(self.headers):
                value = getattr(channel_object, header)
                if header in self.lakeshore372_command_dict:
                    if header == 'excitation':
                        value = self.lakeshore372_command_dict[header][exc_mode][value]
                    else:
                        value = self.lakeshore372_command_dict[header][value]
                    if header == 'exc_mode':
                        exc_mode = value
                value_label = QtWidgets.QLabel(str(value), self)
                self.layout().addWidget(value_label, 2 + i, int(index), 1, 1)
            current_value = self.channels.ls372_get_channel_value(index)
            if self.gb_is_float(current_value):
                current_value = '{0:.3f}'.format(float(current_value))
            current_value_label = QtWidgets.QLabel(str(current_value), self)
            self.layout().addWidget(current_value_label, 3 + i, int(index), 1, 1)
            edit_channel_pushbutton = QtWidgets.QPushButton('Edit Ch {0}'.format(index), self)
            edit_channel_pushbutton.clicked.connect(self.ls372_edit_channel)
            self.layout().addWidget(edit_channel_pushbutton, 4 + i, int(index), 1, 1)
            scan_channel_pushbutton = QtWidgets.QPushButton('Scan Ch {0}'.format(index), self)
            scan_channel_pushbutton.clicked.connect(self.ls372_scan_channel)
            self.layout().addWidget(scan_channel_pushbutton, 5 + i, int(index), 1, 1)
            update_channel_pushbutton = QtWidgets.QPushButton('Update Ch {0}'.format(index), self)
            update_channel_pushbutton.clicked.connect(self.ls372_update_channel_value)
            self.layout().addWidget(update_channel_pushbutton, 6 + i, int(index), 1, 1)

    def ls372_update_channel_value(self):
        '''
        '''
        index = self.sender().text().split(' ')[-1]
        self.set_to_channel = index
        if self.com_port == 'COM4':
            channel_readout_info = self.channels.ls372_get_channel_value(index, reading='kelvin')
        else:
            channel_readout_info = self.channels.ls372_get_channel_value(index, reading='resistance')

    def ls372_scan_channel(self):
        '''
        '''
        index = self.sender().text().split(' ')[-1]
        self.set_to_channel = index
        self.channels.ls372_scan_channel(index, autoscan=0)
        self.status_bar.showMessage('Scanning channel {0}'.format(index))

    def ls372_edit_channel(self, clicked, index=None):
        '''
        '''
        if index is None:
            index = self.sender().text().split(' ')[-1]
        self.set_to_channel = index
        editing_popup = QtWidgets.QMainWindow(self)
        ep_central_widget = QtWidgets.QWidget(editing_popup)
        grid = QtWidgets.QGridLayout()
        ep_central_widget.setLayout(grid)
        editing_popup.setCentralWidget(ep_central_widget)
        for i, header in enumerate(self.headers):
            header_label = QtWidgets.QLabel('{0}: '.format(header.title()), self)
            ep_central_widget.layout().addWidget(header_label, i, 0, 1, 1)
        channel_object = getattr(self.channels, 'channel_{0}'.format(index))
        for i, header in enumerate(self.headers):
            value = getattr(channel_object, header)
            if header in self.lakeshore372_command_dict:
                if header == 'excitation':
                    value = self.lakeshore372_command_dict[header][exc_mode][value]
                else:
                    value = self.lakeshore372_command_dict[header][value]
                if header == 'exc_mode':
                    exc_mode = value
            if header == 'channel':
                value_widget = QtWidgets.QLabel(str(value), editing_popup)
            elif header in ('dwell', 'pause', 'filter_settle_time', 'filter_window'):
                value_widget = QtWidgets.QLineEdit(str(value), editing_popup)
            else:
                if header in self.lakeshore372_command_dict:
                    if header == 'excitation':
                        valid_set_to_values = self.lakeshore372_command_dict[header][exc_mode].values()
                        valid_set_to_values = [x for x in valid_set_to_values if type(x) is not int]
                    elif header == 'resistance_range':
                        valid_set_to_values = self.lakeshore372_command_dict[header].values()
                        valid_set_to_values = [x for x in valid_set_to_values if type(x) is not int]
                    else:
                        valid_set_to_values = self.lakeshore372_command_dict[header].keys()
                        valid_set_to_values = [x for x in valid_set_to_values if type(x) is not int]
                value_widget = QtWidgets.QComboBox(editing_popup)
                for j, valid_set_to_value in enumerate(valid_set_to_values):
                    value_widget.addItem(str(valid_set_to_value))
                    if value == valid_set_to_value:
                        set_to_index = j
                value_widget.setCurrentIndex(set_to_index)
            ep_central_widget.layout().addWidget(value_widget, i, int(index), 1, 1)
        save_pushbutton = QtWidgets.QPushButton('SET', editing_popup)
        save_pushbutton.clicked.connect(lambda: self.ls372_update_channel(ep_central_widget, editing_popup))
        ep_central_widget.layout().addWidget(save_pushbutton, i + 1, int(index), 1, 1)
        editing_popup.move(250, 250)
        editing_popup.show()

    def ls372_update_channel(self, ep_central_widget, editing_popup):
        '''
        '''
        editing_popup.close()
        headers = []

        values = []
        for index in range(ep_central_widget.layout().count()):
            widget = ep_central_widget.layout().itemAt(index).widget()
            position = ep_central_widget.layout().getItemPosition(index)
            if hasattr(widget, 'text'):
                value = widget.text()
            else:
                value = widget.currentText()
            value = value.replace(': ', '')
            if position[1] == 0:
                headers.append(value)
            else:
                values.append(value)
        headers = [x.lower() for x in headers]
        new_settings = dict(zip(headers,values))
        for header in new_settings:
            if header in self.lakeshore372_command_dict:
                value = new_settings[header]
                if header == 'exc_mode':
                    exc_mode = copy(value)
                if header == 'excitation':
                    new_value = self.lakeshore372_command_dict[header][exc_mode][float(value)]
                elif header == 'resistance_range':
                    new_value = self.lakeshore372_command_dict[header][float(value)]
                else:
                    if value.isnumeric():
                        new_value = self.lakeshore372_command_dict[header][int(value)]
                    else:
                        new_value = self.lakeshore372_command_dict[header][value]
                new_settings[header] = new_value
        channel_object = getattr(self.channels, 'channel_{0}'.format(self.set_to_channel))
        self.status_bar.showMessage('Writing new settings to channel {0}'.format(self.set_to_channel))
        QtWidgets.QApplication.processEvents()
        self.channels.ls372_write_new_channel_settings(self.set_to_channel, new_settings, channel_object)
        self.channels.ls372_update_channels()
        self.ls372_populate_gui()
        self.ls372_edit_channel(clicked=False, index=self.set_to_channel)
        self.status_bar.showMessage('Wrote new settings to channel {0}'.format(self.set_to_channel))

    def ls372_analog_output_panel(self):
        '''
        '''
        self.analog_headers = ['analog_output']
        for item in [x for x in dir(self.analog_outputs.analog_output_sample) if not x.startswith('_')]:
            if item not in self.exceptions:
                self.analog_headers.append(item)
        for i, header in enumerate(self.analog_headers):
            header_label = QtWidgets.QLabel('{0}: '.format(header.title()), self)
            self.layout().addWidget(header_label, 19 + i, 0, 1, 1)
        for index, analog_output in enumerate(self.analog_output_indicies):
            analog_output_object = getattr(self.analog_outputs, 'analog_output_{0}'.format(analog_output))
            for i, header in enumerate(self.analog_headers):
                value = getattr(analog_output_object, header)
                if header in self.lakeshore372_command_dict:
                    value = self.lakeshore372_command_dict[header][value]
                value_label = QtWidgets.QLabel(str(value), self)
                self.layout().addWidget(value_label, 19 + i, index + 1, 1, 1)
            edit_analog_output_pushbutton = QtWidgets.QPushButton('Edit A0 {0}'.format(analog_output, self))
            edit_analog_output_pushbutton.clicked.connect(self.ls372_edit_analog_output)
            self.layout().addWidget(edit_analog_output_pushbutton, 20 + i, index + 1, 1, 1)

    def ls372_edit_analog_output(self, clicked=False, analog_output=None):
        '''
        '''
        if analog_output is None:
            analog_output = self.sender().text().split(' ')[-1]
        self.set_to_analog_output = analog_output
        editing_popup = QtWidgets.QMainWindow(self)
        ep_central_widget = QtWidgets.QWidget(editing_popup)
        grid = QtWidgets.QGridLayout()
        ep_central_widget.setLayout(grid)
        editing_popup.setCentralWidget(ep_central_widget)
        for i, header in enumerate(self.analog_headers):
            header_label = QtWidgets.QLabel('{0}: '.format(header.title()), self)
            ep_central_widget.layout().addWidget(header_label, i, 0, 1, 1)
        analog_output_object = getattr(self.analog_outputs, 'analog_output_{0}'.format(self.set_to_analog_output))
        for i, header in enumerate(self.analog_headers):
            value = getattr(analog_output_object, header)
            if header in self.lakeshore372_command_dict:
                value = self.lakeshore372_command_dict[header][value]
            if header == 'analog_output':
                value_widget = QtWidgets.QLabel(str(value), editing_popup)
            elif header in ['delay', 'high_value', 'low_value', 'manual_value']:
                value_widget = QtWidgets.QLineEdit(str(value), editing_popup)
            else:
                if header == 'input_channel':
                    valid_set_to_values = self.channel_indicies
                elif header in self.lakeshore372_command_dict:
                    valid_set_to_values = self.lakeshore372_command_dict[header].values()
                    valid_set_to_values = [x for x in valid_set_to_values if type(x) is not int]
                value_widget = QtWidgets.QComboBox(editing_popup)
                for j, valid_set_to_value in enumerate(valid_set_to_values):
                    value_widget.addItem(str(valid_set_to_value))
                    print()
                    print('value', value, type(value))
                    print('check_value', valid_set_to_value, type(valid_set_to_value))
                    print('analog output', analog_output)
                    print('--------')
                    if header == 'input_channel' and int(valid_set_to_value) == int(value):
                        set_to_index = j
                    elif valid_set_to_value == value:
                        set_to_index = j
                    elif valid_set_to_value == analog_output:
                        set_to_index = j
                print(header, set_to_index)
                value_widget.setCurrentIndex(set_to_index)
            ep_central_widget.layout().addWidget(value_widget, i, 1, 1, 1)
        save_pushbutton = QtWidgets.QPushButton('SET', editing_popup)
        save_pushbutton.clicked.connect(lambda: self.ls372_update_analog_output(ep_central_widget, editing_popup))
        ep_central_widget.layout().addWidget(save_pushbutton, i + 1, 1, 1, 1)
        editing_popup.move(250, 250)
        editing_popup.show()

    def ls372_update_analog_output(self, ep_central_widget, editing_popup):
        '''
        '''
        editing_popup.close()
        headers = []
        values = []
        for index in range(ep_central_widget.layout().count()):
            widget = ep_central_widget.layout().itemAt(index).widget()
            position = ep_central_widget.layout().getItemPosition(index)
            if hasattr(widget, 'text'):
                value = widget.text()
            else:
                value = widget.currentText()
            value = value.replace(': ', '')
            if position[1] == 0:
                headers.append(value)
            else:
                values.append(value)
        headers = [x.lower() for x in headers]
        new_settings = dict(zip(headers,values))
        for header in new_settings:
            value = new_settings[header]
            if header in self.lakeshore372_command_dict:
                new_value = self.lakeshore372_command_dict[header][value]
                new_settings[header] = new_value
        analog_output_object = getattr(self.analog_outputs, 'analog_output_{0}'.format(self.set_to_analog_output))
        self.status_bar.showMessage('Writing new settings to analog output {0}'.format(self.set_to_analog_output))
        QtWidgets.QApplication.processEvents()
        self.analog_outputs.ls372_write_analog_output_settings(self.set_to_analog_output, new_settings, analog_output_object)
        self.channels.ls372_scan_channel(new_settings['input_channel'], autoscan=0)
        self.analog_outputs.ls372_update_analog_outputs()
        self.ls372_populate_gui()
        self.ls372_edit_analog_output(clicked=False, analog_output=self.set_to_analog_output)
        self.status_bar.showMessage('Wrote new settings to analog output {0}'.format(self.set_to_analog_output))

class LS372Channels():

    def __init__(self, serial_com):
        '''
        '''
        self.channel_indicies = [str(x) for x in range(1, 17)]
        self.serial_com = serial_com
        self.ls372_update_channels()

    def ls372_update_channels(self):
        '''
        '''
        for index in self.channel_indicies:
            channel_object = GenericClass()
            channel_object = self.ls372_update_input_channel_settings(index, channel_object)
            setattr(self, 'channel_{0}'.format(index), channel_object)

    def ls372_update_input_channel_settings(self, index, channel_object):
        '''
        '''
        self.serial_com.write("inset? {0}".format(index))
        input_setup_config = self.serial_com.read()
        setattr(channel_object, 'channel', index)
        setattr(channel_object, 'enabled', int(input_setup_config.split(',')[0]))
        setattr(channel_object, 'dwell', float(input_setup_config.split(',')[1]))
        setattr(channel_object, 'pause', float(input_setup_config.split(',')[2]))
        setattr(channel_object, 'curve_number', int(input_setup_config.split(',')[3]))
        setattr(channel_object, 'curve_tempco', int(input_setup_config.split(',')[4]))
        self.serial_com.write("intype? {0}".format(index))
        input_config = self.serial_com.read()
        setattr(channel_object, 'exc_mode', int(input_config.split(',')[0]))
        setattr(channel_object, 'excitation', int(input_config.split(',')[1]))
        setattr(channel_object, 'autorange', int(input_config.split(',')[2]))
        setattr(channel_object, 'resistance_range', int(input_config.split(',')[3]))
        setattr(channel_object, 'cs_shunt', int(input_config.split(',')[4]))
        setattr(channel_object, 'units', int(input_config.split(',')[5]))
        self.serial_com.write("filter? {0}".format(index))
        filter_setup_config = self.serial_com.read()
        setattr(channel_object, 'filter_on', int(filter_setup_config.split(',')[0]))
        setattr(channel_object, 'filter_settle_time', float(filter_setup_config.split(',')[1]))
        setattr(channel_object, 'filter_window', float(filter_setup_config.split(',')[2]))
        return channel_object

    def ls372_get_channel_value(self, index, reading='resistance'):
        '''
        '''
        #self.serial_com.write('scan {0},0 '. format(index))
        #scan_status = self.serial_com.read()
        self.serial_com.write('rdgst? {0} '. format(index))
        sensor_status = self.serial_com.read()
        if reading == 'resistance':
            self.serial_com.write('rdgr? {0} '. format(index))
            sensor_value = self.serial_com.read()
        elif reading == 'kelvin':
            self.serial_com.write('krdg? {0} '. format(index))
            sensor_value = self.serial_com.read()
        if sensor_status == '000':
            channel_readout_info = sensor_value
        else:
            channel_readout_info = 'error'
        return channel_readout_info

    def ls372_scan_channel(self, index, autoscan=0):
        '''
        '''
        scan_cmd = 'scan {0},{1} '.format(index, autoscan)
        self.serial_com.write(scan_cmd)
        self.serial_com.read()

    def ls372_write_new_channel_settings(self, set_to_channel, new_settings, channel_object):
        '''
        Page 165 of manual
        '''
        intype_cmd = 'intype {0},{1},{2},{3},{4},{5},{6} '.format(set_to_channel,
                                                                  new_settings['exc_mode'],
                                                                  new_settings['excitation'],
                                                                  new_settings['autorange'],
                                                                  new_settings['resistance_range'],
                                                                  channel_object.cs_shunt,
                                                                  new_settings['units'],
                                                                  )
        self.serial_com.write(intype_cmd)
        result = self.serial_com.read()
        inset_cmd = 'inset {0},{1},{2},{3},{4},{5} '.format(set_to_channel,
                                                            new_settings['enabled'],
                                                            new_settings['dwell'],
                                                            new_settings['pause'],
                                                            channel_object.curve_number,
                                                            channel_object.curve_tempco
                                                            )
        self.serial_com.write(inset_cmd)
        result = self.serial_com.read()

class LS372AnalogOutputs():

    def __init__(self, serial_com):
        '''
        '''
        self.analog_output_indicies = [str(x) for x in range(1, 4)]
        self.analog_output_indicies = ['sample', 'warmup', 'aux']
        self.serial_com = serial_com
        self.ls372_update_analog_outputs()

    def ls372_update_analog_outputs(self):
        '''
        '''
        for index, analog_output in enumerate(self.analog_output_indicies):
            analog_output_object = GenericClass()
            analog_output_object = self.ls372_update_analog_output_settings(index, analog_output, analog_output_object)
            setattr(self, 'analog_output_{0}'.format(analog_output), analog_output_object)

    def ls372_update_analog_output_settings(self, index, analog_output, analog_output_object):
        '''
        '''
        self.serial_com.write( "analog? {0}".format(index))
        analog_output_config = self.serial_com.read()
        setattr(analog_output_object, 'analog_output', analog_output)
        setattr(analog_output_object, 'polarity', int(analog_output_config.split(',')[0]))
        setattr(analog_output_object, 'analog_mode', int(analog_output_config.split(',')[1]))
        setattr(analog_output_object, 'input_channel', int(analog_output_config.split(',')[2]))
        setattr(analog_output_object, 'source', int(analog_output_config.split(',')[3]))
        setattr(analog_output_object, 'high_value', float(analog_output_config.split(',')[4]))
        setattr(analog_output_object, 'low_value', float(analog_output_config.split(',')[5]))
        setattr(analog_output_object, 'manual_value', float(analog_output_config.split(',')[6]))
        self.serial_com.write( "outmode? {0}".format(index))
        outmode_config = self.serial_com.read()
        setattr(analog_output_object, 'powerup_enable', int(outmode_config.split(',')[2]))
        setattr(analog_output_object, 'filter_on', int(outmode_config.split(',')[4]))
        setattr(analog_output_object, 'delay', int(outmode_config.split(',')[5]))
        return analog_output_object

    def ls372_write_analog_output_settings(self, set_to_channel, new_settings, channel_object):
        '''
        '''
        set_to_channel_dict = {
            'aux': 2,
            'warmup': 1,
            'sample': 0
            }
        set_to_channel = set_to_channel_dict[set_to_channel]
        analog_cmd = 'analog {0},{1},{2},{3},{4},{5},{6},{7} '.format(set_to_channel,
                                                                      new_settings['polarity'],
                                                                      new_settings['analog_mode'],
                                                                      new_settings['input_channel'],
                                                                      new_settings['source'],
                                                                      new_settings['high_value'],
                                                                      new_settings['low_value'],
                                                                      new_settings['manual_value'],
                                                                      )
        print(analog_cmd)
        self.serial_com.write(analog_cmd)
        result = self.serial_com.read()
        outmode_cmd = 'outmode {0},{1},{2},{3},{4},{5},{6} '.format(set_to_channel,
                                                                    new_settings['analog_mode'],
                                                                    new_settings['input_channel'],
                                                                    new_settings['powerup_enable'],
                                                                    new_settings['polarity'],
                                                                    new_settings['filter_on'],
                                                                    new_settings['delay'],
                                                                    )
        print(outmode_cmd)
        self.serial_com.write(outmode_cmd)
        result = self.serial_com.read()


