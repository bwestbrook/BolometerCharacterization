from libraries.gen_class import Class

rtcurve_settings_popup_settings = Class()

rtcurve_settings_popup_settings.rtcurve_popup_build_dict = {
                                                            '_common_settings': {'font': 'med'},
                                                            '_rtcurve_settings_popup_grt_label': {'text': 'GRT Serial',
                                                                                                  'alignment': 'Center', 'position': (2, 0, 1, 3)},
                                                            '_rtcurve_settings_popup_sample_res_factor_label': {'text': 'Sample Res Factor',
                                                                                                                'alignment': 'Center', 'position': (3, 0, 1, 3)},
                                                            '_rtcurve_settings_popup_grt_res_factor_label': {'text': 'GRT Res Factor',
                                                                                                             'alignment': 'Center', 'position': (8, 0, 1, 3)},
                                                            '_rtcurve_settings_popup_normal_res_label': {'text': 'Normal Res',
                                                                                                         'alignment': 'Center', 'position': (10, 0, 1, 1)},
                                                            '_rtcurve_settings_popup_plot_label_label': {'text': 'Plot Label',
                                                                                                         'alignment': 'Center', 'position': (11, 0, 1, 1)},
                                                            '_rtcurve_settings_popup_invert_label': {'text': 'Invert',
                                                                                                     'position': (12, 0, 1, 1)},
                                                            '_rtcurve_settings_popup_close_pushbutton': {'text': 'Run', 'function': '_run_analysis',
                                                                                                         'position': (0, 0, 1, 4)},
                                                            '_rtcurve_settings_popup_close_pushbutton': {'text': 'Close', 'function': '_close_rt',
                                                                                                         'position': (0, 0, 1, 4)}
                                                           }
