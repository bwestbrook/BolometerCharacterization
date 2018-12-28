from libraries.gen_class import Class

multimeter_settings = Class()

multimeter_settings.multimeter_popup_build_dict = {
                                                         '_common_settings': {'font': 'huge'},
                                                         '_multimeter_popup_hardware_label': {'text': 'HARDWARE SETUP', 'alignment': 'Center',
                                                                                                 'font': 'huge', 'color': 'Blue', 'position': (0, 0, 1, 4)},
                                                         # HARDWARE SETUP 
                                                         '_multimeter_popup_daq_channel_1_header_label': {'text': 'DAQ:', 'position': (2, 0, 1, 1)},
                                                         '_multimeter_popup_daq_channel_1_combobox': {'position': (2, 1, 1, 1)},

                                                         '_multimeter_popup_daq_integration_time_1_header_label': {'text': 'Integration Time (ms):','position': (3, 0, 1, 1)},
                                                         '_multimeter_popup_daq_integration_time_1_combobox': {'position': (3, 1, 1, 1)},

                                                         '_multimeter_popup_daq_sample_rate_1_header_label': {'text': 'Sample Rate:', 'position': (3, 2, 1, 1)},
                                                         '_multimeter_popup_daq_sample_rate_1_combobox': {'position': (3, 3, 1, 1)},

                                                         '_multimeter_popup_grt_serial_1_header_label': {'text': 'GRT Serial (Blank == None):', 'position': (3, 4, 1, 1)},
                                                         '_multimeter_popup_grt_serial_1_combobox': {'position': (3, 5, 1, 1)},

                                                         '_multimeter_popup_daq_channel_2_header_label': {'text': 'DAQ:', 'position': (4, 0, 1, 1)},
                                                         '_multimeter_popup_daq_channel_2_combobox': {'position': (4, 1, 1, 1)},

                                                         '_multimeter_popup_daq_integration_time_2_header_label': {'text': 'Integration Time (ms):','position': (5, 0, 1, 1)},
                                                         '_multimeter_popup_daq_integration_time_2_combobox': {'position': (5, 1, 1, 1)},

                                                         '_multimeter_popup_daq_sample_rate_2_header_label': {'text': 'Sample Rate:', 'position': (5, 2, 1, 1)},
                                                         '_multimeter_popup_daq_sample_rate_2_combobox': {'position': (5, 3, 1, 1)},

                                                         '_multimeter_popup_grt_serial_2_header_label': {'text': 'GRT Serial (Blank == None):', 'position': (5, 4, 1, 1)},
                                                         '_multimeter_popup_grt_serial_2_combobox': {'position': (5, 5, 1, 1)},

                                                         # CONTROLS 
                                                         '_multimeter_popup_get_data_pushbutton': {'text': 'Get DAQ Output', 'function': '_take_multimeter_data_point', 'position': (7, 0, 1, 4)},
                                                         '_multimeter_popup_stop_pushbutton': {'text': 'Stop', 'function': '_stop', 'position': (8, 0, 1, 4)},
                                                         '_multimeter_popup_take_close_pushbutton': {'text': 'Close', 'function': '_close_multimeter', 'position': (10, 0, 1, 4)},

                                                         # DATA MONITOR 
                                                         '_multimeter_popup_data_monitor_header_label': {'text': 'VISUAL DATA MONITOR', 'alignment': 'Center', 'color': 'Blue', 'position': (0, 6, 1, 4)},

                                                         '_multimeter_popup_data_point_monitor_1_label': {'text': '', 'position': (2, 6, 4, 4)},

                                                         '_multimeter_popup_data_point_mean_1_header_label': {'text': 'Mean:', 'position': (6, 6, 1, 1)},
                                                         '_multimeter_popup_data_point_mean_1_label': {'text': '', 'position': (6, 7, 1, 1)},

                                                         '_multimeter_popup_data_point_std_1_header_label': {'text': 'STD:', 'position': (6, 8, 1, 1)},
                                                         '_multimeter_popup_data_point_std_1_label': {'text': '', 'position': (6, 9, 1, 1)},

                                                         '_multimeter_popup_data_point_monitor_2_label': {'text': '', 'position': (7, 6, 4, 4)},

                                                         '_multimeter_popup_data_point_mean_2_header_label': {'text': 'Mean:', 'position': (11, 6, 1, 1)},
                                                         '_multimeter_popup_data_point_mean_2_label': {'text': '', 'position': (11, 7, 1, 1)},

                                                         '_multimeter_popup_data_point_std_2_header_label': {'text': 'STD:', 'position': (11, 8, 1, 1)},
                                                         '_multimeter_popup_data_point_std_2_label': {'text': '', 'position': (11, 9, 1, 1)},

                                                         }

multimeter_settings.multimeter_combobox_entry_dict = {
                                                      '_multimeter_popup_daq_channel_1_combobox': ['0', '1', '2', '3', '4', '5', '6', '7'],
                                                      '_multimeter_popup_daq_channel_2_combobox': ['0', '1', '2', '3', '4', '5', '6', '7'],
                                                      '_multimeter_popup_daq_sample_rate_1_combobox': ['50', '500', '1000'],
                                                      '_multimeter_popup_daq_sample_rate_2_combobox': ['50', '500', '1000'],
                                                      '_multimeter_popup_daq_integration_time_1_combobox': ['50', '500', '1000', '10000', '200000'],
                                                      '_multimeter_popup_daq_integration_time_2_combobox': ['50', '500', '1000', '10000', '200000'],
                                                      '_multimeter_popup_grt_serial_1_combobox': ['', '29268'],
                                                      '_multimeter_popup_grt_serial_2_combobox': ['', '29268'],
                                                      }
