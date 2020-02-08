from libraries.gen_class import Class

single_channel_fts_settings = Class()

single_channel_fts_settings.single_channel_fts_build_dict = {
                                                             '_common_settings': {'font': 'large'},
# HARDWARE SETUP 
                                                             '_single_channel_fts_popup_hardware_setup_label': {'text': 'HARDWARE SETUP', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (0, 0, 1, 6)},

                                                             '_single_channel_fts_popup_fts_sm_com_port_header_label': {'text': 'Stepper Motor Resource Name:', 'position': (1, 0, 1, 1)},
                                                             '_single_channel_fts_popup_fts_sm_com_port_combobox': {'function': '_connect_to_com_port', 'position': (1, 1, 1, 1)},
                                                             '_single_channel_fts_popup_fts_sm_connection_status_label': {'text': 'Not Ready', 'color': 'red', 'font': 'huge', 'position': (1, 2, 1, 1)},

                                                             '_single_channel_fts_popup_grid_sm_motor_header_label': {'text': 'Polar Grid Motor:', 'position': (2, 0, 1, 1)},
                                                             '_single_channel_fts_popup_grid_sm_com_port_combobox': {'function': '_connect_to_com_port', 'position': (2, 1, 1, 1)},
                                                             '_single_channel_fts_popup_grid_sm_connection_status_label': {'text': 'Not Ready', 'color': 'red', 'font': 'huge', 'position': (2, 2, 1, 1)},
                                                             '_single_channel_fts_popup_set_grid_angle_pushbutton': {'text': 'Set Pol Grid Angle To:', 'function': '_rotate_grid', 'position': (2, 3, 1, 1)},
                                                             '_single_channel_fts_popup_grid_angle_lineedit': {'text': '',  'position': (2, 4, 1, 1)},

# SCAN SETUP 
                                                             '_single_channel_fts_popup_scan_setup_label': {'text': 'SCAN SETUP', 'font': 'huge', 'color': 'blue',
                                                                                                            'alignment': 'Center', 'position': (4, 0, 1, 6)},

                                                             '_single_channel_fts_popup_starting_position_header_label': {'text': 'Starting Position:', 'position': (5, 0, 1, 1)},
                                                             '_single_channel_fts_popup_starting_position_lineedit': {'text': '-10000', 'function': '_update_single_channel_fts', 'position': (5, 1, 1, 1)},

                                                             '_single_channel_fts_popup_ending_position_header_label': {'text': 'Ending Position:', 'position': (5, 2, 1, 1)},
                                                             '_single_channel_fts_popup_ending_position_lineedit': {'text': '30000', 'function': '_update_single_channel_fts', 'position': (5, 3, 1, 1)},

                                                             '_single_channel_fts_popup_step_size_header_label': {'text': 'Step Size:', 'position': (5, 4, 1, 1)},
                                                             '_single_channel_fts_popup_step_size_lineedit': {'text': '1000', 'function': '_update_single_channel_fts', 'position': (5, 5, 1, 1)},

                                                             '_single_channel_fts_popup_signal_channel_header_label': {'text': 'Signal Channel:', 'position': (7, 0, 1, 1)},
                                                             '_single_channel_fts_popup_signal_channel_combobox': {'position': (7, 1, 1, 1)},

                                                             '_single_channel_fts_popup_integration_time_header_label': {'text': 'Integration Time (ms):', 'position': (8, 0, 1, 1)},
                                                             '_single_channel_fts_popup_integration_time_combobox': {'position': (8, 1, 1, 1)},

                                                             '_single_channel_fts_popup_pause_time_header_label': {'text': 'Pause (ms):', 'position': (8, 2, 1, 1)},
                                                             '_single_channel_fts_popup_pause_time_combobox': {'position': (8, 3, 1, 1)},

                                                             '_single_channel_fts_popup_sample_rate_header_label': {'text': 'Sample Rate (Hz):', 'position': (8, 4, 1, 1)},
                                                             '_single_channel_fts_popup_sample_rate_combobox': {'position': (8, 5, 1, 1)},

                                                             '_single_channel_fts_popup_open_lock_in_pushbutton': {'text': 'Open Lock-in', 'function': '_sr830_dsp', 'position': (9, 0, 1, 1)},
# DERIVED QUANTITIES 

                                                             '_single_channel_fts_popup_number_of_steps_header_label': {'text': 'Number of Steps:', 'position': (6, 0, 1, 1)},
                                                             '_single_channel_fts_popup_number_of_steps_label': {'text': '0', 'position': (6, 1, 1, 1)},

                                                             '_single_channel_fts_popup_max_frequency_header_label': {'text': 'Max Freq (Ghz):', 'position': (6, 2, 1, 1)},
                                                             '_single_channel_fts_popup_max_frequency_label': {'text': '0', 'position': (6, 3, 1, 1)},

                                                             '_single_channel_fts_popup_resolution_header_label': {'text': 'Resolution (Ghz):', 'position': (6, 4, 1, 1)},
                                                             '_single_channel_fts_popup_resolution_label': {'text': '0', 'position': (6, 5, 1, 1)},

# ANALYSIS SETUP 
                                                             '_single_channel_fts_popup_analysis_setup_label': {'text': 'ANALYSIS SETUP', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (10, 0, 1, 6)},

                                                             '_single_channel_fts_popup_distance_per_step_header_label': {'text': 'Dist/Step (nm):', 'position': (11, 0, 1, 1)},
                                                             '_single_channel_fts_popup_distance_per_step_combobox': {'function': '_update_single_channel_fts', 'position': (11, 1, 1, 1)},

                                                             '_single_channel_fts_popup_apodization_type_header_label': {'text': 'Apodization:', 'position': (11, 2, 1, 1)},
                                                             '_single_channel_fts_popup_apodization_type_combobox': {'position': (11, 3, 1, 1)},

                                                             '_single_channel_fts_popup_phone_email_header_label': {'text': 'E-mail address:', 'position': (11, 4, 1, 1)},
                                                             '_single_channel_fts_popup_phone_email_lineedit': {'text': '', 'position': (11, 5, 1, 1)},

                                                             '_single_channel_fts_popup_squid_select_header_label': {'text': 'SQUID:', 'position': (12, 0, 1, 1)},
                                                             '_single_channel_fts_popup_squid_select_combobox': {'function': '_update_squid_calibration', 'position': (12, 1, 1, 1)},

                                                             '_single_channel_fts_popup_sample_name_header_label': {'text': 'Sample Name:', 'position': (12, 2, 1, 1)},
                                                             '_single_channel_fts_popup_sample_name_lineedit': {'position': (12, 3, 1, 1)},

                                                             '_single_channel_fts_popup_beam_splitter_header_label': {'text': 'Beam Splitter (mil):', 'position': (12, 4, 1, 1)},
                                                             '_single_channel_fts_popup_beam_splitter_combobox': {'position': (12, 5, 1, 1)},

                                                             '_single_channel_fts_popup_voltage_bias_header_label': {'text': 'Voltage bias (uV):', 'position': (13, 0, 1, 1)},
                                                             '_single_channel_fts_popup_voltage_bias_lineedit': {'position': (13, 1, 1, 1)},
#
                                                             '_single_channel_fts_popup_heater_voltage_header_label': {'text': 'Heater Voltage:', 'position': (13, 2, 1, 1)},
                                                             '_single_channel_fts_popup_heater_voltage_lineedit': {'position': (13, 3, 1, 1)},

                                                             '_single_channel_fts_popup_verify_parameters_checkbox': {'text': 'Verify Before Start?', 'position': (13, 4, 1, 1)},

                                                             '_single_channel_fts_popup_frequency_band_header_label': {'text': 'Frequency Band (GHz):', 'position': (14, 0, 1, 1)},
                                                             '_single_channel_fts_popup_frequency_band_combobox': {'position': (14, 1, 1, 1)},

                                                             '_single_channel_fts_popup_fft_every_n_points_header_label': {'text': 'FFT Every N Points:', 'position': (14, 2, 1, 1)},
                                                             '_single_channel_fts_popup_fft_every_n_points_combobox': {'position': (14, 3, 1, 1)},
#
# CONTROL BUTTONS 
                                                             '_single_channel_fts_popup_control_buttons_label': {'text': 'CONTROLS', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (16, 0, 1, 6)},

                                                             '_single_channel_fts_popup_update_meta_data_pushbutton': {'text': 'Update Meta Data', 'function': '_update_meta_data',
                                                                                                                       'position': (17, 0, 1, 6)},
                                                             '_single_channel_fts_popup_start_pushbutton': {'text': 'Start', 'function': '_run_fts', 'position': (18, 0, 1, 3)},
                                                             '_single_channel_fts_popup_abort_pushbutton': {'text': 'Abort', 'function': '_stop_fts', 'position': (18, 3, 1, 3)},
                                                             '_single_channel_fts_popup_close_pushbutton': {'text': 'Close', 'function': '_close_single_channel_fts', 'position': (19, 0, 1, 3)},
                                                             '_single_channel_fts_popup_save_pushbutton': {'text': 'Save', 'function': '_save_plots_and_data', 'position': (19, 3, 1, 3)},

# VISUAL DATA MONITORING
                                                             '_single_channel_fts_popup_data_monitor_label': {'text': 'VISUAL DATA MONITOR', 'font': 'huge', 'color': 'blue',
                                                                                                              'alignment': 'Center', 'position': (0, 7, 1, 4)},

                                                             '_single_channel_fts_popup_position_monitor_slider': {'position': (1, 7, 1, 4), 'orientation': 'Horizontal'},

                                                             '_single_channel_fts_popup_position_slider_min_label': {'position': (2, 7, 1, 1)},
                                                             '_single_channel_fts_popup_position_slider_max_label': {'alignment': 'Right', 'position': (2, 10, 1, 1)},

                                                             '_single_channel_fts_popup_current_position_header_label': {'text': 'Current Mirror Position:', 'position': (3, 7, 1, 1)},
                                                             '_single_channel_fts_popup_current_position_label': {'text': '0', 'position': (3, 8, 1, 2)},
                                                             '_single_channel_fts_popup_duration_label': {'font': 'small', 'position': (4, 7, 1, 4)},

                                                             '_single_channel_fts_popup_time_stream_label': {'alignment': 'Center', 'position': (5, 7, 4, 4)},

                                                             '_single_channel_fts_popup_mean_header_label': {'text': 'Time Average:', 'position': (9, 7, 1, 1)},
                                                             '_single_channel_fts_popup_mean_label': {'text': '0', 'position': (9, 8, 1, 1)},

                                                             '_single_channel_fts_popup_std_header_label': {'text': 'Standard Dev:', 'position': (9, 9, 1, 1)},
                                                             '_single_channel_fts_popup_std_label': {'text': '0', 'position': (9, 10, 1, 1)},

                                                             '_single_channel_fts_popup_interferogram_label': {'alignment': 'Center', 'position': (10, 7, 8, 4)},

                                                             '_single_channel_fts_popup_if_mean_header_label': {'text': 'IF Mean:', 'position': (18, 7, 1, 1)},
                                                             '_single_channel_fts_popup_if_mean_label': {'text': '0', 'position': (18, 8, 1, 1)},

                                                             '_single_channel_fts_popup_if_max_min_header_label': {'text': 'If Max - Min:', 'position': (18, 9, 1, 1)},
                                                             '_single_channel_fts_popup_if_max_min_label': {'text': '0', 'position': (18, 10, 1, 1)},

                                                             #'_single_channel_fts_popup_fft_label': {'alignment': 'Center', 'position': (15, 7, 6, 4)},
}

single_channel_fts_settings.single_channel_fts_monitor_build_dict = {
                                                                     '_common_settings': {'font': 'large'},

                                                                     }

single_channel_fts_settings.fts_com_ports = ['COM1', 'COM2', 'COM3', 'COM4']

single_channel_fts_settings.apodization_types = ['BOXCAR', 'TRIANGULAR']

single_channel_fts_settings.carrier_types = ['phone', 'e-mail']

single_channel_fts_settings.fts_combobox_entry_dict = {
                                                       '_single_channel_fts_popup_signal_channel_combobox': ['', '0', '1', '2', '3'],
                                                       '_single_channel_fts_popup_squid_select_combobox': ['', '1', '2', '3', '4', '5', '6'],
                                                       '_single_channel_fts_popup_apodization_type_combobox': ['TRIANGULAR', 'BOXCAR'],
                                                       '_single_channel_fts_popup_distance_per_step_combobox': ["250.39", "4.168"],
                                                       '_single_channel_fts_popup_beam_splitter_combobox': ['5','10'],
                                                       '_single_channel_fts_popup_pause_time_combobox': ['250', '300', '400', '450', '500', '600', '750','1000', '1500', '2000', '3000', '5000', '10000'],
                                                       '_single_channel_fts_popup_integration_time_combobox': ['250', '300', '500', '1000', '1500', '3000'],
                                                       '_single_channel_fts_popup_fft_every_n_points_combobox': ['1', '5', '10', '25', '50', '100'],
                                                       '_single_channel_fts_popup_sample_rate_combobox': ['1000', '2000', '5000'],
                                                       '_single_channel_fts_popup_fts_sm_com_port_combobox': ['COM12'],
                                                       '_single_channel_fts_popup_grid_sm_com_port_combobox': [''],
                                                       '_single_channel_fts_popup_frequency_band_combobox': ['', 'MF-Sinuous1p5', 'MF-Sinuous0p8', '30', '40', '90', '150', '220', '270'],
                                                       #'_single_channel_fts_popup_current_com_port_combobox': ['COM1', 'COM2', 'COM3', 'COM4','COM5','COM6'],
                                                       #'_single_channel_fts_popup_grid_current_com_port_combobox': ['COM1', 'COM2', 'COM3', 'COM4'],
                                                       }

single_channel_fts_settings.fts_scan_params = ['starting_position_lineedit', 'ending_position_lineedit', 'sample_name_lineedit', 'step_size_lineedit',  'grid_angle_lineedit', #ints
                                               'voltage_bias_lineedit', 'heater_voltage_lineedit',
                                               'resolution_label', 'max_frequency_label',
                                               'distance_per_step_combobox', 'squid_select_combobox', 'integration_time_combobox', 'pause_time_combobox',
                                               'fts_sm_com_port_combobox', 'grid_sm_com_port_combobox', 'signal_channel_combobox', 'sample_rate_combobox',
                                               'apodization_type_combobox', 'beam_splitter_combobox', 'frequency_band_combobox'] #combobox

