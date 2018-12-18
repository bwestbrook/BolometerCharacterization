from libraries.gen_class import Class

time_constant_settings = Class()

time_constant_settings.time_constant_popup_build_dict = {
                                                         '_common_settings': {'font': 'huge'},
                                                         '_time_constant_popup_hardware_label': {'text': 'HARDWARE SETUP',

                                                                                                 'font': 'huge', 'color': 'Blue', 'position': (0, 0, 1, 4)},
                                                         # HARDWARE SETUP 
                                                         '_time_constant_popup_daq_select_header_label': {'text': 'DAQ:', 'alignment': 'Right', 'position': (2, 0, 1, 1)},
                                                         '_time_constant_popup_daq_select_combobox': {'position': (2, 1, 1, 1)},

                                                         '_time_constant_popup_daq_integration_time_header_label': {'text': 'Integration Time (ms):', 'alignment': 'Right', 'position': (2, 2, 1, 1)},
                                                         '_time_constant_popup_daq_integration_time_lineedit': {'text': '50', 'position': (2, 3, 1, 1)},

                                                         '_time_constant_popup_frequency_select_header_label': {'text': 'Frequency (Hz)', 'alignment': 'Right', 'position': (3, 0, 1, 1)},
                                                         '_time_constant_popup_frequency_select_combobox': {'position': (3, 1, 1, 1)},

                                                         # DATA SETUP 
                                                         '_time_constant_popup_raw_data_path_pushbutton': {'text': 'Set Data Path:', 'function': '_get_raw_data_save_path', 'position': (4, 0, 1, 1)},
                                                         '_time_constant_popup_raw_data_path_label': {'text': 'You must set a data path', 'font': 'med', 'position': (4, 1, 1, 1)},

                                                         '_time_constant_popup_bolo_name_header_label': {'text': 'Bolo Name:', 'alignment': 'Right', 'position': (5, 0, 1, 1)},
                                                         '_time_constant_popup_bolo_name_lineedit': {'text': 'Test Bolo', 'position': (5, 1, 1, 1)},

                                                         '_time_constant_popup_voltage_bias_header_label': {'text': 'Voltage Bias (uV)', 'alignment': 'Right', 'position': (5, 2, 1, 1)},
                                                         '_time_constant_popup_voltage_bias_lineedit': {'text': '4.0', 'position': (5, 3, 1, 1)},

                                                         # CONTROLS 
                                                         '_time_constant_popup_take_data_point_pushbutton': {'text': 'Take Data', 'function': '_take_time_constant_data_point', 'position': (7, 0, 1, 4)},
                                                         '_time_constant_popup_delete_last_data_point_pushbutton': {'text': 'Delete Last Point', 'function': '_delete_last_point', 'position': (8, 0, 1, 4)},
                                                         '_time_constant_popup_take_close_pushbutton': {'text': 'Close', 'function': '_close_time_constant', 'position': (9, 0, 1, 4)},

                                                         # DATA MONITOR 
                                                         '_time_constant_popup_data_monitor_header_label': {'text': 'VISUAL DATA MONITOR', 'alignment': 'Center', 'color': 'Blue', 'position': (0, 5, 1, 4)},

                                                         '_time_constant_popup_data_point_monitor_label': {'text': '', 'position': (2, 5, 4, 4)},

                                                         '_time_constant_popup_data_point_mean_header_label': {'text': 'Mean:', 'alignment': 'Right', 'position': (6, 5, 1, 1)},
                                                         '_time_constant_popup_data_point_mean_label': {'text': '', 'position': (6, 6, 1, 1)},

                                                         '_time_constant_popup_data_point_std_header_label': {'text': 'STD:', 'alignment': 'Right', 'position': (6, 7, 1, 1)},
                                                         '_time_constant_popup_data_point_std_label': {'text': '', 'position': (6, 8, 1, 1)},

                                                         '_time_constant_popup_all_data_monitor_label': {'text': '', 'position': (7, 5, 3, 4)}, # Final Plot
                                                         }

time_constant_settings.time_constant_comobobox_entry_dict = {
                                                             '_time_constant_popup_frequency_select_combobox': ['2', '4', '8', '16', '32', '64', '128', '256'],
                                                             '_time_constant_popup_daq_select_combobox': ['0', '1', '2', '3', '4', '5', '6', '7'],
                                                             }
