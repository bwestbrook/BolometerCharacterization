from libraries.gen_class import Class

cosmic_rays_settings = Class()

cosmic_rays_settings.cosmic_rays_build_dict = {
                                                             '_common_settings': {'font': 'large'},
# HARDWARE SETUP 
                                                             '_cosmic_rays_popup_hardware_setup_label': {'text': 'Hardware Setup', 'font': 'huge', 'color': 'blue',
                                                                                                         'alignment': 'Center', 'position': (0, 0, 1, 8)},
#
                                                             '_cosmic_rays_popup_daq_channel_1_header_label': {'text': 'DAQ Channel 1:', 'position': (2, 0, 1, 1)},
                                                             '_cosmic_rays_popup_daq_channel_1_combobox': { 'position': (2, 1, 1, 3)},

                                                             '_cosmic_rays_popup_daq_1_integration_time_header_label': {'text': 'Integration Time 1 (ms):', 'position': (3, 0, 1, 1)},
                                                             '_cosmic_rays_popup_daq_1_integration_time_combobox': {'position': (3, 1, 1, 3)},

                                                             '_cosmic_rays_popup_daq_1_sample_rate_header_label': {'text': 'Sample Rate 1 (Hz):', 'position': (4, 0, 1, 1)},
                                                             '_cosmic_rays_popup_daq_1_sample_rate_combobox': {'position': (4, 1, 1, 3)},

                                                             '_cosmic_rays_popup_daq_channel_2_header_label': {'text': 'DAQ Channel 2:', 'position': (2, 4, 1, 1)},
                                                             '_cosmic_rays_popup_daq_channel_2_combobox': { 'position': (2, 5, 1, 3)},

                                                             '_cosmic_rays_popup_daq_2_integration_time_header_label': {'text': 'Integration Time 2 (ms):', 'position': (3, 4, 1, 1)},
                                                             '_cosmic_rays_popup_daq_2_integration_time_combobox': {'position': (3, 5, 1, 3)},

                                                             '_cosmic_rays_popup_daq_2_sample_rate_header_label': {'text': 'Sample Rate 2 (Hz):', 'position': (4, 4, 1, 1)},
                                                             '_cosmic_rays_popup_daq_2_sample_rate_combobox': {'position': (4, 5, 1, 3)},

                                                             '_cosmic_rays_popup_number_of_data_file_header_label': {'text': 'Number of Files:', 'position': (5, 0, 1, 1)},
                                                             '_cosmic_rays_popup_number_of_data_files_lineedit': {'text': '10', 'position': (5, 1, 1, 3)},

                                                             '_cosmic_rays_popup_status_header_label': {'text': 'Status:', 'position': (5, 4, 1, 1)},
                                                             '_cosmic_rays_popup_status_label': {'position': (5, 5, 1, 3)},
# PLOT SETUP 
                                                             '_cosmic_rays_popup_plotting_output_label': {'text': 'Plotting and Output', 'font': 'huge', 'color': 'blue',
                                                                                                          'alignment': 'Center', 'position': (6, 0, 1, 8)},

                                                             '_cosmic_rays_popup_squid_1_header_label': {'text': 'SQUID 1:', 'position': (7, 0, 1, 1), 'font': 'huge', 'color': 'red'},
                                                             '_cosmic_rays_popup_squid_1_select_combobox': {'function': '_update_squid_calibration', 'font': 'huge', 'color': 'red',
                                                                                                           'position': (7, 1, 1, 3)},

                                                             '_cosmic_rays_popup_squid_2_header_label': {'text': 'SQUID 2:', 'position': (7, 4, 1, 1), 'font': 'huge', 'color': 'red'},
                                                             '_cosmic_rays_popup_squid_2_select_combobox': {'function': '_update_squid_calibration', 'font': 'huge', 'color': 'red',
                                                                                                           'position': (7, 5, 1, 3)},

                                                             '_cosmic_rays_popup_sample_1_name_header_label': {'text': 'Sample 1 Name:', 'position': (8, 0, 1, 1)},
                                                             '_cosmic_rays_popup_sample_1_name_lineedit': {'text': '', 'position': (8, 1, 1, 3)},

                                                             '_cosmic_rays_popup_sample_2_name_header_label': {'text': 'Sample 2 Name:', 'position': (8, 4, 1, 1)},
                                                             '_cosmic_rays_popup_sample_2_name_lineedit': {'text': '', 'position': (8, 5, 1, 3)},

                                                             '_cosmic_rays_popup_sample_1_voltage_bias_header_label': {'text': 'Sample 1 Vb (uV):', 'position': (9, 0, 1, 1)},
                                                             '_cosmic_rays_popup_sample_1_voltage_bias_lineedit': {'position': (9, 1, 1, 3)},

                                                             '_cosmic_rays_popup_sample_2_voltage_bias_header_label': {'text': 'Sample 2 Vb (uV):', 'position': (9, 4, 1, 1)},
                                                             '_cosmic_rays_popup_sample_2_voltage_bias_lineedit': {'position': (9, 5, 1, 3)},

                                                             '_cosmic_rays_popup_sample_1_squid_offset_header_label': {'text': 'Sample 2 SQUID Offset (V):', 'position': (10, 0, 1, 1)},
                                                             '_cosmic_rays_popup_sample_1_squid_offset_lineedit': {'position': (10, 1, 1, 3)},

                                                             '_cosmic_rays_popup_sample_2_squid_offset_header_label': {'text': 'Sample 2 SQUID Offset (V):', 'position': (10, 4, 1, 1)},
                                                             '_cosmic_rays_popup_sample_2_squid_offset_lineedit': {'position': (10, 5, 1, 3)},


# CONTROL BUTTONS 
                                                             '_cosmic_rays_popup_control_buttons_label': {'text': 'Controls', 'font': 'huge', 'color': 'blue',
                                                                                                          'alignment': 'Center', 'position': (14, 0, 1, 8)},

                                                             '_cosmic_rays_popup_start_pushbutton': {'text': 'Start', 'function': '_run_cosmic_rays', 'position': (15, 0, 1, 4)},

                                                             '_cosmic_rays_popup_stop_pushbutton': {'text': 'Stop', 'function': '_stop', 'position': (15, 4, 1, 4)},

                                                             '_cosmic_rays_popup_save_pushbutton': {'text': 'Save Plots and Data', 'function': '_save_plots_and_data', 'position': (16, 0, 1, 8)},

                                                             '_cosmic_rays_popup_close_pushbutton': {'text': 'Close', 'function': '_close_cosmic_rays', 'position': (17, 0, 1, 8)},

# VISUAL DATA MONITORING
                                                             '_cosmic_rays_popup_data_1_label': {'alignment': 'Center', 'position': (11, 0, 1, 4)},

                                                             '_cosmic_rays_popup_data_1_mean_header_label': {'text': 'AVG:', 'alignment': 'Right', 'position': (14, 0, 1, 1)},
                                                             '_cosmic_rays_popup_data_1_mean_label': {'alignment': 'Left', 'position': (14, 1, 1, 1)},

                                                             '_cosmic_rays_popup_data_1_std_header_label': {'text': 'STD:', 'alignment': 'Right', 'position': (14, 2, 1, 1)},
                                                             '_cosmic_rays_popup_data_1_std_label': {'alignment': 'Left', 'position': (14, 3, 1, 1)},

                                                             '_cosmic_rays_popup_data_2_label': {'alignment': 'Center', 'position': (11, 4, 1, 4)},

                                                             '_cosmic_rays_popup_data_2_mean_header_label': {'text': 'AVG:', 'alignment': 'Right', 'position': (14, 4, 1, 1)},
                                                             '_cosmic_rays_popup_data_2_mean_label': {'alignment': 'Left', 'position': (14, 5, 1, 1)},

                                                             '_cosmic_rays_popup_data_2_std_header_label': {'text': 'STD:', 'alignment': 'Right', 'position': (14, 6, 1, 1)},
                                                             '_cosmic_rays_popup_data_2_std_label': {'alignment': 'Left', 'position': (14, 7, 1, 1)},


}



cosmic_rays_settings.cosmic_rays_combobox_entry_dict = {
                                                          '_cosmic_rays_popup_daq_channel_1_combobox': ['0', '1', '2', '3'],
                                                          '_cosmic_rays_popup_daq_1_sample_rate_combobox': ['1000', '3000', '6000'],
                                                          '_cosmic_rays_popup_daq_1_integration_time_combobox': ['1000', '10000', '20000', '30000', '600000'],
                                                          '_cosmic_rays_popup_squid_1_select_combobox': ['', '1', '2', '3', '4', '5', '6'],
                                                          '_cosmic_rays_popup_daq_channel_2_combobox': ['0', '1', '2', '3'],
                                                          '_cosmic_rays_popup_daq_2_sample_rate_combobox': ['1000', '3000', '6000'],
                                                          '_cosmic_rays_popup_daq_2_integration_time_combobox': ['1000', '10000', '20000', '30000', '600000'],
                                                          '_cosmic_rays_popup_squid_2_select_combobox': ['', '1', '2', '3', '4', '5', '6'],
                                                          #'_cosmic_rays_popup_daq_channel_3_combobox': ['0', '1', '2', '3'],
                                                          #'_cosmic_rays_popup_grt_range_combobox': ['2', '20', '200', '2K', '20K', '200K', '2M'],
                                                          #'_cosmic_rays_popup_sample_temp_combobox': ['1.2K', '1.0K', '310mK', '260mK'],
                                                          #'_cosmic_rays_popup_sample_drift_direction_combobox': ['Hi2Lo', 'Lo2Hi'],
                                                          #'_cosmic_rays_popup_optical_load_combobox': ['Dark', '77K', '300K']
                                                         }

cosmic_rays_settings.cosmic_rays_run_params = ['squid_1_select_combobox', 'squid_2_select_combobox', 'sample_1_name_lineedit', 'sample_2_name_lineedit',
                                               'daq_1_sample_rate_combobox', 'daq_2_sample_rate_combobox',
                                               'daq_channel_1_combobox', 'daq_channel_2_combobox',
                                               'daq_1_integration_time_combobox', 'daq_2_integration_time_combobox',
                                               'number_of_data_files_lineedit']
