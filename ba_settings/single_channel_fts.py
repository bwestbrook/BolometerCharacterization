from libraries.gen_class import Class

single_channel_fts_settings = Class()

single_channel_fts_settings.single_channel_fts_build_dict = {
                                                             '_common_settings': {'font': 'large'},
# HARDWARE SETUP 
                                                             '_single_channel_fts_popup_hardware_setup_label': {'text': 'HARDWARE SETUP', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (0, 0, 1, 4)},

                                                             '_single_channel_fts_popup_stepper_motor_resource_name_header_label': {'text': 'Stepper Motor Resource Name:', 'position': (1, 0, 1, 1)},
                                                             '_single_channel_fts_popup_current_com_port_combobox': {'function': '_connect_to_com_port', 'position': (1, 1, 1, 1)},

                                                             '_single_channel_fts_popup_signal_channel_header_label': {'text': 'Signal Channel:', 'position': (1, 2, 1, 1)},
                                                             '_single_channel_fts_popup_signal_channel_combobox': {'position': (1, 3, 1, 1)},

                                                             '_single_channel_fts_popup_successful_connection_header_label': {'text': '', 'function': '_connect_to_com_port', 'position': (1, 4, 1, 2)},
                                                             '_single_channel_fts_popup_grid_motor_header_label': {'text': 'Polar Grid Motor:', 'position': (2, 0, 1, 1)},
                                                             '_single_channel_fts_popup_grid_current_com_port_combobox': {'function': '_connect_to_com_port', 'position': (2, 1, 1, 1)},

                                                             '_single_channel_fts_popup_grid_successful_connection_header_label': {'text': '', 'function': '_connect_to_com_port', 'position': (2, 2, 1, 2)},
# SCAN SETUP 
                                                             '_single_channel_fts_popup_scan_setup_label': {'text': 'SCAN SETUP', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (3, 0, 1, 4)},

                                                             '_single_channel_fts_popup_starting_position_header_label': {'text': 'Starting Position (Blue):', 'position': (4, 0, 1, 1)},
                                                             '_single_channel_fts_popup_starting_position_lineedit': {'text': '-30000', 'function': '_update_single_channel_fts', 'position': (4, 1, 1, 1)},

                                                             '_single_channel_fts_popup_ending_position_header_label': {'text': 'Ending Position (Red):', 'position': (4, 2, 1, 1)},
                                                             '_single_channel_fts_popup_ending_position_lineedit': {'text': '30000', 'function': '_update_single_channel_fts', 'position': (4, 3, 1, 1)},

                                                             '_single_channel_fts_popup_step_size_header_label': {'text': 'Step Size:', 'position': (4, 4, 1, 1)},
                                                             '_single_channel_fts_popup_step_size_lineedit': {'text': '1000', 'function': '_update_single_channel_fts', 'position': (4, 5, 1, 1)},

                                                             '_single_channel_fts_popup_integration_time_header_label': {'text': 'Integration Time (ms):', 'position': (6, 0, 1, 1)},
                                                             '_single_channel_fts_popup_integration_time_lineedit': {'text': '200', 'position': (6, 1, 1, 1)},

                                                             '_single_channel_fts_popup_pause_time_header_label': {'text': 'Pause (ms):', 'position': (6, 2, 1, 1)},
                                                             '_single_channel_fts_popup_pause_time_lineedit': {'text': '10', 'position': (6, 3, 1, 1)},

                                                             '_single_channel_fts_popup_sample_rate_header_label': {'text': 'Sample Rate (Hz):', 'position': (6, 4, 1, 1)},
                                                             '_single_channel_fts_popup_sample_rate_combobox': {'position': (6, 5, 1, 1)},
# DERIVED QUANTITIES 

                                                             '_single_channel_fts_popup_number_of_steps_header_label': {'text': 'Number of Steps:', 'position': (5, 0, 1, 1)},
                                                             '_single_channel_fts_popup_number_of_steps_label': {'text': '0', 'position': (5, 1, 1, 1)},

                                                             '_single_channel_fts_popup_highest_frequency_header_label': {'text': 'Highest Freq (Ghz):', 'position': (5, 2, 1, 1)},
                                                             '_single_channel_fts_popup_highest_frequency_label': {'text': '0', 'position': (5, 3, 1, 1)},

                                                             '_single_channel_fts_popup_resolution_header_label': {'text': 'Resolution (Ghz):', 'position': (5, 4, 1, 1)},
                                                             '_single_channel_fts_popup_resolution_label': {'text': '0', 'position': (5, 5, 1, 1)},


# ANALYSIS SETUP 

                                                             '_single_channel_fts_popup_analysis_setup_label': {'text': 'ANALYSIS SETUP', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (8, 0, 1, 4)},

                                                             '_single_channel_fts_popup_DistPerStep_header_label': {'text': 'DistPerStep(in):', 'position': (9, 0, 1, 1)},
                                                             '_single_channel_fts_popup_DistPerStep_lineedit': {'text': '9.858e-6', 'position': (9, 1, 1, 1)},

                                                             '_single_channel_fts_popup_DistPerStep_bill_header_label': {'text': 'Bills: 9.585e-6    Paul: 1.64e-7', 'position': (9, 2, 1, 1)},

                                                             '_single_channel_fts_popup_apodization_type_header_label': {'text': 'Apodization:', 'position': (10, 0, 1, 1)},
                                                             '_single_channel_fts_popup_apodization_type_combobox': {'function':'_apodize','position': (10, 1, 1, 1)},

                                                             '_single_channel_fts_popup_0-path_position_header_label': {'text': '0-Path Position(in):', 'position': (10, 2, 1, 1)},
                                                             '_single_channel_fts_popup_0-path_position_lineedit': {'text': '1.345', 'position': (10, 3, 1, 1)},

                                                             '_single_channel_fts_popup_phone_email_header_label': {'text': 'Phone # or e-mail address:', 'position': (11, 0, 1, 1)},
                                                             '_single_channel_fts_popup_phone_email_lineedit': {'text': '', 'position': (11, 1, 1, 3)},

                                                             '_single_channel_fts_popup_carrier_header_label': {'text': 'Select Carrier:', 'position': (12, 0, 1, 1)},
                                                             '_single_channel_fts_popup_carrier_type_combobox': {'position': (12, 1, 1, 3)},


# CONTROL BUTTONS 
                                                             '_single_channel_fts_popup_control_buttons_label': {'text': 'CONTROLS', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (16, 0, 1, 4)},

                                                             '_single_channel_fts_popup_start_pushbutton': {'text': 'Start', 'function': '_run_fts', 'position': (17, 0, 1, 1)},

                                                             '_single_channel_fts_popup_pause_pushbutton': {'text': 'Pause', 'function': '_dummy', 'position': (17, 1, 1, 1)},

                                                             '_single_channel_fts_popup_done_pushbutton': {'text': 'Done', 'function': '_dummy', 'position': (17, 2, 1, 1)},

                                                             '_single_channel_fts_popup_close_pushbutton': {'text': 'Close', 'function': '_close_single_channel_fts', 'position': (17, 3, 1, 1)},

                                                             '_single_channel_fts_popup_save_pushbutton': {'text': 'Save', 'function': '_final_plot', 'position': (18, 5, 1, 1)},

# VISUAL DATA MONITORING
                                                             '_single_channel_fts_popup_data_monitor_label': {'text': 'VISUAL DATA MONITOR', 'font': 'huge', 'color': 'blue',
                                                                                                              'alignment': 'Center', 'position': (0, 7, 1, 4)},

                                                             '_single_channel_fts_popup_position_monitor_slider': {'function': None, 'position': (1, 7, 1, 5), 'orientation': 'Horizontal'},

                                                             '_single_channel_fts_popup_mean_header_label': {'text': 'Time Average:', 'position': (3, 7, 1, 1)},
                                                             '_single_channel_fts_popup_mean_label': {'text': '0', 'position': (3, 8, 1, 1)},

                                                             '_single_channel_fts_popup_std_header_label': {'text': 'Standard Dev:', 'position': (3, 9, 1, 1)},
                                                             '_single_channel_fts_popup_std_label': {'text': '0', 'position': (3, 10, 1, 1)},

                                                             '_single_channel_fts_popup_current_position_header_label': {'text': 'Current Position (White):', 'position': (4, 9, 1, 1)},
                                                             '_single_channel_fts_popup_current_position_label': {'text': '0', 'position': (4, 10, 1, 1)},

                                                             '_single_channel_fts_popup_position_slider_min_label': {'text': '-5000', 'position': (2, 7, 1, 1)},
                                                             '_single_channel_fts_popup_position_slider_max_label': {'text': '10000', 'position': (2, 11, 1, 1)},

                                                            
                                                             '_single_channel_fts_popup_time_stream_label': {'alignment': 'Center', 'width': 700, 'position': (5, 7, 5, 4)},

                                                             '_single_channel_fts_popup_interferogram_label': {'alignment': 'Center', 'position': (10, 7, 6, 4)},

                                                             '_single_channel_fts_popup_fft_label': {'alignment': 'Center', 'width': 700, 'position': (16, 7, 7, 4)},
}

single_channel_fts_settings.single_channel_fts_monitor_build_dict = {
                                                                     '_common_settings': {'font': 'large'},

                                                                     }

single_channel_fts_settings.fts_com_ports = ['COM1', 'COM2', 'COM3', 'COM4']

single_channel_fts_settings.apodization_types = ['BOXCAR', 'TRIANGULAR']

single_channel_fts_settings.carrier_types = ['phone', 'e-mail']

single_channel_fts_settings.combobox_entry_dict = {
                                                   '_single_channel_fts_popup_signal_channel_combobox': ['0', '1', '2', '3', '4', '5', '6', '7'],
                                                   '_single_channel_fts_popup_carrier_type_combobox': ['phone', 'e-mail'],
                                                   '_single_channel_fts_popup_apodization_type_combobox': ['BOXCAR', 'TRIAGNULAR'],
                                                   '_single_channel_fts_popup_current_com_port_combobox': ['COM1', 'COM2', 'COM3', 'COM4'],
                                                   '_single_channel_fts_popup_grid_current_com_port_combobox': ['COM1', 'COM2', 'COM3', 'COM4'],
                                                   '_single_channel_fts_popup_sample_rate_combobox': ['50', '100', '250', '500', '1000'],
                                                   }


single_channel_fts_settings.fts_int_run_settings = ['starting_position', 'ending_position', 'step_size', 'integration_time', 'pause_time', 'sample_rate']
single_channel_fts_settings.fts_float_run_settings = ['DistPerStep']
single_channel_fts_settings.fts_pulldown_run_settings = ['stepper_motor', 'signal_channel', 'sample_rate','apodization_type']


