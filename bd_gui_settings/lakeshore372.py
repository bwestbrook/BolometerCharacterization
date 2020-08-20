from GuiBuilder.gui_builder import GenericClass

lakeshore372_settings = GenericClass()

lakeshore372_settings.lakeshore372_popup_build_dict = {
    '_common_settings': {
        'font': 'huge'
        },
    '_BD_lakeshore372_popup_info_header_label': {
        'text': 'Basic Information',
        'alignment': 'Center',
        'color': 'Blue',
        'position': (0, 0, 1, 4)
        },
    '_BD_lakeshore372_popup_info_label': {
        'font': 'huge',
        'position': (1, 0, 1, 4)
        },
    '_BD_lakeshore372_popup_analog_output_config_header_label': {
        'text': 'Analog Output Config',
        'alignment': 'Center',
        'color': 'Blue',
        'position': (2, 0, 1, 4)
        },
    '_BD_lakeshore372_popup_analog_output_header_label': {
        'text': 'Analog Out Monitor Channel:',
        'position': (3, 0, 1, 1)
        },
    '_BD_lakeshore372_popup_analog_output_monitor_combobox': {
        'function': 'bd_set_analog_output',
        'position': (3, 1, 1, 3)
        },
    '_BD_lakeshore372_popup_high_v_header_label': {
        'text': 'High V set point',
        'position': (4, 0, 1, 1)
        },
    '_BD_lakeshore372_popup_high_v_combobox': {
        'function': 'bd_set_high_v_for_output',
        'position': (4, 1, 1, 3)
        },
    '_BD_lakeshore372_popup_analog_conversion_label': {
        'position': (5, 0, 1, 4)
        },
    '_BD_lakeshore372_popup_channels_header_label': {
        'text': 'Channel Config',
        'alignment': 'Center',
        'color': 'Blue',
        'position': (6, 0, 1, 4)
        },
    '_BD_lakeshore372_popup_input_channels_header_label': {
        'text': 'Input Channel:',
        'position': (7, 0, 1, 1)
        },
    '_BD_lakeshore372_popup_input_channels_combobox': {
        'function': 'bd_update_input_channel_settings',
        'position': (7, 1, 1, 3)
        },
    '_BD_lakeshore372_popup_channel_excitation_type_header_label': {
        'text': 'Excitation Type:',
        'position': (8, 0, 1, 1)
        },
    '_BD_lakeshore372_popup_channel_excitation_type_combobox': {
        'position': (8, 1, 1, 3)
        },
    '_BD_lakeshore372_popup_channel_excitation_header_label': {
        'text': 'Excitation',
        'position': (9, 0, 1, 1)
        },
    '_BD_lakeshore372_popup_channel_excitation_combobox': {
        'position': (9, 1, 1, 3)
        },
    '_BD_lakeshore372_popup_channel_resistance_range_header_label': {
        'text': 'Resistance Range (Ohms)',
        'position': (10, 0, 1, 1)
        },
    '_BD_lakeshore372_popup_channel_resistance_range_combobox': {
        'position': (10, 1, 1, 3)
        },
}


channels = [str(x) for x in range(1, 17)]

lakeshore372_settings.lakeshore372_analog_output_dict = {
    'analog_channel': {
        'warm_up': 0,
        'sample': 1,
        'still': 2
        },
    'exc_mode': {
        'voltage': '0',
        'current': '1',
        '0': 'voltage',
        '1': 'current'
        },
    'mode': {
        'output_off': 0,
        'monitor': 1,
        'open_loop': 2,
        'zone': 3,
        'still': 4,
        'closed_loop': 5,
        'warm_up': 5,
        },
    'polarity': {
        'unipolar': 0,
        'bipolar': 1
        },
    'filter': {
        'unfiltered': 0,
        'filtered': 1
        },
    'source': {
        '1': 'kelvin',
        '2': 'Ohms',
        'kelvin': '1',
        'Kelvin': '1',
        'ohms': '2',
        'Ohms': '2',
        },
    }

lakeshore372_settings.ls372_resistance_range_dict = {
    '1': 2.0e-3,
    '2': 6.32e-3,
    '3': 20.0e-3,
    '4': 63.2e-3,
    '5': 200e-3,
    '6': 632e-3,
    '7': 2.0,
    '8': 6.3,
    '9': 20,
    '10': 63,
    '11': 20,
    '12': 63,
    '13': 2.00e3,
    '14': 6.32e3,
    '15': 20.0e3,
    '16': 63.2e3,
    '17': 200e3,
    '18': 632e3,
    '19': 2.00e6,
    '20': 6.32e6,
    '21': 20.0e6,
    '22': 63.2e6,
}

lakeshore372_settings.ls372_voltage_excitation_dict = {
    '1': 2.0e-6,
    '2': 6.32e-6,
    '3': 20.0e-6,
    '4': 63.2e-6,
    '5': 200.0e-6,
    '6': 632.0e-6,
    '7': 2.0e-3,
    '8': 6.32e-3,
    '9': 20.0e-3,
    '10': 63.2e-3,
    '11': 200.0e-3,
    '12': 632.0e-3
}

lakeshore372_settings.ls372_current_excitation_dict = {
    '1': 1.0e-12,
    '2': 3.16e-12,
    '3': 10.0e-12,
    '4': 31.6e-12,
    '5': 100.0e-12,
    '6': 316.0e-12,
    '7': 1.0e-9,
    '8': 3.16e-9,
    '9': 10.0e-9,
    '10': 31.6e-9,
    '11': 100.0e-9,
    '12': 316.0e-9,
    '13': 1.0e-6,
    '14': 3.16e-6,
    '15': 10.0e-6,
    '16': 31.6e-6,
    '17': 100.0e-6,
    '18': 316.0e-6,
    '19': 1.0e-3,
    '20': 3.16e-3,
    '21': 10.0-3,
    '22': 31.6-3}

lakeshore372_settings.current_excitations = [str(x) for x in lakeshore372_settings.ls372_current_excitation_dict.values()]
lakeshore372_settings.voltage_excitations = [str(x) for x in lakeshore372_settings.ls372_voltage_excitation_dict.values()]
lakeshore372_settings.resistance_ranges = [str(x) for x in lakeshore372_settings.ls372_resistance_range_dict.values()]

lakeshore372_settings.lakeshore372_combobox_entry_dict = {
    '_BD_lakeshore372_popup_input_channels_combobox': channels,
    '_BD_lakeshore372_popup_analog_output_monitor_combobox': channels,
    '_BD_lakeshore372_popup_high_v_combobox': [
        '0.1', #10V = 0.1 Ohms
        '1.0', #10V = 1.0 Ohms
        '10', #10V = 10.0 Ohms
        ],
    '_BD_lakeshore372_popup_channel_resistance_range_combobox': lakeshore372_settings.resistance_ranges,
    '_BD_lakeshore372_popup_channel_excitation_combobox': lakeshore372_settings.current_excitations,
    '_BD_lakeshore372_popup_channel_excitation_type_combobox': ['current', 'voltage']
    }
