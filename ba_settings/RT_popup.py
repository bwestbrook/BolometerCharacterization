from libraries.gen_class import Class

rtcurve_settings_popup_settings = Class()

rtcurve_settings_popup_settings.rtcurve_popup_build_dict = {
                                                            '_common_settings': {'font': 'med'},
                                                            '_rtcurve_settings_popup_grt_label': {'text': 'GRT Serial',
                                                                                                  'alignment': 'Center', 'position': (1, 1, 1, 3)},
                                                            '_rtcurve_settings_popup_sample_res_factor_label': {'text': 'Sample Res Factor',
                                                                                                                'alignment': 'Center', 'position': (1, 4, 1, 3)},
                                                            '_rtcurve_settings_popup_grt_res_factor_label': {'text': 'GRT Res Factor',
                                                                                                             'alignment': 'Center', 'position': (1, 7, 1, 3)},
                                                            '_rtcurve_settings_popup_normal_res_label': {'text': 'Normal Res',
                                                                                                         'alignment': 'Center', 'position': (1, 9, 1, 1)},
                                                            '_rtcurve_settings_popup_plot_label_label': {'text': 'Plot Label',
                                                                                                         'alignment': 'Center', 'position': (1, 10, 1, 1)},
                                                            '_rtcurve_settings_popup_invert_label': {'text': 'Invert',
                                                                                                     'position': (1, 11, 1, 1)},
                                                            '_rtcurve_settings_popup_close_pushbutton': {'text': 'Close', 'function': '_close_rt',
                                                                                                         'position': (0, 0, 1, 12)}
                                                           }
