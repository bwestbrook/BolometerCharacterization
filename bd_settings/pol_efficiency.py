from GuiBuilder.gui_builder import GenericClass

pol_efficiency_settings = GenericClass()

pol_efficiency_settings.pol_efficiency_build_dict = {
                                                     '_common_settings': {'font': 'large'},
# HARDWARE SETUP 
                                                     '_pol_efficiency_popup_hardware_setup_label': {'text': 'HARDWARE SETUP', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (0, 0, 1, 6)},

                                                     '_pol_efficiency_popup_sm_com_port_header_label': {'text': 'Stepper Motor Resource Name:', 'position': (1, 0, 1, 1)},
                                                     '_pol_efficiency_popup_sm_com_port_combobox': {'function': '_connect_to_com_port', 'position': (1, 1, 1, 1)},
                                                     '_pol_efficiency_popup_sm_connection_status_label': {'text': 'Not Ready', 'color': 'red', 'font': 'huge', 'position': (1, 2, 1, 1)},


# SCAN SETUP 
                                                     '_pol_efficiency_popup_scan_setup_label': {'text': 'SCAN SETUP', 'font': 'huge', 'color': 'blue',
                                                                                                    'alignment': 'Center', 'position': (4, 0, 1, 6)},

                                                     '_pol_efficiency_popup_starting_position_header_label': {'text': 'Starting Position:', 'position': (5, 0, 1, 1)},
                                                     '_pol_efficiency_popup_starting_position_lineedit': {'text': '-10000', 'function': '_update_pol_efficiency', 'position': (5, 1, 1, 1)},

                                                     '_pol_efficiency_popup_ending_position_header_label': {'text': 'Ending Position:', 'position': (5, 2, 1, 1)},
                                                     '_pol_efficiency_popup_ending_position_lineedit': {'text': '30000', 'function': '_update_pol_efficiency', 'position': (5, 3, 1, 1)},

                                                     '_pol_efficiency_popup_step_size_header_label': {'text': 'Step Size:', 'position': (5, 4, 1, 1)},
                                                     '_pol_efficiency_popup_step_size_lineedit': {'text': '1000', 'function': '_update_pol_efficiency', 'position': (5, 5, 1, 1)},

                                                     '_pol_efficiency_popup_signal_channel_header_label': {'text': 'Signal Channel:', 'position': (7, 0, 1, 1)},
                                                     '_pol_efficiency_popup_signal_channel_combobox': {'position': (7, 1, 1, 1)},

                                                     '_pol_efficiency_popup_integration_time_header_label': {'text': 'Integration Time (ms):', 'position': (8, 0, 1, 1)},
                                                     '_pol_efficiency_popup_integration_time_combobox': {'position': (8, 1, 1, 1)},

                                                     '_pol_efficiency_popup_pause_time_header_label': {'text': 'Pause (ms):', 'position': (8, 2, 1, 1)},
                                                     '_pol_efficiency_popup_pause_time_combobox': {'position': (8, 3, 1, 1)},

                                                     '_pol_efficiency_popup_sample_rate_header_label': {'text': 'Sample Rate (Hz):', 'position': (8, 4, 1, 1)},
                                                     '_pol_efficiency_popup_sample_rate_combobox': {'position': (8, 5, 1, 1)},

                                                     '_pol_efficiency_popup_open_lock_in_pushbutton': {'text': 'Open Lock-in', 'function': '_sr830_dsp', 'position': (9, 0, 1, 1)},
# DERIVED QUANTITIES 

                                                     '_pol_efficiency_popup_number_of_steps_header_label': {'text': 'Number of Steps:', 'position': (6, 0, 1, 1)},
                                                     '_pol_efficiency_popup_number_of_steps_label': {'text': '0', 'position': (6, 1, 1, 1)},


# ANALYSIS SETUP 
                                                     '_pol_efficiency_popup_analysis_setup_label': {'text': 'ANALYSIS SETUP', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (10, 0, 1, 6)},

                                                     '_pol_efficiency_popup_distance_per_step_header_label': {'text': 'Steps/Degree (nm):', 'position': (11, 0, 1, 1)},
                                                     '_pol_efficiency_popup_distance_per_step_lineedit': {'text': '', 'position': (11, 1, 1, 1)},

                                                     '_pol_efficiency_popup_squid_select_header_label': {'text': 'SQUID:', 'position': (12, 0, 1, 1)},
                                                     '_pol_efficiency_popup_squid_select_combobox': {'function': '_update_squid_calibration', 'position': (12, 1, 1, 1)},

                                                     '_pol_efficiency_popup_sample_name_header_label': {'text': 'Sample Name:', 'position': (12, 2, 1, 1)},
                                                     '_pol_efficiency_popup_sample_name_lineedit': {'position': (12, 3, 1, 1)},

                                                     '_pol_efficiency_popup_voltage_bias_header_label': {'text': 'Voltage bias (uV):', 'position': (13, 0, 1, 1)},
                                                     '_pol_efficiency_popup_voltage_bias_lineedit': {'position': (13, 1, 1, 1)},
#
                                                     '_pol_efficiency_popup_heater_voltage_header_label': {'text': 'Thermal Source (T):', 'position': (13, 2, 1, 1)},
                                                     '_pol_efficiency_popup_heater_voltage_lineedit': {'text': '77K', 'position': (13, 3, 1, 1)},

                                                     '_pol_efficiency_popup_verify_parameters_checkbox': {'text': 'Verify Before Start?', 'position': (13, 4, 1, 1)},
#
# CONTROL BUTTONS 
                                                     '_pol_efficiency_popup_control_buttons_label': {'text': 'CONTROLS', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (16, 0, 1, 6)},

                                                     '_pol_efficiency_popup_start_pushbutton': {'text': 'Start', 'function': '_run_pol_efficiency', 'position': (17, 0, 1, 3)},
                                                     '_pol_efficiency_popup_stop_pushbutton': {'text': 'Stop', 'function': '_stop', 'position': (17, 3, 1, 3)},
                                                     '_pol_efficiency_popup_close_pushbutton': {'text': 'Close', 'function': '_close_pol_efficiency', 'position': (18, 0, 1, 3)},
                                                     '_pol_efficiency_popup_save_pushbutton': {'text': 'Save', 'function': '_save_plots_and_data', 'position': (18, 3, 1, 3)},

# VISUAL DATA MONITORING
                                                     '_pol_efficiency_popup_data_monitor_label': {'text': 'VISUAL DATA MONITOR', 'font': 'huge', 'color': 'blue',
                                                                                                  'alignment': 'Center', 'position': (0, 7, 1, 4)},

                                                     '_pol_efficiency_popup_position_monitor_slider': {'position': (1, 7, 1, 4), 'orientation': 'Horizontal'},

                                                     '_pol_efficiency_popup_position_slider_min_label': {'position': (2, 7, 1, 1)},
                                                     '_pol_efficiency_popup_position_slider_max_label': {'alignment': 'Right', 'position': (2, 10, 1, 1)},

                                                     '_pol_efficiency_popup_current_position_header_label': {'text': 'Current Grid Position:', 'position': (3, 7, 1, 1)},
                                                     '_pol_efficiency_popup_current_position_label': {'text': '0', 'position': (3, 8, 1, 2)},
                                                     '_pol_efficiency_popup_duration_label': {'font': 'small', 'position': (4, 7, 1, 4)},

                                                     '_pol_efficiency_popup_time_stream_label': {'alignment': 'Center', 'position': (5, 7, 4, 4)},

                                                     '_pol_efficiency_popup_mean_header_label': {'text': 'Time Average:', 'position': (9, 7, 1, 1)},
                                                     '_pol_efficiency_popup_mean_label': {'text': '0', 'position': (9, 8, 1, 1)},

                                                     '_pol_efficiency_popup_std_header_label': {'text': 'Standard Dev:', 'position': (9, 9, 1, 1)},
                                                     '_pol_efficiency_popup_std_label': {'text': '0', 'position': (9, 10, 1, 1)},

                                                     '_pol_efficiency_popup_data_label': {'alignment': 'Center', 'position': (10, 7, 8, 4)},

                                                     '_pol_efficiency_popup_min_max_header_label': {'text': 'Min/Max:', 'position': (18, 7, 1, 1)},
                                                     '_pol_efficiency_popup_min_max_label': {'text': '0', 'position': (18, 8, 1, 1)},

                                                     '_pol_efficiency_popup_min_over_max_header_label': {'text': 'Min/Max:', 'position': (18, 9, 1, 1)},
                                                     '_pol_efficiency_popup_min_over_max_label': {'text': '0', 'position': (18, 10, 1, 1)},

}



pol_efficiency_settings.pol_efficiency_combobox_entry_dict = {
                                                              '_pol_efficiency_popup_signal_channel_combobox': ['', '0', '1', '2', '3'],
                                                              '_pol_efficiency_popup_squid_select_combobox': ['', '1', '2', '3', '4', '5', '6'],
                                                              '_pol_efficiency_popup_pause_time_combobox': ['500', '750','1000', '1500', '2000', '3000', '5000', '10000'],
                                                              '_pol_efficiency_popup_integration_time_combobox': ['250', '500', '1000', '1500', '3000'],
                                                              '_pol_efficiency_popup_sample_rate_combobox': ['5000', '6000'],
                                                              '_pol_efficiency_popup_sm_com_port_combobox': ['COM12'],
                                                               }

pol_efficiency_settings.pol_efficiency_scan_params = ['starting_position_lineedit', 'ending_position_lineedit', 'sample_name_lineedit', 'step_size_lineedit',  'grid_angle_lineedit', #ints
                                                      'voltage_bias_lineedit', 'heater_voltage_lineedit',
                                                      'resolution_label', 'max_frequency_label',
                                                      'distance_per_step_combobox', 'squid_select_combobox', 'integration_time_combobox', 'pause_time_combobox',
                                                      'sm_com_port_combobox', 'grid_sm_com_port_combobox', 'signal_channel_combobox', 'sample_rate_combobox',
                                                      ] #combobox

