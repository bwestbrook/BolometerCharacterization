from libraries.gen_class import Class

xy_collector_settings = Class()

xy_collector_settings.xy_collector_build_dict = {
                                                             '_common_settings': {'font': 'large'},
# HARDWARE SETUP 
                                                             '_xy_collector_popup_hardware_setup_label': {'text': 'HARDWARE SETUP', 'font': 'huge', 'color': 'blue',
                                                                                                         'alignment': 'Center', 'position': (0, 0, 1, 4)},

                                                             '_xy_collector_popup_mode_header_label': {'text': 'XY Mode:', 'position': (1, 0, 1, 1)},
                                                             '_xy_collector_popup_mode_combobox': {'function': '_update_in_xy_mode', 'position': (1, 1, 1, 1)},

                                                             '_xy_collector_popup_daq_channel_x_header_label': {'text': 'DAQ Channel X:', 'position': (2, 0, 1, 1)},
                                                             '_xy_collector_popup_daq_channel_x_combobox': { 'position': (2, 1, 1, 1)},

                                                             '_xy_collector_popup_daq_channel_y_header_label': {'text': 'DAQ Channel Y:', 'position': (2, 2, 1, 1)},
                                                             '_xy_collector_popup_daq_channel_y_combobox': { 'position': (2, 3, 1, 1)},

                                                             '_xy_collector_popup_squid_header_label': {'text': 'SQUID:', 'position': (3, 0, 1, 1), 'font': 'huge', 'color': 'red'},
                                                             '_xy_collector_popup_squid_select_combobox': {'function': '_update_squid_calibration', 'font': 'huge', 'color': 'red',
                                                                                                           'position': (3, 1, 1, 1)},

                                                             '_xy_collector_popup_squid_conversion_header_label': {'text': 'SQUID Calibration:', 'position': (3, 2, 1, 1)},
                                                             '_xy_collector_popup_squid_conversion_label': {'position': (3, 3, 1, 1)},

                                                             '_xy_collector_popup_voltage_factor_header_label': {'text': 'Voltage Factor:', 'position': (4, 0, 1, 1)},
                                                             '_xy_collector_popup_voltage_factor_combobox': {'position': (4, 1, 1, 1)},

                                                             '_xy_collector_popup_daq_integration_time_header_label': {'text': 'Integration Time (ms) [min 40ms]:', 'position': (5, 0, 1, 1)},
                                                             '_xy_collector_popup_daq_integration_time_combobox': {'position': (5, 1, 1, 1)},

                                                             '_xy_collector_popup_daq_sample_rate_header_label': {'text': 'Sample Rate (Hz):', 'position': (5, 2, 1, 1)},
                                                             '_xy_collector_popup_daq_sample_rate_combobox': {'position': (5, 3, 1, 1)},
# PLOT SETUP 
                                                             '_xy_collector_popup_sample_name_header_label': {'text': 'Sample Label:', 'position': (6, 0, 1, 1)},
                                                             '_xy_collector_popup_sample_name_lineedit': {'text': '', 'position': (6, 1, 1, 1)},

                                                             '_xy_collector_popup_sample_temp_header_label': {'text': 'Sample Temp:', 'position': (6, 2, 1, 1)},
                                                             '_xy_collector_popup_sample_temp_lineedit': {'text': '', 'position': (6, 3, 1, 1), 'font': 'med'},

                                                             '_xy_collector_popup_raw_data_path_header_label': {'text': 'Raw Data Path:', 'position': (7, 0, 1, 1)},
                                                             '_xy_collector_popup_raw_data_path_label': {'text': 'Start Taking Data To Set Raw Data Path', 'position': (7, 1, 1, 3), 'font': 'med'},

                                                             '_xy_collector_popup_fit_clip_lo_header_label': {'text': 'Fit Clip Low:', 'position': (8, 0, 1, 1)},
                                                             '_xy_collector_popup_fit_clip_lo_lineedit': {'text': '', 'position': (8, 1, 1, 1)},

                                                             '_xy_collector_popup_fit_clip_hi_header_label': {'text': 'Fit Clip Hi:', 'position': (8, 2, 1, 1)},
                                                             '_xy_collector_popup_fit_clip_hi_lineedit': {'text': '', 'position': (8, 3, 1, 1)},

                                                             '_xy_collector_popup_data_clip_lo_header_label': {'text': 'Data Clip Low:', 'position': (9, 0, 1, 1)},
                                                             '_xy_collector_popup_data_clip_lo_lineedit': {'text': '', 'position': (9, 1, 1, 1)},

                                                             '_xy_collector_popup_data_clip_hi_header_label': {'text': 'Data Clip Hi:', 'position': (9, 2, 1, 1)},
                                                             '_xy_collector_popup_data_clip_hi_lineedit': {'text': '', 'position': (9, 3, 1, 1)},

                                                             '_xy_collector_popup_include_errorbars_checkbox': {'text': 'Include Error Bars:', 'position': (10, 0, 1, 1)},

                                                             '_xy_collector_popup_invert_output_checkbox': {'text': 'Invert Output:', 'position': (10, 1, 1, 1)},

                                                             '_xy_collector_popup_sample_res_header_label': {'text': 'Sample Res RT (Ohms):', 'position': (11, 0, 1, 1)},
                                                             '_xy_collector_popup_sample_res_lineedit': {'text': '', 'position': (11, 1, 1, 1)},
# CONTROL BUTTONS 
                                                             '_xy_collector_popup_control_buttons_label': {'text': 'CONTROLS', 'font': 'huge', 'color': 'blue',
                                                                                                          'alignment': 'Center', 'position': (12, 0, 1, 4)},
                                                             '_xy_collector_popup_start_pushbutton': {'text': 'Start', 'font': 'huge', 'function': '_run_xy_collector', 'position': (13, 0, 1, 2)},

                                                             '_xy_collector_popup_pause_pushbutton': {'text': 'Stop', 'function': '_stop', 'position': (13, 2, 1, 2)},

                                                             '_xy_collector_popup_save_pushbutton': {'text': 'Make and Save Plots and Data', 'function': '_save_plots_and_data', 'position': (14, 0, 1, 4)},

                                                             '_xy_collector_popup_close_pushbutton': {'text': 'Close', 'function': '_close_xy_collector', 'position': (15, 0, 1, 4)},

# VISUAL DATA MONITORING
                                                             '_xy_collector_popup_data_monitor_label': {'text': 'VISUAL DATA MONITOR', 'font': 'huge', 'color': 'blue',
                                                                                                              'alignment': 'Center', 'position': (0, 4, 1, 6)},

                                                             '_xy_collector_popup_xdata_label': {'alignment': 'Center', 'position': (1, 4, 3, 6)},

                                                             '_xy_collector_popup_xdata_mean_header_label': {'text': 'AVG:', 'alignment': 'Right', 'position': (4, 4, 1, 1)},
                                                             '_xy_collector_popup_xdata_mean_label': {'alignment': 'Left', 'position': (4, 5, 1, 1)},

                                                             '_xy_collector_popup_xdata_std_header_label': {'text': 'STD', 'alignment': 'Right', 'position': (4, 6, 1, 1)},
                                                             '_xy_collector_popup_xdata_std_label': {'alignment': 'Left', 'position': (4, 7, 1, 1)},

                                                             '_xy_collector_popup_ydata_label': {'alignment': 'Center', 'position': (5, 4, 3, 6)},

                                                             '_xy_collector_popup_ydata_mean_header_label': {'text': 'AVG:', 'alignment': 'Right', 'position': (8, 4, 1, 1)},
                                                             '_xy_collector_popup_ydata_mean_label': {'alignment': 'Left', 'position': (8, 5, 1, 1)},

                                                             '_xy_collector_popup_ydata_std_header_label': {'text': 'STD', 'alignment': 'Right', 'position': (8, 6, 1, 1)},
                                                             '_xy_collector_popup_ydata_std_label': {'alignment': 'Left', 'position': (8, 7, 1, 1)},

                                                             '_xy_collector_popup_xydata_label': {'alignment': 'Center', 'position': (10, 4, 3, 6)},

}



xy_collector_settings.xy_collector_combobox_entry_dict = {
                                                        '_xy_collector_popup_mode_combobox': ['IV', 'RT', 'Discrete'],
                                                        '_xy_collector_popup_daq_channel_x_combobox': ['0', '1', '2', '3', '4', '5', '6', '7'],
                                                        '_xy_collector_popup_daq_channel_y_combobox': ['0', '1', '2', '3', '4', '5', '6', '7'],
                                                        '_xy_collector_popup_squid_select_combobox': ['1', '2', '3', '4', '5', '6'],
                                                        '_xy_collector_popup_voltage_factor_combobox': ['1e-5', '1e-4', '1e2', '1e3'],
                                                        '_xy_collector_popup_daq_sample_rate_combobox': ['50', '500', '1000'],
                                                        '_xy_collector_popup_daq_integration_time_combobox': ['50', '100', '500', '1000']
                                                       }




