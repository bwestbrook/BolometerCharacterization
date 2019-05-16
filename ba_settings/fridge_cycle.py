from libraries.gen_class import Class

fridge_cycle_settings = Class()

fridge_cycle_settings.fridge_cycle_popup_build_dict = {
                                                       '_common_settings': {'font': 'large'},
                                                       '_fridge_cycle_popup_header_label': {'text': 'Select Params for Fridge Cycle', 'alignment': 'Center',
                                                                                            'position': (0, 0, 1, 2)},
                                                        # CYCLE PARAMS
                                                       '_fridge_cycle_popup_start_resistance_header_label': {'text': 'Start Resistance', 'position': (1, 0, 1, 1)},
                                                       '_fridge_cycle_popup_start_resistance_lineedit': {'text': '200000.0', 'position': (1, 1, 1, 1)},
                                                       '_fridge_cycle_popup_end_resistance_header_label': {'text': 'End Resistance', 'position': (2, 0, 1, 1)},
                                                       '_fridge_cycle_popup_end_resistance_lineedit': {'text': '3500.0', 'position': (2, 1, 1, 1)},
                                                       '_fridge_cycle_popup_cycle_voltage_header_label': {'text': 'Cycle Voltage', 'position': (3, 0, 1, 1)},
                                                       '_fridge_cycle_popup_cycle_voltage_combobox': {'position': (3, 1, 1, 1)},
                                                       '_fridge_cycle_popup_cycle_end_temperature_header_label': {'text': 'Cycle End Temp:', 'position': (4, 2, 1, 1)},
                                                       '_fridge_cycle_popup_cycle_end_temperature_combobox': {'position': (4, 3, 1, 1)},

                                                        # GRT PARAMS
                                                       '_fridge_cycle_popup_grt_daq_channel_header_label': {'text': 'GRT DAQ:', 'position': (1, 2, 1, 1)},
                                                       '_fridge_cycle_popup_grt_daq_channel_combobox': {'position': (1, 3, 1, 1)},
                                                       '_fridge_cycle_popup_grt_serial_header_label': {'text': 'GRT SERIAL:', 'position': (2, 2, 1, 1)},
                                                       '_fridge_cycle_popup_grt_serial_combobox': {'position': (2, 3, 1, 1)},
                                                       '_fridge_cycle_popup_grt_range_header_label': {'text': 'GRT RANGE:', 'position': (3, 2, 1, 1)},
                                                       '_fridge_cycle_popup_grt_range_combobox': {'position': (3, 3, 1, 1)},

                                                        # Monitoring
                                                       '_fridge_cycle_popup_status_header_label': {'text': 'Status:', 'alignment': 'Right', 'position': (4, 0, 1, 1)},
                                                       '_fridge_cycle_popup_status_label': {'text': 'Idle', 'alignment': 'Left', 'position': (4, 1, 1, 2)},
                                                       '_fridge_cycle_popup_fridge_cycle_plot_label': {'alignment': 'Center', 'position': (5, 0, 1, 4)},
                                                       '_fridge_cycle_popup_abr_resistance_header_label': {'text': 'ABR Res:', 'position': (6, 0, 1, 1)},
                                                       '_fridge_cycle_popup_abr_resistance_value_label': {'position': (6, 1, 1, 1)},
                                                       '_fridge_cycle_popup_ps_voltage_header_label': {'text': 'PS Vol:', 'position': (6, 2, 1, 1)},
                                                       '_fridge_cycle_popup_ps_voltage_value_label': {'position': (6, 3, 1, 1)},
                                                       '_fridge_cycle_popup_grt_temperature_header_label': {'text': 'GRT Temp:', 'position': (7, 0, 1, 1)},
                                                       '_fridge_cycle_popup_grt_temperature_value_label': {'position': (7, 1, 1, 1)},

                                                        # Controls
                                                       '_fridge_cycle_popup_start_cycle_pushbutton': {'text': 'Start Cycle', 'function': '_start_fridge_cycle', 'position': (8, 0, 1, 2)},
                                                       '_fridge_cycle_popup_stop_cycle_pushbutton': {'text': 'Stop Cycle', 'function': '_stop_fridge_cycle', 'position': (8, 2, 1, 2)},
                                                       '_fridge_cycle_popup_man_set_voltage_pushbutton': {'text': 'Set Voltage', 'function': '_set_ps_voltage_fc', 'position': (9, 0, 1, 1)},
                                                       '_fridge_cycle_popup_man_set_voltage_lineedit': {'text': '0', 'position': (9, 1, 1, 1)},
                                                       '_fridge_cycle_popup_close_fridge_cycle_pushbutton': {'text': 'Close', 'function': '_close_fridge_cycle', 'position': (10, 0, 1, 4)},
                                                       }

fridge_cycle_settings.fridge_cycle_combobox_entry_dict = {
                                                          '_fridge_cycle_popup_grt_daq_channel_combobox': [str(x) for x in range(10)],
                                                          '_fridge_cycle_popup_cycle_voltage_combobox': ['2', '25'],
                                                          '_fridge_cycle_popup_grt_serial_combobox': ['', '29268', 'X36942'],
                                                          '_fridge_cycle_popup_grt_range_combobox': ['2', '20', '200', '2K', '20K', '200K', '2M'],
                                                          '_fridge_cycle_popup_cycle_end_temperature_combobox': ['1000', '500', '320', '300', '290', '280'],
                                                         }
