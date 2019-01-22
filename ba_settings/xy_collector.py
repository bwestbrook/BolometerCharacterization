from libraries.gen_class import Class

xy_collector_settings = Class()

xy_collector_settings.xy_collector_build_dict = {
                                                             '_common_settings': {'font': 'large'},
# HARDWARE SETUP 
                                                             '_xy_collector_popup_hardware_setup_label': {'text': 'HARDWARE SETUP', 'font': 'large', 'color': 'blue',
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

                                                             '_xy_collector_popup_grt_range_header_label': {'text': 'GRT Range:', 'position': (4, 2, 1, 1)},
                                                             '_xy_collector_popup_grt_range_combobox': {'position': (4, 3, 1, 1)},

                                                             '_xy_collector_popup_daq_integration_time_header_label': {'text': 'Integration Time (ms):', 'position': (5, 0, 1, 1)},
                                                             '_xy_collector_popup_daq_integration_time_combobox': {'position': (5, 1, 1, 1)},

                                                             '_xy_collector_popup_daq_sample_rate_header_label': {'text': 'Sample Rate (Hz):', 'position': (5, 2, 1, 1)},
                                                             '_xy_collector_popup_daq_sample_rate_combobox': {'position': (5, 3, 1, 1)},
# PLOT SETUP 
                                                             #'_xy_collector_popup_raw_data_path_header_label': {'text': 'Raw Data Path:', 'position': (7, 0, 1, 1)},
                                                             #'_xy_collector_popup_raw_data_path_label': {'text': 'Start Taking Data To Set Raw Data Path', 'position': (7, 1, 1, 3), 'font': 'med'},

                                                             '_xy_collector_popup_plotting_output_label': {'text': 'Plotting/Output', 'font': 'large', 'color': 'blue',
                                                                                                           'alignment': 'Center', 'position': (6, 0, 1, 4)},

                                                             '_xy_collector_popup_sample_name_header_label': {'text': 'Sample Name:', 'position': (7, 0, 1, 1)},
                                                             '_xy_collector_popup_sample_name_lineedit': {'text': '', 'position': (7, 1, 1, 1)},

                                                             '_xy_collector_popup_optical_load_header_label': {'text': 'Optical Load:', 'position': (7, 2, 1, 1)},
                                                             '_xy_collector_popup_optical_load_combobox': {'position': (7, 3, 1, 1)},

                                                             '_xy_collector_popup_sample_drift_direction_label': {'text': 'Stage Drift :', 'position': (8, 0, 1, 1)},
                                                             '_xy_collector_popup_sample_drift_direction_combobox': {'position': (8, 1, 1, 1), 'font': 'med'},

                                                             '_xy_collector_popup_sample_temp_header_label': {'text': 'Sample Temp:', 'position': (8, 2, 1, 1)},
                                                             '_xy_collector_popup_sample_temp_combobox': {'position': (8, 3, 1, 1), 'font': 'med'},

                                                             '_xy_collector_popup_fit_clip_lo_header_label': {'text': 'Fit Clip Low:', 'position': (9, 0, 1, 1)},
                                                             '_xy_collector_popup_fit_clip_lo_lineedit': {'text': '', 'position': (9, 1, 1, 1)},

                                                             '_xy_collector_popup_fit_clip_hi_header_label': {'text': 'Fit Clip Hi:', 'position': (9, 2, 1, 1)},
                                                             '_xy_collector_popup_fit_clip_hi_lineedit': {'text': '', 'position': (9, 3, 1, 1)},

                                                             '_xy_collector_popup_data_clip_lo_header_label': {'text': 'Data Clip Low:', 'position': (10, 0, 1, 1)},
                                                             '_xy_collector_popup_data_clip_lo_lineedit': {'text': '', 'position': (10, 1, 1, 1)},

                                                             '_xy_collector_popup_data_clip_hi_header_label': {'text': 'Data Clip Hi:', 'position': (10, 2, 1, 1)},
                                                             '_xy_collector_popup_data_clip_hi_lineedit': {'text': '', 'position': (10, 3, 1, 1)},

                                                             '_xy_collector_popup_sample_res_header_label': {'text': 'Sample Res RT (Ohms):', 'position': (11, 0, 1, 1)},
                                                             '_xy_collector_popup_sample_res_lineedit': {'text': '', 'position': (11, 1, 1, 1)},

                                                             '_xy_collector_popup_include_errorbars_checkbox': {'text': 'Include Error Bars:', 'position': (11, 2, 1, 1)},

                                                             '_xy_collector_popup_invert_output_checkbox': {'text': 'Invert Output:', 'position': (11, 3, 1, 1)},

# CONTROL BUTTONS 
                                                             '_xy_collector_popup_control_buttons_label': {'text': 'CONTROLS', 'font': 'large', 'color': 'blue',
                                                                                                          'alignment': 'Center', 'position': (13, 0, 1, 4)},

                                                             '_xy_collector_popup_start_pushbutton': {'text': 'Start', 'font': 'huge', 'function': '_run_xy_collector', 'position': (14, 0, 1, 2)},

                                                             '_xy_collector_popup_pause_pushbutton': {'text': 'Stop', 'function': '_stop', 'position': (14, 2, 1, 2)},

                                                             '_xy_collector_popup_save_pushbutton': {'text': 'Make and Save Plots and Data', 'function': '_save_plots_and_data', 'position': (15, 0, 1, 4)},

                                                             '_xy_collector_popup_close_pushbutton': {'text': 'Close', 'function': '_close_xy_collector', 'position': (16, 0, 1, 4)},

# VISUAL DATA MONITORING
                                                             '_xy_collector_popup_data_monitor_label': {'text': 'VISUAL DATA MONITOR', 'font': 'large', 'color': 'blue',
                                                                                                        'alignment': 'Center', 'position': (0, 4, 1, 6)},

                                                             '_xy_collector_popup_xdata_label': {'alignment': 'Center', 'position': (1, 4, 5, 6)},

                                                             '_xy_collector_popup_xdata_mean_header_label': {'text': 'AVG:', 'alignment': 'Right', 'position': (6, 4, 1, 1)},
                                                             '_xy_collector_popup_xdata_mean_label': {'alignment': 'Left', 'position': (6, 5, 1, 1)},

                                                             '_xy_collector_popup_xdata_std_header_label': {'text': 'STD', 'alignment': 'Right', 'position': (6, 6, 1, 1)},
                                                             '_xy_collector_popup_xdata_std_label': {'alignment': 'Left', 'position': (6, 7, 1, 1)},

                                                             '_xy_collector_popup_ydata_label': {'alignment': 'Center', 'position': (7, 4, 5, 6)},

                                                             '_xy_collector_popup_ydata_mean_header_label': {'text': 'AVG:', 'alignment': 'Right', 'position': (12, 4, 1, 1)},
                                                             '_xy_collector_popup_ydata_mean_label': {'alignment': 'Left', 'position': (12, 5, 1, 1)},

                                                             '_xy_collector_popup_ydata_std_header_label': {'text': 'STD', 'alignment': 'Right', 'position': (12, 6, 1, 1)},
                                                             '_xy_collector_popup_ydata_std_label': {'alignment': 'Left', 'position': (12, 7, 1, 1)},

                                                             '_xy_collector_popup_xydata_label': {'alignment': 'Center', 'position': (13, 4, 5, 6)},

}



xy_collector_settings.xy_collector_combobox_entry_dict = {
                                                          '_xy_collector_popup_mode_combobox': ['IV', 'RT', 'Discrete'],
                                                          '_xy_collector_popup_daq_channel_x_combobox': ['0', '1', '2', '3'],
                                                          '_xy_collector_popup_daq_channel_y_combobox': ['0', '1', '2', '3'],
                                                          '_xy_collector_popup_squid_select_combobox': ['', '1', '2', '3', '4', '5', '6'],
                                                          '_xy_collector_popup_voltage_factor_combobox': ['1e-5', '1e-4'],
                                                          '_xy_collector_popup_daq_sample_rate_combobox': ['50', '500', '1000'],
                                                          '_xy_collector_popup_daq_integration_time_combobox': ['50', '100', '500', '1000'],
                                                          '_xy_collector_popup_grt_range_combobox': ['2', '20', '200', '2K', '20K', '200K', '2M'],
                                                          '_xy_collector_popup_sample_temp_combobox': ['1.2K', '1.0K', '900mK', '800mK', '700mK',
                                                                                                       '600mK', '500mK', '400mK', '350mK', '325mK',
                                                                                                       '300mK', '275mK', '260mK', '250mK'],
                                                          '_xy_collector_popup_sample_drift_direction_combobox': ['Hi2Lo', 'Lo2Hi'],
                                                          '_xy_collector_popup_optical_load_combobox': ['Dark', '77K', '300K']
                                                         }

