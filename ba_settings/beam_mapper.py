import numpy as np
from libraries.gen_class import Class

beam_mapper_settings = Class()

beam_mapper_settings.beam_mapper_build_dict = {
                                               '_common_settings': {'font': 'large'},
#HARDWARE SETUP
                                               '_beam_mapper_popup_hardware_setup_label': {'text': 'HARDWARE SETUP', 'alignment': 'Center', 'font': 'huge', 'color': 'blue', 'position': (0, 0, 1, 6)},

                                               '_beam_mapper_popup_x_motor_header_label': {'text': 'X MOTOR:', 'position': (1, 0, 1, 1)},
                                               '_beam_mapper_popup_x_current_com_port_combobox': {'function': '_connect_to_com_port','position': (1, 1, 1, 1)},
                                               '_beam_mapper_popup_x_successful_connection_header_label': {'text': '', 'position': (2, 0, 1, 2)},

                                               '_beam_mapper_popup_x_motor_current_header_label': {'text': 'X MOTOR CURRENT (A):', 'position': (3, 0, 1, 1)},
                                               '_beam_mapper_popup_x_motor_current_label': {'position': (3, 1, 1, 1)},

                                               '_beam_mapper_popup_x_motor_velocity_header_label': {'text': 'X velocity (mm/s):', 'position': (4, 0, 1, 1)},
                                               '_beam_mapper_popup_x_motor_velocity_label': {'position': (4, 1, 1, 1)},

                                               '_beam_mapper_popup_y_motor_header_label': {'text': 'Y MOTOR', 'position': (1, 2, 1, 1)},
                                               '_beam_mapper_popup_y_current_com_port_combobox': {'function': '_connect_to_com_port','position': (1, 3, 1, 1)},
                                               '_beam_mapper_popup_y_successful_connection_header_label': {'text': '', 'position': (2, 2, 1, 2)},

                                               '_beam_mapper_popup_y_motor_current_header_label': {'text': 'Y MOTOR CURRENT (A):', 'position': (3, 2, 1, 1)},
                                               '_beam_mapper_popup_y_motor_current_label': {'position': (3, 3, 1, 1)},

                                               '_beam_mapper_popup_y_motor_velocity_header_label': {'text': 'Y Velocity (mm/s):', 'position': (4, 2, 1, 1)},
                                               '_beam_mapper_popup_y_motor_velocity_label': {'position': (4, 3, 1, 1)},

                                               '_beam_mapper_popup_DistPerStep_header_label': {'text': 'DistPerStep (nm)', 'position': (5, 0, 1, 1)},
                                               '_beam_mapper_popup_DistPerStep_label': {'text': '253.39', 'position': (5, 1, 1, 1)},
#SCAN SETUP
                                               '_beam_mapper_popup_scan_setup_label': {'text': 'SCAN SETUP', 'alignment': 'Center', 'font': 'huge', 'color': 'blue', 'position': (6, 0, 1, 6)},

                                               '_beam_mapper_popup_start_x_position_header_label': {'text': 'Start X Pos (steps)', 'position': (7, 0, 1, 1)},
                                               '_beam_mapper_popup_start_x_position_lineedit': {'function': '_initialize_beam_mapper', 'text': '-100000', 'position': (7, 1, 1, 1)},

                                               '_beam_mapper_popup_end_x_position_header_label': {'text': 'End X Pos (steps)', 'position': (8, 0, 1, 1)},
                                               '_beam_mapper_popup_end_x_position_lineedit': {'function': '_initialize_beam_mapper', 'text': '100000', 'position': (8, 1, 1, 1)},

                                               '_beam_mapper_popup_start_y_position_header_label': {'text': 'Start Y Pos (steps)', 'position': (7, 2, 1, 1)},
                                               '_beam_mapper_popup_start_y_position_lineedit': {'function': '_initialize_beam_mapper', 'text': '-100000', 'position': (7, 3, 1, 1)},

                                               '_beam_mapper_popup_end_y_position_header_label': {'text': 'End Y Pos (steps)', 'position': (8, 2, 1, 1)},
                                               '_beam_mapper_popup_end_y_position_lineedit': {'function': '_initialize_beam_mapper', 'text': '100000', 'position': (8, 3, 1, 1)},

                                               '_beam_mapper_popup_n_points_x_header_label': {'text': 'N points X', 'position': (11, 0, 1, 1)},
                                               '_beam_mapper_popup_n_points_x_label': {'text': '', 'position': (11, 1, 1, 1)},

                                               '_beam_mapper_popup_n_points_y_header_label': {'text': 'N points Y', 'position': (11, 2, 1, 1)},
                                               '_beam_mapper_popup_n_points_y_label': {'text': '', 'position': (11, 3, 1, 1)},

                                               '_beam_mapper_popup_total_x_header_label': {'text': 'Total X', 'position': (10, 0, 1, 1)},
                                               '_beam_mapper_popup_total_x_label': {'text': '', 'position': (10, 1, 1, 1)},

                                               '_beam_mapper_popup_total_y_header_label': {'text': 'Total Y', 'position': (10, 2, 1, 1)},
                                               '_beam_mapper_popup_total_y_label': {'text': '', 'position': (10, 3, 1, 1)},

                                               '_beam_mapper_popup_step_size_x_header_label': {'text': 'Step Size X', 'position': (9, 0, 1, 1)},
                                               '_beam_mapper_popup_step_size_x_lineedit': {'function': '_initialize_beam_mapper', 'text': '50000', 'position': (9, 1, 1, 1)},

                                               '_beam_mapper_popup_step_size_y_header_label': {'text': 'Step Size Y', 'position': (9, 2, 1, 1)},
                                               '_beam_mapper_popup_step_size_y_lineedit': {'function': '_initialize_beam_mapper', 'text': '50000', 'position': (9, 3, 1, 1)},

                                               '_beam_mapper_popup_integration_time_header_label': {'text': 'Integration Time (ms):', 'position': (12, 0, 1, 1)},
                                               '_beam_mapper_popup_integration_time_combobox': {'position': (12, 1, 1, 1)},

                                               '_beam_mapper_popup_pause_time_header_label': {'text': 'Pause (ms):', 'position': (12, 2, 1, 1)},
                                               '_beam_mapper_popup_pause_time_combobox': {'position': (12, 3, 1, 1)},

                                               '_beam_mapper_popup_signal_channel_header_label': {'text': 'Signal Channel', 'position': (13, 0, 1, 1)},
                                               '_beam_mapper_popup_signal_channel_combobox': {'position': (13, 1, 1, 1)},

                                               '_beam_mapper_popup_sample_rate_header_label': {'text': 'Sample Rate (Hz):', 'position': (13, 2, 1, 1)},
                                               '_beam_mapper_popup_sample_rate_combobox': {'position': (13, 3, 1, 1)},

                                               '_beam_mapper_popup_squid_select_header_label': {'text': 'SQUID:', 'position': (14, 0, 1, 1)},
                                               '_beam_mapper_popup_squid_select_combobox': {'function': '_update_squid_calibration', 'position': (14, 1, 1, 1)},

                                               '_beam_mapper_popup_sample_name_header_label': {'text': 'SQUID:', 'position': (14, 2, 1, 1)},
                                               '_beam_mapper_popup_sample_name_lineedit': {'position': (14, 3, 1, 1)},
#CONTROL
                                               '_beam_mapper_popup_controls_label': {'text': 'CONTROLS', 'alignment': 'Center', 'font': 'huge', 'color': 'blue', 'position': (15, 0, 1, 6)},

                                               '_beam_mapper_popup_start_pushbutton': {'text': 'Start', 'function': '_take_beam_map', 'position': (16, 0, 1, 2)},
                                               #'_beam_mapper_popup_pause_pushbutton': {'text': 'Pause', 'position': (15, 2, 1, 2)},
                                               '_beam_mapper_popup_cancel_pushbutton': {'text': 'Cancel', 'color': 'red', 'function': '_stop', 'position': (17, 0, 1, 4)},
                                               '_beam_mapper_popup_close_pushbutton': {'function': '_close_beam_mapper', 'text': 'Close', 'position': (18, 0, 1, 4)},
                                               '_beam_mapper_popup_save_pushbutton': {'text': 'Save', 'function': '_final_plot', 'position': (19, 0, 1, 4)},
#SCAN MONITOR
                                               '_beam_mapper_popup_scan_monitor_label': {'text': 'SCAN MONITOR', 'alignment': 'Center', 'font': 'huge', 'color': 'blue', 'position': (0, 8, 1, 6)},

                                               '_beam_mapper_popup_x_position_header_label': {'text': 'X Pos (steps)', 'position': (1, 8, 1, 1)},
                                               '_beam_mapper_popup_x_position_label': {'text': '', 'position': (1, 9, 1, 1)},

                                               '_beam_mapper_popup_y_position_header_label': {'text': 'Y Pos (steps)', 'position': (1, 10, 1, 1)},
                                               '_beam_mapper_popup_y_position_label': {'text': '', 'position': (1, 11, 1, 1)},

                                               '_beam_mapper_popup_data_mean_header_label': {'text': 'Data Mean:', 'position': (2, 8, 1, 1)},
                                               '_beam_mapper_popup_data_mean_label': {'text': '', 'position': (2, 9, 1, 1)},

                                               '_beam_mapper_popup_data_std_header_label': {'text': 'Data STD:', 'position': (2, 10, 1, 1)},
                                               '_beam_mapper_popup_data_std_label': {'text': '', 'position': (2, 11, 1, 1)},

                                               '_beam_mapper_popup_status_label': {'position': (3, 8, 1, 2)},

                                               '_beam_mapper_popup_time_stream_label': {'position': (4, 8, 4, 4)},

                                               '_beam_mapper_popup_2D_plot_label': {'alignment': 'Center', 'position': (9, 8, 10, 4)},
                                               }

beam_mapper_settings.motor_currents = np.linspace(1, 1, 10)
beam_mapper_settings.beam_mapper_combobox_entry_dict = {'_beam_mapper_popup_x_current_com_port_combobox': ['COM12'],
                                                        '_beam_mapper_popup_y_current_com_port_combobox': ['COM5'],
                                                        '_beam_mapper_popup_integration_time_combobox': ['500', '1000'],
                                                        '_beam_mapper_popup_pause_time_combobox': ['500', '1000'],
                                                        '_beam_mapper_popup_sample_rate_combobox': ['1000', '2500', '5000'],
                                                        '_beam_mapper_popup_squid_select_combobox': ['', '1', '2', '3', '4', '5', '6'],
                                                        '_beam_mapper_popup_signal_channel_combobox': ['0', '1', '2', '3', '4', '5', '6', '7']}

beam_mapper_settings.beam_map_int_settings = ['step_size_x', 'start_x_position', 'end_x_position',
                                              'step_size_y', 'start_y_position', 'end_y_position',
                                              'integration_time', 'pause_time']

beam_mapper_settings.beam_map_pulldown_run_settings = ['x_motor', 'y_motor', 'signal_channel', 'sample_rate']


beam_mapper_settings.beam_mapper_params = ['pause_time_lineedit',
                                           'start_x_position_lineedit',
                                           'end_x_position_lineedit',
                                           'n_points_x_label',
                                           'step_size_x_lineedit',
                                           'x_current_com_port_combobox',
                                           'start_y_position_lineedit',
                                           'end_y_position_lineedit',
                                           'n_points_y_label',
                                           'step_size_y_lineedit',
                                           'y_current_com_port_combobox',
                                           'squid_select_combobox',
                                           'sample_name_lineedit',
                                           'signal_channel_combobox',
                                           'integration_time_combobox',
                                           'pause_time_combobox',
                                           'sample_rate_combobox',
                                           ]



