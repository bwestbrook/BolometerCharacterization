from GuiBuilder.gui_builder import GenericClass

rtcurve_settings_popup_settings = GenericClass()

rtcurve_settings_popup_settings.rtcurve_popup_build_dict = {
                                                            '_common_settings': {'font': 'med'},
                                                            '_rtcurve_settings_popup_close_pushbutton': {'text': 'Close', 'function': '_close_rt',
                                                                                                         'width': 200, 'height': 150, 'position': (0, 0, 1, 2)},
                                                            '_rtcurve_settings_popup_run_pushbutton': {'text': 'Run', 'function': '_run_analysis',
                                                                                                       'width': 200, 'height': 150, 'position': (0, 3, 1, 2)},
                                                            '_rtcurve_settings_popup_grt_label': {'text': 'GRT Serial', 'position': (3, 0, 1, 1)},
                                                            '_rtcurve_settings_popup_sample_res_factor_label': {'text': 'Sample Res Factor', 'position': (4, 0, 1, 1)},
                                                            '_rtcurve_settings_popup_grt_res_factor_label': {'text': 'GRT Res Factor', 'position': (5, 0, 1, 1)},
                                                            '_rtcurve_settings_popup_normal_res_label': {'text': 'Normal Res', 'position': (6, 0, 1, 1)},
                                                            '_rtcurve_settings_popup_plot_label_label': {'text': 'Plot Label', 'position': (7, 0, 1, 1)},
                                                            '_rtcurve_settings_popup_invert_label': {'text': 'Invert', 'position': (8, 0, 1, 1)}
                                                           }
