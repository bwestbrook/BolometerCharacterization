from libraries.gen_class import Class

polcurve_settings_popup_settings = Class()

polcurve_settings_popup_settings.polcurve_popup_build_dict = {
                                                              '_common_settings': {'font': 'med'},
                                                              '_polcurve_settings_popup_close_pushbutton': {'text': 'Close', 'function': '_close_pol',
                                                                                                            'width': 200, 'height': 150, 'position': (0, 0, 1, 2)},
                                                              '_polcurve_settings_popup_run_pushbutton': {'text': 'Run', 'function': '_run_analysis',
                                                                                                          'width': 200, 'height': 150, 'position': (0, 3, 1, 2)},
                                                              '_polcurve_settings_popup_plot_label_label': {'text': 'Plot Label', 'position': (4, 0, 1, 1)},
                                                              '_polcurve_settings_popup_normalize_label': {'text': 'Normalize?', 'position': (5, 0, 1, 1)},
                                                              '_polcurve_settings_popup_color_label': {'text': 'Color', 'position': (6, 0, 1, 1)},
                                                              '_polcurve_settings_popup_xlim_label': {'text': 'X Lim', 'position': (7, 0, 1, 1)},
                                                              '_polcurve_settings_popup_smoothing_factor_label': {'text': 'Smoothing:', 'position': (8, 0, 1, 1)},
                                                             }
