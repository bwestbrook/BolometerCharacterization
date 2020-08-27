from GuiBuilder.gui_builder import GenericClass

fridge_cycle_settings = GenericClass()

fridge_cycle_settings.fridge_cycle_popup_build_dict = {
                                                       '_common_settings': {'font': 'large'},
                                                       '_fridge_cycle_popup_header_label': {'text': 'FC Params', 'alignment': 'Center', 'position': (0, 0, 1, 2)},
                                                        # CYCLE PARAMS
                                                       '_fridge_cycle_popup_start_resistance_header_label': {'text': 'Start Resistance', 'position': (1, 0, 1, 1)},
                                                       '_fridge_cycle_popup_start_resistance_lineedit': {'text': '200000.0', 'position': (1, 1, 1, 1)},
                                                       '_fridge_cycle_popup_end_resistance_header_label': {'text': 'End Resistance', 'position': (2, 0, 1, 1)},
                                                       '_fridge_cycle_popup_end_resistance_lineedit': {'text': '3500.0', 'position': (2, 1, 1, 1)},
                                                       '_fridge_cycle_popup_cycle_voltage_header_label': {'text': 'Cycle Voltage', 'position': (3, 0, 1, 1)},
                                                       '_fridge_cycle_popup_cycle_voltage_combobox': {'position': (3, 1, 1, 1)},
                                                       '_fridge_cycle_popup_cycle_end_temperature_label': {'position': (4, 0, 1, 1)},
                                                       '_fridge_cycle_popup_cycle_end_temperature_combobox': {'position': (4, 1, 1, 1)},

                                                        # GRT PARAMS
                                                       '_fridge_cycle_popup_grt_daq_channel_header_label': {'text': 'GRT DAQ:', 'position': (5, 0, 1, 1)},
                                                       '_fridge_cycle_popup_grt_daq_channel_combobox': {'position': (5, 1, 1, 1)},
                                                       '_fridge_cycle_popup_grt_serial_header_label': {'text': 'GRT SERIAL:', 'position': (6, 0, 1, 1)},
                                                       '_fridge_cycle_popup_grt_serial_combobox': {'position': (6, 1, 1, 1)},
                                                       '_fridge_cycle_popup_grt_range_header_label': {'text': 'GRT RANGE:', 'position': (7, 0, 1, 1)},
                                                       '_fridge_cycle_popup_grt_range_combobox': {'position': (7, 1, 1, 1)},

                                                        # Monitoring
                                                       '_fridge_cycle_popup_fridge_cycle_plot_label': {'alignment': 'Right', 'position': (1, 2, 12, 2)},

                                                       '_fridge_cycle_popup_status_label': {'text': 'Idle', 'alignment': 'Center', 'position': (0, 2, 1, 2)},

                                                       '_fridge_cycle_popup_abr_resistance_header_label': {'text': 'ABR Res:', 'position': (8, 0, 1, 1)},
                                                       '_fridge_cycle_popup_abr_resistance_value_label': {'position': (8, 1, 1, 1)},

                                                       '_fridge_cycle_popup_abr_temperature_header_label': {'text': 'ABR Temp:', 'position': (9, 0, 1, 1)},
                                                       '_fridge_cycle_popup_abr_temperature_value_label': {'position': (9, 1, 1, 1)},

                                                       '_fridge_cycle_popup_grt_temperature_header_label': {'text': 'GRT Temp:', 'position': (10, 0, 1, 1)},
                                                       '_fridge_cycle_popup_grt_temperature_value_label': {'position': (10, 1, 1, 1)},

                                                       '_fridge_cycle_popup_ps_voltage_header_label': {'text': 'PS Vol:', 'position': (11, 0, 1, 1)},
                                                       '_fridge_cycle_popup_ps_voltage_value_label': {'position': (11, 1, 1, 1)},

                                                        # Controls
                                                       '_fridge_cycle_popup_start_cycle_pushbutton': {'text': 'Start Cycle', 'function': '_start_fridge_cycle', 'position': (11, 2, 1, 2)},
                                                       '_fridge_cycle_popup_stop_cycle_pushbutton': {'text': 'Stop Cycle', 'function': '_stop_fridge_cycle', 'position': (12, 2, 1, 2)},
                                                       '_fridge_cycle_popup_man_set_voltage_pushbutton': {'text': 'Set Voltage', 'function': '_set_ps_voltage_fc', 'position': (11, 0, 1, 1)},
                                                       '_fridge_cycle_popup_man_set_voltage_lineedit': {'text': '0', 'position': (11, 1, 1, 1)},
                                                       '_fridge_cycle_popup_close_fridge_cycle_pushbutton': {'text': 'Close', 'function': '_close_fridge_cycle', 'position': (13, 2, 1, 2)},
                                                       }

fridge_cycle_settings.fridge_cycle_combobox_entry_dict = {
                                                          '_fridge_cycle_popup_grt_daq_channel_combobox': [str(x) for x in range(10)],
                                                          '_fridge_cycle_popup_cycle_voltage_combobox': ['2', '25'],
                                                          '_fridge_cycle_popup_grt_serial_combobox': ['', '29268', 'X36942'],
                                                          '_fridge_cycle_popup_grt_range_combobox': ['2', '20', '200', '2K', '20K', '200K', '2M'],
                                                          '_fridge_cycle_popup_cycle_end_temperature_combobox': ['1000', '500', '320', '300', '290', '280'],
                                                         }
