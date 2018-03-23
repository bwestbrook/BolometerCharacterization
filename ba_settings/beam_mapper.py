import numpy as np
from libraries.gen_class import Class

beam_mapper_settings = Class()

beam_mapper_settings.beam_mapper_build_dict = {
                                               '_common_settings': {'font': 'large'},
#HARDWARE SETUP
                                               '_beam_mapper_popup_hardware_setup_label': {'text': 'HARDWARE SETUP', 'alignment': 'Center', 'font': 'huge', 'color': 'blue', 'position': (0, 0, 1, 8)},

                                               '_beam_mapper_popup_start_x_motor_header_label': {'text': 'X MOTOR:', 'position': (1, 0, 1, 1)},
                                               '_beam_mapper_popup_start_x_motor_combobox': {'position': (1, 1, 1, 1)},

                                               '_beam_mapper_popup_start_x_motor_current_label': {'text': 'X MOTOR CURRENT (A):', 'position': (2, 0, 1, 1)},
                                               '_beam_mapper_popup_start_x_motor_current_lineedit': {'position': (2, 1, 1, 1)},

                                               '_beam_mapper_popup_start_x_motor_speed_label': {'text': 'X MOTOR SPEED (steps/s):', 'position': (3, 0, 1, 1)},
                                               '_beam_mapper_popup_start_x_motor_speed_lineedit': {'position': (3, 1, 1, 1)},

                                               '_beam_mapper_popup_end_y_motor_header_label': {'text': 'Y MOTOR', 'position': (1, 2, 1, 1)},
                                               '_beam_mapper_popup_end_y_motor_combobox': {'position': (1, 3, 1, 1)},

                                               #'_beam_mapper_popup_start_y_position_header_label': {'text': 'Start Y Pos (cm)', 'position': (6, 4, 1, 1)},
                                               #'_beam_mapper_popup_start_y_position_lineedit': {'text': '-25', 'position': (6, 5, 1, 1)},
#
                                               #'_beam_mapper_popup_end_y_position_header_label': {'text': 'End Y Pos (cm)', 'position': (6, 6, 1, 1)},
                                               #'_beam_mapper_popup_end_y_position_lineedit': {'text': '25', 'position': (6, 7, 1, 1)},
#SCAN SETUP
                                               '_beam_mapper_popup_scan_setup_label': {'text': 'SCAN SETUP', 'alignment': 'Center', 'font': 'huge', 'color': 'blue', 'position': (5, 0, 1, 8)},

                                               '_beam_mapper_popup_start_x_position_header_label': {'text': 'Start X Pos (cm)', 'position': (6, 0, 1, 1)},
                                               '_beam_mapper_popup_start_x_position_lineedit': {'text': '-25', 'position': (6, 1, 1, 1)},

                                               '_beam_mapper_popup_end_x_position_header_label': {'text': 'End X Pos (cm)', 'position': (6, 2, 1, 1)},
                                               '_beam_mapper_popup_end_x_position_lineedit': {'text': '25', 'position': (6, 3, 1, 1)},

                                               '_beam_mapper_popup_start_y_position_header_label': {'text': 'Start Y Pos (cm)', 'position': (6, 4, 1, 1)},
                                               '_beam_mapper_popup_start_y_position_lineedit': {'text': '-25', 'position': (6, 5, 1, 1)},

                                               '_beam_mapper_popup_end_y_position_header_label': {'text': 'End Y Pos (cm)', 'position': (6, 6, 1, 1)},
                                               '_beam_mapper_popup_end_y_position_lineedit': {'text': '25', 'position': (6, 7, 1, 1)},
#SCAN MONITOR
                                               '_beam_mapper_popup_scan_monitor_label': {'text': 'SCAN MONITOR', 'alignment': 'Center', 'font': 'huge', 'color': 'blue', 'position': (0, 8, 1, 6)},

                                               '_beam_mapper_popup_x_position_header_label': {'text': 'X Pos (cm)', 'position': (1, 8, 1, 1)},
                                               '_beam_mapper_popup_x_position_label': {'text': '', 'position': (1, 9, 1, 1)},

                                               '_beam_mapper_popup_y_position_header_label': {'text': 'Y Pos (cm)', 'position': (1, 10, 1, 1)},
                                               '_beam_mapper_popup_y_position_label': {'text': '', 'position': (1, 11, 1, 1)},
                                               }

beam_mapper_settings.motor_currents = np.linspace(1, 1, 10)
beam_mapper_settings.com_ports = ['COM1', 'COM2', 'COM3', 'COM4']

