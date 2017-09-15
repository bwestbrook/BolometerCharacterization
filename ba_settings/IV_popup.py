from libraries.gen_class import Class

ivcurve_settings_popup_settings = Class()

ivcurve_settings_popup_settings.ivcurve_popup_build_dict = {
                                                            '_common_settings': {'font': 'med'},
                                                            '_ivcurve_settings_popup_squid_channel_label': {'text': 'SQUID Channel',
                                                                                                            'alignment': 'Center', 'position': (1, 1, 1, 1)},
                                                            '_ivcurve_settings_popup_squid_transimpedance_label': {'text': 'SQUID Conv Factor (uA/V)',
                                                                                                                   'alignment': 'Center', 'position': (1, 7, 1, 1)},
                                                            '_ivcurve_settings_popup_voltage_conversion_factor_label': {'text': 'Vol Conv Factor',
                                                                                                                        'alignment': 'Center', 'position': (1, 8, 1, 2)},
                                                            '_ivcurve_settings_popup_plot_label_label': {'text': 'Plot Label', 'position': (1, 10, 1, 1)},
                                                            '_ivcurve_settings_popup_v_clip_low_label': {'text': 'V Clip Lo',
                                                                                                         'position': (1, 11, 1, 1)},
                                                            '_ivcurve_settings_popup_v_clip_high_label': {'text': 'V Clip Hi',
                                                                                                          'position': (1, 12, 1, 1)},
                                                            '_ivcurve_settings_popup_calibration_resistor_label': {'text': 'Calibration Resistance',
                                                                                                                   'position': (1, 13, 1, 1)},
                                                            '_ivcurve_settings_popup_calibrate_squid_label': {'text': 'Calibrate SQUID?',
                                                                                                              'position': (1, 14, 1, 1)},
                                                            '_ivcurve_settings_popup_close_pushbutton': {'text': 'Close', 'function': '_close_iv',
                                                                                                         'position': (0, 0, 1, 15)}
                                                           }
