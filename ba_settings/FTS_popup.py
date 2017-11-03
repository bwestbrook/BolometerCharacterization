from libraries.gen_class import Class

ftscurve_settings_popup_settings = Class()

ftscurve_settings_popup_settings.ftscurve_popup_build_dict = {
                                                              '_common_settings': {'font': 'med'},
                                                              '_ftscurve_settings_popup_close_pushbutton': {'text': 'Close', 'function': '_close_fts',
                                                                                                           'width': 200, 'height': 150, 'position': (0, 0, 1, 2)},
                                                              '_ftscurve_settings_popup_run_pushbutton': {'text': 'Run', 'function': '_run_analysis',
                                                                                                         'width': 200, 'height': 150, 'position': (0, 3, 1, 2)},
                                                              '_ftscurve_settings_popup_plot_label_label': {'text': 'Plot Label', 'position': (4, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_normalize_label': {'text': 'Normalize?', 'position': (5, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_color_label': {'text': 'Color', 'position': (6, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_xlim_label': {'text': 'X Lim', 'position': (7, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_smoothing_factor_label': {'text': 'Smoothing:', 'position': (8, 0, 1, 1)},
                                                              #'_ftscurve_settings_popup_grt_label': {'text': 'GRT Serial', 'position': (3, 0, 1, 1)},
                                                              #'_ftscurve_settings_popup_sample_res_factor_label': {'text': 'Sample Res Factor', 'position': (4, 0, 1, 1)},
                                                              #'_ftscurve_settings_popup_grt_res_factor_label': {'text': 'GRT Res Factor', 'position': (5, 0, 1, 1)},
                                                              #'_ftscurve_settings_popup_normal_res_label': {'text': 'Normal Res', 'position': (6, 0, 1, 1)},
                                                              #'_ftscurve_settings_popup_invert_label': {'text': 'Invert', 'position': (8, 0, 1, 1)}
                                                             }
