from libraries.gen_class import Class

user_move_stepper_settings = Class()

user_move_stepper_settings.user_move_stepper_build_dict = {
                                                           '_common_settings': {'font': 'large'},
                                                           '_user_move_stepper_popup_current_com_port_combobox': {'function': '_connect_to_com_port', 'height': 200,
                                                                                                                  'position': (0, 0, 1, 2)},
                                                           '_user_move_stepper_popup_current_position_header_label': {'text': 'Current Position:',
                                                                                                                      'position': (1, 0, 1, 1)},
                                                           '_user_move_stepper_popup_current_position_label': {'text': '',
                                                                                                               'position': (1, 1, 1, 1)},
                                                           '_user_move_stepper_popup_move_to_position_label': {'text': 'Move Stepper To:',
                                                                                                               'position': (2, 0, 1, 1)},
                                                           '_user_move_stepper_popup_lineedit': {'text': '0',
                                                                                                 'position': (2, 1, 1, 1)},
                                                           '_user_move_stepper_popup_velocity_select_header_label': {'text': 'Stepper Velocity (mm/s):',
                                                                                                                     'position': (3, 0, 1, 1)},
                                                           '_user_move_stepper_popup_velocity_select_lineedit': {'text': '2.0',
                                                                                                                 'position': (3, 1, 1, 1)},
                                                           '_user_move_stepper_popup_move_pushbutton': {'text': 'Move Stepper', 'function': '_move_stepper',
                                                                                                        'position': (4, 0, 1, 2)},
                                                           '_user_move_stepper_popup_reset_zero_pushbutton': {'text': 'Reset Zero', 'function': '_reset_stepper_zero',
                                                                                                              'position': (5, 0, 1, 2)},
                                                           '_user_move_stepper_popup_close_pushbutton': {'text': 'Close User Move Stepper', 'function': '_close_user_move_stepper',
                                                                                                         'position': (6, 0, 1, 2)},
                                                           }

user_move_stepper_settings.com_ports = ['COM1', 'COM2', 'COM3', 'COM4']
