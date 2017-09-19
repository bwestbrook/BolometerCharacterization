from libraries.gen_class import Class

main_panel_settings = Class()

main_panel_settings.main_panel_build_dict = {
                                             '_common_settings': {'font': 'med'},
                                             '_main_panel_welcome_label': {'text': 'Hello, please select an analysis type a file then click run',
                                                                           'position': (0, 0, 1, 1)},
                                             '_main_panel_select_files_pushbutton': {'text': 'Select File(s)', 'function': '_select_files',
                                                                                     'position': (1, 0, 1, 2)},
                                             '_main_panel_selected_file_label': {'text': '',
                                                                                 'position': (2, 0, 1, 2)},
                                             '_main_panel_clear_files_pushbutton': {'text': 'Clear Files', 'function': '_clear_files',
                                                                                    'position': (3, 0, 1, 2)},
                                             '_main_panel_ivcurve_checkbox': {'text': 'IV_Curve', 'function': '_select_analysis_type',
                                                                              'position': (4, 0, 1, 1)},
                                             '_main_panel_rtcurve_checkbox': {'text': 'RT_Curve', 'function': '_select_analysis_type',
                                                                              'position': (4, 1, 1, 1)},
                                             '_main_panel_run_pushbutton': {'text': 'Run', 'function': '_run_analysis',
                                                                            'position': (5, 0, 1, 2)},
                                             '_main_panel_close_pushbutton': {'text': 'Close', 'function': '_close_main',
                                                                              'position': (6, 0, 1, 2)}
                                             }
