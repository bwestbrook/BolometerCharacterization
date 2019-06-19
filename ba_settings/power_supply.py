from libraries.gen_class import Class

power_supply_settings = Class()

power_supply_settings.power_supply_popup_build_dict = {
                                                       '_common_settings': {'font': 'large'},
                                                       '_power_supply_popup_header_label': {'text': 'Control and configure the E3634A PS remotely', 'alignment': 'Center', 'position': (0, 0, 1, 4)},
                                                       # General Control
                                                       '_power_supply_popup_set_voltage_pushbutton': {'text': 'Set Voltage (V):', 'function': '_set_ps_voltage', 'position': (1, 0, 1, 1)},
                                                       '_power_supply_popup_set_voltage_lineedit': {'text': '0','position': (1, 1, 1, 1)},
                                                       '_power_supply_popup_set_voltage_label': {'position': (1, 2, 1, 1)},
                                                       '_power_supply_popup_which_squid_label': {'position': (1, 3, 1, 1)},
                                                       '_power_supply_popup_test_label': {'position': (2, 0, 1, 1), 'color': 'red', 'text': 'Test'},
                                                       '_power_supply_popup_test2_label': {'position': (2, 1, 1, 1), 'color': 'blue', 'text': 'Test2'},
                                                       '_power_supply_popup_voltage_control_dial': {'function': '_set_ps_voltage_dial', 'dial_min': 0, 'dial_max': 25, 'position': (2, 15, 1, 1)},
                                                       # Close
                                                       '_power_supply_popup_close_power_supply_pushbutton': {'text': 'Close Power Supply', 'function': '_close_power_supply', 'position': (8, 0, 1, 4)},
                                                         }

power_supply_settings.power_supply_combobox_entry_dict = { }
