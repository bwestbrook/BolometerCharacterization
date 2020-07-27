from libraries.gen_class import Class

multimeter_settings = Class()

multimeter_settings.multimeter_popup_build_dict = {
    '_common_settings': {
        'font': 'huge'
        },
    '_BD_multimeter_popup_hardware_label': {
        'text': 'HARDWARE SETUP',
        'alignment': 'Center', 'font': 'huge',
        'color': 'Blue',
        'position': (0, 0, 1, 4)
        },
    # HARDWARE SETUP 
    '_BD_multimeter_popup_daq_channel_1_header_label': {
        'text': 'DAQ:',
        'position': (2, 0, 1, 1)
        },
    '_BD_multimeter_popup_daq_channel_1_combobox': {
        'position': (2, 1, 1, 1)
        },
    '_BD_multimeter_popup_daq_integration_time_1_header_label': {
        'text': 'Integration Time (ms):',
        'position': (3, 0, 1, 1)
        },
    '_BD_multimeter_popup_daq_integration_time_1_combobox': {
        'position': (3, 1, 1, 1)
        },
    '_BD_multimeter_popup_daq_sample_rate_1_header_label': {
        'text': 'Sample Rate:',
        'position': (3, 2, 1, 1)
        },
    '_BD_multimeter_popup_daq_sample_rate_1_combobox': {
        'position': (3, 3, 1, 1)
        },
    '_BD_multimeter_popup_grt_serial_1_header_label': {
        'text': 'GRT Serial (Blank == None):',
        'position': (4, 0, 1, 1)
        },
    '_BD_multimeter_popup_grt_serial_1_combobox': {
        'position': (4, 1, 1, 1)
        },
    '_BD_multimeter_popup_grt_range_1_header_label': {
        'text': 'GRT Range',
        'position': (4, 2, 1, 1)
        },
    '_BD_multimeter_popup_grt_range_1_combobox': {
        'position': (4, 3, 1, 1)
        },
    '_BD_multimeter_popup_daq_channel_2_header_label': {
        'text': 'DAQ:',
        'position': (6, 0, 1, 1)
        },
    '_BD_multimeter_popup_daq_channel_2_combobox': {
        'position': (6, 1, 1, 1)
        },
    '_BD_multimeter_popup_daq_integration_time_2_header_label': {
        'text': 'Integration Time (ms):',
        'position': (7, 0, 1, 1)
        },
    '_BD_multimeter_popup_daq_integration_time_2_combobox': {
        'position': (7, 1, 1, 1)
        },
    '_BD_multimeter_popup_daq_sample_rate_2_header_label': {
        'text': 'Sample Rate:',
        'position': (7, 2, 1, 1)
        },
    '_BD_multimeter_popup_daq_sample_rate_2_combobox': {
        'position': (7, 3, 1, 1)
        },
    '_BD_multimeter_popup_grt_serial_2_header_label': {
        'text': 'GRT Serial (Blank == None):',
        'position': (8, 0, 1, 1)
        },
    '_BD_multimeter_popup_grt_serial_2_combobox': {
        'position': (8, 1, 1, 1)
        },
    '_BD_multimeter_popup_grt_range_2_header_label': {
        'text': 'GRT Range',
        'position': (8, 2, 1, 1)
        },
    '_BD_multimeter_popup_grt_range_2_combobox': {
        'position': (8, 3, 1, 1)
        },
    # CONTROLS 
    '_BD_multimeter_popup_get_data_pushbutton': {
        'text': 'Get DAQ Output',
        'function': 'bd_take_multimeter_data_point',
        'position': (10, 0, 1, 10)
        },
    '_BD_multimeter_popup_stop_pushbutton': {
        'text': 'Stop',
        'function': 'bd_stop',
        'position': (11, 0, 1, 10)
        },
    '_BD_multimeter_popup_take_close_pushbutton': {
        'text': 'Close',
        'function': 'bd_close_multimeter',
        'position': (12, 0, 1, 10)
        },
    # DATA MONITOR 
    '_BD_multimeter_popup_data_monitor_header_label': {
        'text': 'VISUAL DATA MONITOR',
        'alignment': 'Center',
        'color': 'Blue',
        'position': (0, 6, 1, 4)
        },
    '_BD_multimeter_popup_data_point_monitor_1_label': {
        'position': (2, 6, 3, 4)
        },
    '_BD_multimeter_popup_data_point_mean_1_header_label': {
        'text': 'Mean:',
        'position': (5, 6, 1, 1)
        },
    '_BD_multimeter_popup_data_point_mean_1_label': {
        'text': '',
        'position': (5, 7, 1, 1)
        },
    '_BD_multimeter_popup_data_point_std_1_header_label': {
        'text': 'STD:',
        'position': (5, 8, 1, 1)},
    '_BD_multimeter_popup_data_point_std_1_label': {
        'position': (5, 9, 1, 1)
        },
    '_BD_multimeter_popup_data_point_monitor_2_label': {
        'position': (6, 6, 3, 4)
        },
    '_BD_multimeter_popup_data_point_mean_2_header_label': {
        'text': 'Mean:',
        'position': (9, 6, 1, 1)
        },
    '_BD_multimeter_popup_data_point_mean_2_label': {
        'position': (9, 7, 1, 1)
        },
    '_BD_multimeter_popup_data_point_std_2_header_label': {
        'text': 'STD:',
        'position': (9, 8, 1, 1)
        },
    '_BD_multimeter_popup_data_point_std_2_label': {
        'position': (9, 9, 1, 1)
        }
}

multimeter_settings.multimeter_combobox_entry_dict = {
    '_BD_multimeter_popup_daq_channel_1_combobox': ['0', '1', '2', '3', '4', '5', '6', '7'],
    '_BD_multimeter_popup_daq_channel_2_combobox': ['0', '1', '2', '3', '4', '5', '6', '7'],
    '_BD_multimeter_popup_daq_sample_rate_1_combobox': ['50', '500', '1000', '5000'],
    '_BD_multimeter_popup_daq_sample_rate_2_combobox': ['50', '500', '1000', '5000'],
    '_BD_multimeter_popup_daq_integration_time_1_combobox': ['50', '500', '1000', '10000', '100000'],
    '_BD_multimeter_popup_daq_integration_time_2_combobox': ['50', '500', '1000', '10000', '100000'],
    '_BD_multimeter_popup_grt_serial_1_combobox': ['', '29268', 'X36942'],
    '_BD_multimeter_popup_grt_serial_2_combobox': ['', '29268', 'X36942'],
    '_BD_multimeter_popup_grt_range_1_combobox': ['2', '20', '200', '2K', '20K', '200K', '2M'],
    '_BD_multimeter_popup_grt_range_2_combobox': ['2', '20', '200', '2K', '20K', '200K', '2M'],
}

multimeter_settings.multimeter_voltage_factor_range_dict = {
    '2': 1.0,
    '20': 10.0,
    '200': 1e2,
    '2K': 1e3,
    '20K': 1e4,
    '200K': 1e5,
    '2M': 1e6,
}

