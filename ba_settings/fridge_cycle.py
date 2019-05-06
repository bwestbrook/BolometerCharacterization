from libraries.gen_class import Class

fridge_cycle_settings = Class()

fridge_cycle_settings.fridge_cycle_popup_build_dict = {
                                                       '_common_settings': {'font': 'huge'},
                                                       '_fridge_cycle_popup_header_label': {'text': 'hello', 'position': (0, 0, 1, 1)},

                                                       '_fridge_cycle_popup_start_resistance_header_label': {'text': 'Start Resistance', 'position': (1, 0, 1, 1)},
                                                       '_fridge_cycle_popup_start_resistance_header_label': {'text': 'Start Resistance', 'position': (1, 0, 1, 1)},
                                                       '_fridge_cycle_popup_start_resistance_lineedit': {'text': '1000.0', 'position': (1, 1, 1, 1)},
                                                       '_fridge_cycle_popup_end_resistance_header_label': {'text': 'End Resistance', 'position': (2, 0, 1, 1)},
                                                       '_fridge_cycle_popup_end_resistance_lineedit': {'text': '500.0', 'position': (2, 1, 1, 1)},
                                                       '_fridge_cycle_popup_cycle_voltage_header_label': {'text': 'Cycle Voltage', 'position': (3, 0, 1, 1)},
                                                       '_fridge_cycle_popup_cycle_voltage_lineedit': {'text': '25', 'position': (3, 1, 1, 1)},
                                                       '_fridge_cycle_popup_resistance_hisory_label': {'position': (4, 0, 1, 1)},
                                                       '_fridge_cycle_popup_voltage_hisory_label': {'position': (4, 1, 1, 1)},
                                                       '_fridge_cycle_popup_resistance_value_label': {'position': (5, 0, 1, 1)},
                                                       '_fridge_cycle_popup_voltage_value_label': {'position': (5, 1, 1, 1)},
                                                       '_fridge_cycle_popup_start_cycle_pushbutton': {'text': 'Start Cycle', 'function': '_start_fridge_cycle', 'position': (6, 0, 1, 1)},
                                                       '_fridge_cycle_popup_stop_cycle_pushbutton': {'text': 'Stop Cycle', 'function': '_stop_fridge_cycle', 'position': (6, 1, 1, 1)},
                                                       '_fridge_cycle_popup_close_fridge_cycle_pushbutton': {'text': 'Close', 'function': '_close_fridge_cycle', 'position': (7, 0, 1, 2)},
                                                       }

