from libraries.gen_class import Class

daq_main_panel_settings = Class()

daq_main_panel_settings.daq_main_panel_build_dict = {
                                                     '_common_settings': {'font': 'huge'},
                                                     '_daq_main_panel_welcome_label': {'text': 'Hello, please select a DAQ type',
                                                                                       'font': 'huge', 'position': (0, 0, 1, 4)},
                                                     '_daq_main_panel_daq_select_combobox': {'function': '_launch_daq', 'height': 600,
                                                                                             'position': (1, 0, 1, 4)},
                                                     '_daq_main_panel_close_pushbutton': {'text': 'Close', 'function': '_close_main', 'height': 200,
                                                                                          'position': (2, 0, 1, 4)}
                                                     }

daq_main_panel_settings.daq_functions = ['_user_move_stepper', '_single_channel_fts']
