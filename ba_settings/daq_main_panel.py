from libraries.gen_class import Class

daq_main_panel_settings = Class()

daq_main_panel_settings.daq_main_panel_build_dict = {
                                                     '_common_settings': {'font': 'huge'},
                                                     '_daq_main_panel_welcome_label': {'text': 'Hello, please select a DAQ type',
                                                                                       'font': 'huge', 'position': (0, 0, 1, 4)},
                                                     '_daq_main_panel_user_move_stepper_pushbutton': {'text': 'Move Stepper', 'function': '_launch_daq', 'position': (1, 0, 1, 1)},
                                                     '_daq_main_panel_single_channel_fts_pushbutton': {'text': 'Single Channel FTS', 'function': '_launch_daq', 'position': (1, 1, 1, 1)},
                                                     '_daq_main_panel_beam_mapper_pushbutton': {'text': 'Beam Mapper', 'function': '_launch_daq', 'position': (1, 2, 1, 1)},
                                                     '_daq_main_panel_pol_efficiency_pushbutton': {'text': 'Pol Efficiency', 'function': '_launch_daq', 'position': (1, 3, 1, 1)},
                                                     '_daq_main_panel_xycollector_pushbutton': {'text': 'XY Collector', 'function': '_launch_daq', 'position': (2, 0, 1, 1)},
                                                     '_daq_main_panel_time_constatn_pushbutton': {'text': 'Time Constant', 'function': '_launch_daq', 'position': (2, 1, 1, 1)},
                                                     '_daq_main_panel_close_pushbutton': {'text': 'Close', 'function': '_close_main', 'position': (3, 0, 1, 4)}
                                                     }

