from libraries.gen_class import Class

taucurve_settings_popup_settings = Class()

taucurve_settings_popup_settings.taucurve_popup_build_dict = {
                                                              '_common_settings': {'font': 'med'},
                                                              '_taucurve_settings_popup_welcome_label': {'text': 'Tau Curve Settings', 'position': (0, 0, 1, 2)},
                                                              '_taucurve_settings_popup_title_header_label': {'text': 'Plot Title', 'position': (0, 2, 1, 2)},
                                                              '_taucurve_settings_popup_title_lineedit': {'text': '', 'position': (0, 4, 1, 2)},
                                                              '_taucurve_settings_popup_plot_pushbutton': {'text': 'Plot', 'function': '_plot_taucurve',
                                                                                                           'position': (6, 0, 1, 2)},
                                                              '_taucurve_settings_popup_close_pushbutton': {'text': 'Close', 'function': '_close_tau_popup',
                                                                                                            'position': (7, 0, 1, 2)},
                                                              }
