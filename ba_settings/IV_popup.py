from libraries.gen_class import Class

ivcurve_settings_popup_settings = Class()

ivcurve_settings_popup_settings.ivcurve_popup_build_dict = {
                                                            '_common_settings': {'font': 'med'},
                                                            '_ivcurve_settings_popup_close_pushbutton': {'text': 'Close', 'function': '_close_iv',
                                                                                                         'width': 200, 'height': 150, 'position': (0, 0, 1, 2)},
                                                            '_ivcurve_settings_popup_run_pushbutton': {'text': 'Run', 'function': '_run_analysis',
                                                                                                       'width': 200, 'height': 150, 'position': (0, 3, 1, 2)},
                                                            '_ivcurve_settings_popup_squid_channel_label': {'text': 'SQUID Channel',
                                                                                                            'alignment': 'Center', 'position': (4, 0, 1, 1)},
                                                            '_ivcurve_settings_popup_squid_transimpedance_label': {'text': 'SQ Conv (uA/V)',
                                                                                                                   'alignment': 'Center', 'position': (5, 0, 1, 1)},
                                                            '_ivcurve_settings_popup_voltage_conversion_factor_label': {'text': 'Vol Conv Factor', 'position': (6, 0, 1, 2)},
                                                            '_ivcurve_settings_popup_plot_label_label': {'text': 'Plot Label', 'position': (7, 0, 1, 1)},
                                                            '_ivcurve_settings_popup_v_fit_low_label': {'text': 'V Fit Lo',
                                                                                                         'position': (8, 0, 1, 1)},
                                                            '_ivcurve_settings_popup_v_fit_high_label': {'text': 'V Fit Hi',
                                                                                                          'position': (9, 0, 1, 1)},
                                                            '_ivcurve_settings_popup_v_plot_low_label': {'text': 'V Plot Lo',
                                                                                                         'position': (10, 0, 1, 1)},
                                                            '_ivcurve_settings_popup_v_plot_high_label': {'text': 'V Plot Hi',
                                                                                                          'position': (11, 0, 1, 1)},
                                                            '_ivcurve_settings_popup_calibration_resistor_label': {'text': 'Cal Res',
                                                                                                                   'position': (12, 0, 1, 1)},
                                                            '_ivcurve_settings_popup_fracrn_label': {'text': 'Frac Rn', 'position': (13, 0, 1, 1)},
                                                            '_ivcurve_settings_popup_color_label': {'text': 'Color',
                                                                                                    'position': (14, 0, 1, 1)},
                                                            '_ivcurve_settings_popup_calibrate_squid_label': {'text': 'Calibrate?',
                                                                                                              'position': (15, 0, 1, 1)},
                                                            '_ivcurve_settings_popup_difference_label': {'text': 'Difference?',
                                                                                                         'position': (16, 0, 1, 1)}
                                                           }
