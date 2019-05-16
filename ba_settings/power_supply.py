from libraries.gen_class import Class

power_supply_settings = Class()

power_supply_settings.power_supply_popup_build_dict = {
                                                       '_common_settings': {'font': 'large'},
                                                       '_power_supply_popup_header_label': {'text': 'Control and configure the E3634A PS remotely', 'alignment': 'Center', 'position': (0, 0, 1, 4)},
                                                       # General Control
                                                       '_power_supply_popup_set_voltage_pushbutton': {'text': 'Set Voltage:', 'function': '_set_ps_voltage', 'position': (1, 0, 1, 1)},
                                                       '_power_supply_popup_set_voltage_lineedit': {'text': '0:','position': (1, 1, 1, 1)},
                                                       # Close
                                                       '_power_supply_popup_close_lock_in_pushbutton': {'text': 'Close Power Supply', 'function': '_close_power_supply', 'position': (8, 0, 1, 4)},
                                                         }

power_supply_settings.power_supply_combobox_entry_dict = { }
