from libraries.gen_class import Class

xycollector_settings = Class()

xycollector_settings.xycollector_build_dict = {
                                                             '_common_settings': {'font': 'large'},
# HARDWARE SETUP 
                                                             '_xycollector_popup_hardware_setup_label': {'text': 'HARDWARE SETUP', 'font': 'huge', 'color': 'blue',
                                                                                                         'alignment': 'Center', 'position': (0, 0, 1, 2)},

                                                             '_xycollector_popup_mode_header_label': {'text': 'XY Mode:', 'position': (1, 0, 1, 1)},
                                                             '_xycollector_popup_mode_combobox': {'function': '_update_in_xy_mode', 'position': (1, 1, 1, 1)},

                                                             '_xycollector_popup_daq_channel_x_header_label': {'text': 'DAQ Channel X:', 'position': (2, 0, 1, 1)},
                                                             '_xycollector_popup_daq_channel_x_combobox': { 'position': (2, 1, 1, 1)},

                                                             '_xycollector_popup_daq_channel_y_header_label': {'text': 'DAQ Channel Y:', 'position': (3, 0, 1, 1)},
                                                             '_xycollector_popup_daq_channel_y_combobox': { 'position': (3, 1, 1, 1)},

                                                             '_xycollector_popup_daq_integration_time_header_label': {'text': 'Integration Time (ms) [min 40ms]:', 'position': (4, 0, 1, 1)},
                                                             '_xycollector_popup_daq_integration_time_lineedit': {'text': '50',  'function': '_force_min_time', 'position': (4, 1, 1, 1)},

                                                             '_xycollector_popup_squid_header_label': {'text': 'SQUID:', 'position': (5, 0, 1, 1)},
                                                             '_xycollector_popup_squid_select_combobox': {'function': '_update_squid_calibration', 'position': (5, 1, 1, 1)},

                                                             '_xycollector_popup_squid_conversion_header_label': {'text': 'SQUID Calibration:', 'position': (6, 0, 1, 1)},
                                                             '_xycollector_popup_squid_conversion_label': {'position': (6, 1, 1, 1)},

                                                             '_xycollector_popup_voltage_factor_header_label': {'text': 'Voltage Factor:', 'position': (7, 0, 1, 1)},
                                                             '_xycollector_popup_voltage_factor_combobox': {'position': (7, 1, 1, 1)},
# PLOT SETUP 
                                                             '_xycollector_popup_sample_name_header_label': {'text': 'Sample Name:', 'position': (8, 0, 1, 1)},
                                                             '_xycollector_popup_sample_name_lineedit': {'text': '', 'position': (8, 1, 1, 1)},

# CONTROL BUTTONS 
                                                             '_xycollector_popup_control_buttons_label': {'text': 'CONTROLS', 'font': 'huge', 'color': 'blue',
                                                                                                          'alignment': 'Center', 'position': (9, 0, 1, 2)},
                                                             '_xycollector_popup_start_pushbutton': {'text': 'Start', 'function': '_run_xycollector', 'position': (10, 0, 1, 1)},

                                                             '_xycollector_popup_pause_pushbutton': {'text': 'Stop', 'function': '_stop', 'position': (10, 1, 1, 1)},

                                                             '_xycollector_popup_save_pushbutton': {'text': 'Save', 'function': '_final_plot', 'position': (11, 0, 1, 2)},

                                                             '_xycollector_popup_close_pushbutton': {'text': 'Close', 'function': '_close_xycollector', 'position': (12, 0, 1, 2)},

# VISUAL DATA MONITORING
                                                             '_xycollector_popup_data_monitor_label': {'text': 'VISUAL DATA MONITOR', 'font': 'huge', 'color': 'blue',
                                                                                                              'alignment': 'Center', 'position': (0, 2, 1, 6)},

                                                             '_xycollector_popup_xdata_label': {'alignment': 'Center', 'position': (1, 2, 3, 6)},

                                                             '_xycollector_popup_xdata_mean_header_label': {'text': 'AVG:', 'alignment': 'Right', 'position': (4, 2, 1, 1)},
                                                             '_xycollector_popup_xdata_mean_label': {'alignment': 'Left', 'position': (4, 3, 1, 1)},

                                                             '_xycollector_popup_xdata_std_header_label': {'text': 'STD', 'alignment': 'Right', 'position': (4, 4, 1, 1)},
                                                             '_xycollector_popup_xdata_std_label': {'alignment': 'Left', 'position': (4, 5, 1, 1)},

                                                             '_xycollector_popup_ydata_label': {'alignment': 'Center', 'position': (5, 2, 3, 6)},

                                                             '_xycollector_popup_ydata_mean_header_label': {'text': 'AVG:', 'alignment': 'Right', 'position': (8, 2, 1, 1)},
                                                             '_xycollector_popup_ydata_mean_label': {'alignment': 'Left', 'position': (8, 3, 1, 1)},

                                                             '_xycollector_popup_ydata_std_header_label': {'text': 'STD', 'alignment': 'Right', 'position': (8, 4, 1, 1)},
                                                             '_xycollector_popup_ydata_std_label': {'alignment': 'Left', 'position': (8, 5, 1, 1)},

                                                             '_xycollector_popup_xydata_label': {'alignment': 'Center', 'position': (10, 2, 3, 6)},

}



xycollector_settings.xycollector_combobox_entry_dict = {
                                                        '_xycollector_popup_mode_combobox': ['IV', 'RT', 'Discrete'],
                                                        '_xycollector_popup_daq_channel_x_combobox': ['0', '1', '2', '3', '4', '5', '6', '7'],
                                                        '_xycollector_popup_daq_channel_y_combobox': ['0', '1', '2', '3', '4', '5', '6', '7'],
                                                        '_xycollector_popup_squid_select_combobox': ['1', '2', '3', '4', '5', '6'],
                                                        '_xycollector_popup_voltage_factor_combobox': ['e-5', 'e-4', 'e2', 'e3']
                                                       }




