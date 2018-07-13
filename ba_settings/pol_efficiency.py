from libraries.gen_class import Class

pol_efficiency_settings = Class()

pol_efficiency_settings.pol_efficiency_build_dict = {    '_common_settings': {'font': 'large'},
# HARDWARE SETUP 
                                                             '_pol_efficiency_popup_hardware_setup_label': {'text': 'HARDWARE SETUP', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (0, 0, 1, 4)},

                                                             '_pol_efficiency_popup_stepper_motor_resource_name_header_label': {'text': 'Stepper Motor Resource Name:', 'position': (1, 0, 1, 1)},
                                                             '_pol_efficiency_popup_current_com_port_combobox': {'function': '_connect_to_com_port', 'position': (1, 1, 1, 1)},

                                                             '_pol_efficiency_popup_signal_channel_header_label': {'text': 'Signal Channel:', 'position': (1, 2, 1, 1)},
                                                             '_pol_efficiency_popup_signal_channel_combobox': {'position': (1, 3, 1, 1)},

                                                             '_pol_efficiency_popup_successful_connection_header_label': {'text': '', 'function': '_connect_to_com_port', 'position': (1, 4, 1, 2)},
                                                         
# SCAN SETUP 
                                                             '_pol_efficiency_popup_scan_setup_label': {'text': 'SCAN SETUP', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (2, 0, 1, 4)},

                                                             '_pol_efficiency_popup_starting_angle_header_label': {'text': 'Starting Angle (Blue):', 'position': (3, 0, 1, 1)},
                                                             '_pol_efficiency_popup_starting_angle_lineedit': {'text': '0', 'function': '_update_pol_efficiency_popup', 'position': (3, 1, 1, 1)},

                                                             '_pol_efficiency_popup_ending_angle_header_label': {'text': 'Ending Angle (Red):', 'position': (3, 2, 1, 1)},
                                                             '_pol_efficiency_popup_ending_angle_lineedit': {'text': '360', 'function': '_update_pol_efficiency_popup', 'position': (3, 3, 1, 1)},

                                                             '_pol_efficiency_popup_step_size_header_label': {'text': 'Step Size:', 'position': (3, 4, 1, 1)},
                                                             '_pol_efficiency_popup_step_size_lineedit': {'text': '60', 'function': '_update_pol_efficiency_popup', 'position': (3, 5, 1, 1)},

                                                             '_pol_efficiency_popup_integration_time_header_label': {'text': 'Integration Time (ms):', 'position': (5, 0, 1, 1)},
                                                             '_pol_efficiency_popup_integration_time_lineedit': {'text': '200', 'position': (5, 1, 1, 1)},

                                                             '_pol_efficiency_popup_pause_time_header_label': {'text': 'Pause (ms):', 'position': (5, 2, 1, 1)},
                                                             '_pol_efficiency_popup_pause_time_lineedit': {'text': '10', 'position': (5, 3, 1, 1)},

                                                             '_pol_efficiency_popup_sample_rate_header_label': {'text': 'Sample Rate (Hz):', 'position': (5, 4, 1, 1)},
                                                             '_pol_efficiency_popup_sample_rate_combobox': {'position': (5, 5, 1, 1)},
# DERIVED QUANTITIES 

                                                             '_pol_efficiency_popup_number_of_steps_header_label': {'text': 'Number of Steps:', 'position': (4, 0, 1, 1)},
                                                             '_pol_efficiency_popup_number_of_steps_label': {'text': '0', 'position': (4, 1, 1, 1)},

#                                                             '_pol_efficiency_popup_highest_frequency_header_label': {'text': 'Highest Freq (Ghz):', 'position': (4, 2, 1, 1)},
 #                                                            '_pol_efficiency_popup_highest_frequency_label': {'text': '0', 'position': (4, 3, 1, 1)},

  #                                                           '_pol_efficiency_popup_resolution_header_label': {'text': 'Resolution (Ghz):', 'position': (4, 4, 1, 1)},
   #                                                          '_pol_efficiency_popup_resolution_label': {'text': '0', 'position': (4, 5, 1, 1)},

# CONTROL BUTTONS
                                                             '_pol_efficiency_popup_control_buttons_label': {'text': 'CONTROLS', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (6, 0, 1, 4)},

                                                             '_pol_efficiency_popup_start_pushbutton': {'text': 'Start', 'function': '_run_pol_efficiency', 'position': (7, 0, 1, 1)},

                                                             '_pol_efficiency_popup_pause_pushbutton': {'text': 'Pause', 'function': '_pause', 'position': (7, 1, 1, 1)},
                                                        

                                                             '_pol_efficiency_popup_close_pushbutton': {'text': 'Close', 'function': '_close_pol_efficiency', 'position': (7, 2, 1, 1)},

# VISUAL DATA MONITORING 
                                                             '_pol_efficiency_popup_data_monitor_label': {'text': 'VISUAL DATA MONITOR', 'font': 'huge', 'color': 'blue',
                                                                                                              'alignment': 'Center', 'position': (0, 7, 1, 4)},
 
                                                             '_pol_efficiency_popup_position_monitor_slider': {'function': None, 'position': (1, 7, 1, 5), 'orientation': 'Horizontal'},

                                                             '_pol_efficiency_popup_mean_header_label': {'text': 'Time Average:', 'position': (3, 7, 1, 1)},
                                                             '_pol_efficiency_popup_mean_label': {'text': '0', 'position': (3, 8, 1, 1)},

                                                             '_pol_efficiency_popup_std_header_label': {'text': 'Standard Dev:', 'position': (4, 7, 1, 1)},
                                                             '_pol_efficiency_popup_std_label': {'text': '0.0', 'position': (4, 8, 1, 1)},

                                                             '_pol_efficiency_popup_current_angle_header_label': {'text': 'Current Angle:', 'position': (5, 7, 1, 1)},
                                                             '_pol_efficiency_popup_current_angle_label': {'text': '0', 'position': (5, 8, 1, 1)},

                                                             '_pol_efficiency_popup_position_slider_min_label': {'text': '0', 'function':'_update_pol_efficiency_popup', 'position': (2, 7, 1, 1)},
                                                             '_pol_efficiency_popup_position_slider_max_label': {'text': '360', 'function':'_update_pol_efficiency_popup', 'position': (2, 11, 1, 1)},

                                                             '_pol_efficiency_popup_time_stream_label': {'alignment': 'Center', 'width': 800, 'height': 400, 'position': (3, 9, 3, 2)},

                                                             '_pol_efficiency_popup_data_label': {'alignment': 'Center', 'width': 800, 'height': 400, 'position': (6, 9, 3, 2)},

                                                            
                                                             '_pol_efficiency_popup_save_pushbutton': {'text': 'Save', 'function': '_final_plot', 'position': (15, 9, 1, 1)},
                                                         

                                                           }




pol_efficiency_settings.pol_efficiency_combobox_entry_dict = {
                                                   '_pol_efficiency_popup_signal_channel_combobox': ['0', '1', '2', '3', '4', '5', '6', '7'],
                                                   '_pol_efficiency_popup_current_com_port_combobox': ['COM1', 'COM2', 'COM3', 'COM4'],
                                                   '_pol_efficiency_popup_sample_rate_combobox': ['50', '100', '250', '500', '1000'],
                                                   }

pol_efficiency_settings.pol_int_run_settings = ['starting_angle', 'ending_angle', 'step_size', 'integration_time', 'pause_time', 'sample_rate']
pol_efficiency_settings.pol_pulldown_run_settings = ['stepper_motor', 'signal_channel', 'sample_rate']
