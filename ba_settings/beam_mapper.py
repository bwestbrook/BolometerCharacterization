import numpy as np
from libraries.gen_class import Class

beam_mapper_settings = Class()

beam_mapper_settings.beam_mapper_build_dict = {
                                               '_common_settings': {'font': 'large'},
#HARDWARE SETUP
                                               '_beam_mapper_popup_hardware_setup_label': {'text': 'HARDWARE SETUP', 'alignment': 'Center', 'font': 'huge', 'color': 'blue', 'position': (0, 0, 1, 6)},

                                               '_beam_mapper_popup_x_motor_header_label': {'text': 'X MOTOR:', 'position': (1, 0, 1, 1)},
                                               '_beam_mapper_popup_x_motor_combobox': {'position': (1, 1, 1, 1)},

                                               '_beam_mapper_popup_x_motor_current_label': {'text': 'X MOTOR CURRENT (A):', 'position': (2, 0, 1, 1)},
                                               '_beam_mapper_popup_x_motor_current_lineedit': {'position': (2, 1, 1, 1)},

                                               '_beam_mapper_popup_x_motor_speed_label': {'text': 'X MOTOR SPEED (steps/s):', 'position': (3, 0, 1, 1)},
                                               '_beam_mapper_popup_x_motor_speed_lineedit': {'position': (3, 1, 1, 1)},

                                               '_beam_mapper_popup_y_motor_header_label': {'text': 'Y MOTOR', 'position': (1, 2, 1, 1)},
                                               '_beam_mapper_popup_y_motor_combobox': {'position': (1, 3, 1, 1)},

                                               '_beam_mapper_popup_y_motor_current_label': {'text': 'Y MOTOR CURRENT (A):', 'position': (2, 2, 1, 1)},
                                               '_beam_mapper_popup_y_motor_current_lineedit': {'position': (2, 3, 1, 1)},

                                               '_beam_mapper_popup_y_motor_speed_label': {'text': 'Y MOTOR SPEED (steps/s):', 'position': (3, 2, 1, 1)},
                                               '_beam_mapper_popup_y_motor_speed_lineedit': {'position': (3, 3, 1, 1)},

                                               '_beam_mapper_popup_DistPerStep_header_label': {'text': 'DistPerStep (nm)', 'position': (4, 0, 1, 1)},
                                               '_beam_mapper_popup_DistPerStep_label': {'text': '253.39', 'position': (4, 1, 1, 1)},

                                               #'_beam_mapper_popup_end_y_position_header_label': {'text': 'End Y Pos (cm)', 'position': (6, 6, 1, 1)},
                                               #'_beam_mapper_popup_end_y_position_lineedit': {'text': '25', 'position': (6, 7, 1, 1)},
#SCAN SETUP
                                               '_beam_mapper_popup_scan_setup_label': {'text': 'SCAN SETUP', 'alignment': 'Center', 'font': 'huge', 'color': 'blue', 'position': (5, 0, 1, 6)},

                                               '_beam_mapper_popup_start_x_position_header_label': {'text': 'Start X Pos (cm)', 'position': (6, 0, 1, 1)},
                                               '_beam_mapper_popup_start_x_position_lineedit': {'function': '_initialize_beam_mapper', 'text': '-50', 'position': (6, 1, 1, 1)},

                                               '_beam_mapper_popup_end_x_position_header_label': {'text': 'End X Pos (cm)', 'position': (7, 0, 1, 1)},
                                               '_beam_mapper_popup_end_x_position_lineedit': {'function': '_initialize_beam_mapper', 'text': '50', 'position': (7, 1, 1, 1)},

                                               '_beam_mapper_popup_start_y_position_header_label': {'text': 'Start Y Pos (cm)', 'position': (6, 2, 1, 1)},
                                               '_beam_mapper_popup_start_y_position_lineedit': {'function': '_initialize_beam_mapper', 'text': '-50', 'position': (6, 3, 1, 1)},

                                               '_beam_mapper_popup_end_y_position_header_label': {'text': 'End Y Pos (cm)', 'position': (7, 2, 1, 1)},
                                               '_beam_mapper_popup_end_y_position_lineedit': {'function': '_initialize_beam_mapper', 'text': '50', 'position': (7, 3, 1, 1)},

                                               '_beam_mapper_popup_n_points_x_header_label': {'text': 'N points X', 'position': (8, 0, 1, 1)},
                                               '_beam_mapper_popup_n_points_x_lineedit': {'text': '15', 'position': (8, 1, 1, 1)},

                                               '_beam_mapper_popup_n_points_y_header_label': {'text': 'N points Y', 'position': (8, 2, 1, 1)},
                                               '_beam_mapper_popup_n_points_y_lineedit': {'text': '15', 'position': (8, 3, 1, 1)},

                                               '_beam_mapper_popup_total_x_header_label': {'text': 'Total X', 'position': (9, 0, 1, 1)},
                                               '_beam_mapper_popup_total_x_label': {'text': '', 'position': (9, 1, 1, 1)},

                                               '_beam_mapper_popup_total_y_header_label': {'text': 'Total Y', 'position': (9, 2, 1, 1)},
                                               '_beam_mapper_popup_total_y_label': {'text': '', 'position': (9, 3, 1, 1)},

                                               '_beam_mapper_popup_step_size_y_header_label': {'text': 'Step Size Y', 'position': (10, 2, 1, 1)},
                                               '_beam_mapper_popup_step_size_y_label': {'text': '', 'position': (10, 3, 1, 1)},

                                               '_beam_mapper_popup_step_size_x_header_label': {'text': 'Step Size X', 'position': (10, 0, 1, 1)},
                                               '_beam_mapper_popup_step_size_x_label': {'text': '', 'position': (10, 1, 1, 1)},

                                               '_beam_mapper_popup_step_size_y_header_label': {'text': 'Step Size Y', 'position': (10, 2, 1, 1)},
                                               '_beam_mapper_popup_step_size_y_label': {'text': '', 'position': (10, 3, 1, 1)},

#CONTROL
                                               '_beam_mapper_popup_controls_label': {'text': 'CONTROLS', 'alignment': 'Center', 'font': 'huge', 'color': 'blue', 'position': (13, 0, 1, 6)},

                                               '_beam_mapper_popup_start_pushbutton': {'text': 'Start', 'function': '_take_beam_map', 'position': (14, 0, 1, 2)},
                                               '_beam_mapper_popup_pause_pushbutton': {'text': 'Pause', 'position': (14, 2, 1, 2)},
                                               '_beam_mapper_popup_cancel_pushbutton': {'text': 'Cancel', 'color': 'red', 'position': (15, 0, 1, 4)},
                                               '_beam_mapper_popup_close_pushbutton': {'function': '_close_beam_mapper', 'text': 'Close', 'position': (16, 0, 1, 4)},

#SCAN MONITOR
                                               '_beam_mapper_popup_scan_monitor_label': {'text': 'SCAN MONITOR', 'alignment': 'Center', 'font': 'huge', 'color': 'blue', 'position': (0, 8, 1, 6)},

                                               '_beam_mapper_popup_x_position_header_label': {'text': 'X Pos (cm)', 'position': (1, 8, 1, 1)},
                                               '_beam_mapper_popup_x_position_label': {'text': '', 'position': (1, 9, 1, 1)},

                                               '_beam_mapper_popup_y_position_header_label': {'text': 'Y Pos (cm)', 'position': (1, 10, 1, 1)},
                                               '_beam_mapper_popup_y_position_label': {'text': '', 'position': (1, 11, 1, 1)},

                                               '_beam_mapper_popup_2D_plot_label': {'position': (2, 8, 4, 4)},
                                               }

beam_mapper_settings.motor_currents = np.linspace(1, 1, 10)
beam_mapper_settings.beam_mapper_combobox_entry_dict = {'_beam_mapper_popup_x_motor_combobox': ['COM1', 'COM2', 'COM3', 'COM4'],
                                                        '_beam_mapper_popup_y_motor_combobox': ['COM1', 'COM2', 'COM3', 'COM4']}

beam_mapper_settings.beam_map_int_settings = ['n_points_x', 'n_points_y', 'start_x_position', 'end_x_position', 'start_y_position', 'end_y_position']



