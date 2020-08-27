from GuiBuilder.gui_builder import GenericClass

power_supply_settings = GenericClass()

power_supply_settings.power_supply_popup_build_dict = {
                                                       '_common_settings': {'font': 'large'},
                                                       '_power_supply_popup_header_label': {'text': 'Control and configure the E3634A PS remotely', 'alignment': 'Center', 'position': (0, 0, 1, 4)},
                                                       # General Control
                                                       '_power_supply_popup_set_voltage_pushbutton': {'text': 'Set Voltage (V):', 'position': (1, 0, 1, 1)},
                                                       '_power_supply_popup_set_voltage_lineedit': {'text': '0','position': (1, 1, 1, 1)},
                                                       '_power_supply_popup_set_voltage_label': {'position': (1, 2, 1, 1)},
                                                       '_power_supply_popup_which_squid_label': {'position': (1, 3, 1, 1)},
                                                       '_power_supply_popup_test_label': {'position': (2, 0, 1, 1), 'color': 'red', 'text': 'Test'},
                                                       '_power_supply_popup_test2_label': {'position': (2, 1, 1, 1), 'color': 'blue', 'text': 'Test2'},
                                                       '_power_supply_popup_overvoltage_pushbutton': {'text': 'Over Voltage', 'position': (2, 4, 1, 1)},
                                                       '_power_supply_popup_overcurrent_pushbutton': {'text': 'Over Current', 'position': (2, 5, 1, 1)},
                                                       '_power_supply_popup_range_selection2_pushbutton': {'text':'50V, 4A','position': (2, 3, 1, 1)},
                                                       '_power_supply_popup_range_selection_pushbutton': {'text':'25V, 7A','position': (2, 2, 1, 1)},
                                                       '_power_supply_popup_display_limit_pushbutton': {'text':'Display Limit','position': (2, 6, 1, 1)},
                                                       '_power_supply_popup_recall_pushbutton': {'text':'Recall','position': (3, 2, 1, 1)},
                                                       '_power_supply_popup_store_pushbutton': {'text':'Store','position': (3, 3, 1, 1)},
                                                       '_power_supply_popup_error_pushbutton': {'text':'Error','position': (3, 4, 1, 1)},
                                                       '_power_supply_popup_io_configuration_pushbutton': {'text':'I/O Config','position': (3, 5, 1, 1)},
                                                       '_power_supply_popup_output_pushbutton': {'text':'Output on/off','position': (3, 6, 1, 1)},
                                                       '_power_supply_popup_voltage_dial_dial': {'dial_min': 5, 'dial_max': 25, 'position': (2, 8, 1, 1)}, 
                                                       # Close
                                                       '_power_supply_popup_close_power_supply_pushbutton': {'text': 'Close Power Supply', 'function': '_close_power_supply', 'position': (8, 0, 1, 9)},
                                                         }

power_supply_settings.power_supply_combobox_entry_dict = { }
