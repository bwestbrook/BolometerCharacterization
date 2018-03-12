from libraries.gen_class import Class

ftscurve_settings_popup_settings = Class()

ftscurve_settings_popup_settings.ftscurve_popup_build_dict = {
                                                              '_common_settings': {'font': 'med'},
                                                              '_ftscurve_settings_popup_close_pushbutton': {'text': 'Close', 'function': '_close_fts',
                                                                                                           'width': 200, 'height': 150, 'position': (0, 0, 1, 2)},
                                                              '_ftscurve_settings_popup_run_pushbutton': {'text': 'Run', 'function': '_run_analysis',
                                                                                                         'width': 200, 'height': 150, 'position': (0, 3, 1, 2)},
                                                              '_ftscurve_settings_popup_plot_title_label': {'text': 'Plot Title', 'position': (4, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_plot_label_label': {'text': 'Plot Label', 'position': (5, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_normalize_label': {'text': 'Normalize?', 'position': (6, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_divide_bs_label': {'text': 'Divide BS:', 'position': (7, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_divide_mmf_label': {'text': 'Divide MMF:', 'position': (8, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_add_atm_model_label': {'text': 'Add ATM:', 'position': (9, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_color_label': {'text': 'Color', 'position': (10, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_xlim_clip_label': {'text': 'X Lim Clip', 'position': (11, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_xlim_plot_label': {'text': 'X Lim Plot', 'position': (12, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_smoothing_factor_label': {'text': 'Smoothing:', 'position': (13, 0, 1, 1)},
                                                              #'_ftscurve_settings_popup_grt_label': {'text': 'GRT Serial', 'position': (3, 0, 1, 1)},
                                                              #'_ftscurve_settings_popup_sample_res_factor_label': {'text': 'Sample Res Factor', 'position': (4, 0, 1, 1)},
                                                              #'_ftscurve_settings_popup_grt_res_factor_label': {'text': 'GRT Res Factor', 'position': (5, 0, 1, 1)},
                                                              #'_ftscurve_settings_popup_normal_res_label': {'text': 'Normal Res', 'position': (6, 0, 1, 1)},
                                                              #'_ftscurve_settings_popup_invert_label': {'text': 'Invert', 'position': (8, 0, 1, 1)}
                                                              }
