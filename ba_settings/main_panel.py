from libraries.gen_class import Class

main_panel_settings = Class()

main_panel_settings.main_panel_build_dict = {
                                             '_common_settings': {'font': 'large'},
                                             '_main_panel_welcome_label': {'text': 'Hello, please select an analysis type a file then click run', 'position': (0, 0, 1, 1)},
                                             '_main_panel_select_files_pushbutton': {'text': 'Select File(s)', 'function': '_select_files', 'position': (1, 0, 1, 6)},
                                             '_main_panel_clear_files_pushbutton': {'text': 'Clear Files', 'function': '_clear_files', 'position': (2, 0, 1, 6)},
                                             '_main_panel_selected_file_label': {'text': '', 'position': (3, 0, 1, 6)},
                                             '_main_panel_ivcurve_pushbutton': {'text': 'IV_Curve', 'function': '_select_analysis_type', 'position': (4, 0, 1, 1)},
                                             '_main_panel_rtcurve_pushbutton': {'text': 'RT_Curve', 'function': '_select_analysis_type', 'position': (4, 1, 1, 1)},
                                             '_main_panel_ftscurve_pushbutton': {'text': 'FTS_Curve', 'function': '_select_analysis_type', 'position': (4, 2, 1, 1)},
                                             '_main_panel_ifcurve_pushbutton': {'text': 'IF_Curve', 'function': '_select_analysis_type', 'position': (4, 3, 1, 1)},
                                             '_main_panel_polcurve_pushbutton': {'text': 'POL_Curve', 'function': '_select_analysis_type', 'position': (4, 4, 1, 1)},
                                             '_main_panel_taucurve_pushbutton': {'text': 'TAU_Curve', 'function': '_select_analysis_type', 'position': (4, 5, 1, 1)},
                                             '_main_panel_close_pushbutton': {'text': 'Close', 'function': '_close_main', 'position': (6, 0, 1, 6)}
                                             }
