from libraries.gen_class import Class

user_move_stepper_settings = Class()

user_move_stepper_settings.user_move_stepper_build_dict = {
                                                           '_common_settings': {'font': 'large'},


                                                           '_user_move_stepper_popup_com_ports_header_label': {'text': 'Select a Com Port:', 'position': (0, 0, 1, 1)},
                                                           '_user_move_stepper_popup_com_ports_combobox': {'function': '_connect_to_com_port', 'position': (0, 1, 1, 1)},
                                                           '_user_move_stepper_popup_successful_connection_header_label': {'position': (0, 2, 1, 1)},

                                                           '_user_move_stepper_popup_control_label': {'text': 'CONTROL', 'position': (1, 0, 1, 1)},
                                                           '_user_move_stepper_popup_set_to_label': {'text': 'SET TO', 'position': (1, 1, 1, 1)},
                                                           '_user_move_stepper_popup_actual_label': {'text': 'ACTUAL', 'position': (1, 2, 1, 2)},

                                                           '_user_move_stepper_popup_move_pushbutton': {'text': 'Move Stepper To:', 'function': '_move_stepper', 'position': (2, 0, 1, 1)},
                                                           '_user_move_stepper_popup_move_to_position_lineedit': {'text': '0', 'position': (2, 1, 1, 1)},
                                                           '_user_move_stepper_popup_current_position_label': {'position': (2, 2, 1, 2)},

                                                           '_user_move_stepper_popup_set_current_pushbutton': {'text': 'Set Current Current to:', 'function': '_set_current', 'position': (3, 0, 1, 1)},
                                                           '_user_move_stepper_popup_set_current_to_lineedit': {'text': '1.0', 'function': '_limit_current', 'position': (3, 1, 1, 1)},
                                                           '_user_move_stepper_popup_actual_current_label': {'position': (3, 2, 1, 2)},

                                                           '_user_move_stepper_popup_set_velocity_pushbutton': {'text': 'Set Velocity to: (mm/s)', 'function': '_set_velocity', 'position': (4, 0, 1, 1)},
                                                           '_user_move_stepper_popup_set_velocity_to_lineedit': {'text': '2.0', 'position': (4, 1, 1, 1)},
                                                           '_user_move_stepper_popup_actual_velocity_label': {'position': (4, 2, 1, 2)},

                                                           '_user_move_stepper_popup_set_acceleration_pushbutton': {'text': 'Set Acceleration to: (mm/s/s)', 'function': '_set_acceleration', 'position': (5, 0, 1, 1)},
                                                           '_user_move_stepper_popup_set_acceleration_to_lineedit': {'text': '25', 'position': (5, 1, 1, 1)},
                                                           '_user_move_stepper_popup_actual_acceleration_label': {'position': (5, 2, 1, 2)},

                                                           '_user_move_stepper_popup_reset_zero_pushbutton': {'text': 'Reset Zero', 'function': '_reset_stepper_zero', 'position': (7, 0, 1, 5)},
                                                           '_user_move_stepper_popup_close_pushbutton': {'text': 'Close User Move Stepper', 'function': '_close_user_move_stepper', 'position': (8, 0, 1, 5)},
                                                           }


user_move_stepper_settings.user_move_stepper_combobox_entry_dict = {
                                                                    '_user_move_stepper_popup_current_com_port_combobox': ['COM8'],
                                                                    }
