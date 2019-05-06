from libraries.gen_class import Class

fridge_cycle_settings = Class()

fridge_cycle_settings.fridge_cycle_popup_build_dict = {
                                                       '_common_settings': {'font': 'huge'},
                                                       '_fridge_cycle_popup_header_label': {'text': 'hello', 'position': (0, 0, 1, 1)},

                                                       '_fridge_cycle_popup_start_resistance_header_label': {'text': 'Start Resistance', 'position': (1, 0, 1, 1)},
                                                       '_fridge_cycle_popup_start_resistance_header_label': {'text': 'Start Resistance', 'position': (1, 0, 1, 1)},
                                                       '_fridge_cycle_popup_start_resistance_lineedit': {'text': '1e6', 'position': (1, 1, 1, 1)},
                                                       '_fridge_cycle_popup_end_resistance_header_label': {'text': 'End Resistance', 'position': (2, 0, 1, 1)},
                                                       '_fridge_cycle_popup_end_resistance_lineedit': {'text': '3.5e3', 'position': (2, 1, 1, 1)},
                                                       '_fridge_cycle_popup_start_cycle_pushbutton': {'text': 'Start Cycle', 'function': '_start_fridge_cycle', 'position': (3, 0, 1, 1)},
                                                       '_fridge_cycle_popup_stop_cycle_pushbutton': {'text': 'Stop Cycle', 'function': '_stop_fridge_cycle', 'position': (3, 1, 1, 1)},
                                                       '_fridge_cycle_popup_close_fridge_cycle_pushbutton': {'text': 'Close', 'function': '_close_fridge_cycle', 'position': (4, 0, 1, 2)},
                                                       }

