from libraries.gen_class import Class

daq_main_panel_settings = Class()

daq_main_panel_settings.daq_main_panel_build_dict = {
                                                     '_common_settings': {'font': 'huge'},
                                                     '_daq_main_panel_welcome_label': {'text': 'Hello, please select a DAQ type', 'alignment': 'Center',
                                                                                       'font': 'huge', 'position': (0, 0, 1, 4), 'color': 'Blue'},
                                                     # Options 
                                                     '_daq_main_panel_user_move_stepper_pushbutton': {'text': 'User Move Stepper', 'function': '_launch_daq', 'position': (1, 0, 1, 1)},
                                                     '_daq_main_panel_single_channel_fts_pushbutton': {'text': 'Single Channel FTS', 'function': '_launch_daq', 'position': (1, 1, 1, 1)},
                                                     '_daq_main_panel_beam_mapper_pushbutton': {'text': 'Beam Mapper', 'function': '_launch_daq', 'position': (1, 2, 1, 1)},
                                                     '_daq_main_panel_pol_efficiency_pushbutton': {'text': 'Pol Efficiency', 'function': '_launch_daq', 'position': (1, 3, 1, 1)},
                                                     '_daq_main_panel_xycollector_pushbutton': {'text': 'XY Collector', 'function': '_launch_daq', 'position': (2, 0, 1, 1)},
                                                     '_daq_main_panel_time_constant_pushbutton': {'text': 'Time Constant', 'function': '_launch_daq', 'position': (2, 1, 1, 1)},
                                                     '_daq_main_panel_multimeter_pushbutton': {'text': 'Multimeter', 'function': '_launch_daq', 'position': (2, 2, 1, 1)},
                                                     '_daq_main_panel_cosmic_rays_pushbutton': {'text': 'Cosmic Rays', 'function': '_launch_daq', 'position': (2, 3, 1, 1)},
                                                     '_daq_main_panel_fridge_cycle_pushbutton': {'text': 'Fridge Cycle', 'function': '_launch_daq', 'position': (3, 0, 1, 1)},
                                                     '_daq_main_panel_sr830_dsp_pushbutton': {'text': 'SR830 DSP', 'function': '_launch_daq', 'position': (3, 1, 1, 1)},
                                                     '_daq_main_panel_e3634a_pushbutton': {'text': 'E3634A', 'function': '_launch_daq', 'position': (3, 2, 1, 1)},
                                                     '_daq_main_panel_data_analyzer_pushbutton': {'text': 'Data Analyzer', 'function': '_launch_daq', 'position': (3, 3, 1, 1)},
                                                     # Sample Dict
                                                     '_daq_main_panel_set_sample_dict_label': {'text': 'Enter the samples names for the six channels (Optional)', 'alignment': 'Center',
                                                                                               'font': 'huge', 'position': (4, 0, 1, 4), 'color': 'Blue'},
                                                     '_daq_main_panel_set_sample_1_header_label': {'text': 'Ch 1', 'position': (5, 0, 1, 1)},
                                                     '_daq_main_panel_set_sample_1_lineedit': {'position': (5, 1, 1, 1)},
                                                     '_daq_main_panel_set_sample_2_header_label': {'text': 'Ch 2', 'position': (5, 2, 1, 1)},
                                                     '_daq_main_panel_set_sample_2_lineedit': {'position': (5, 3, 1, 1)},
                                                     '_daq_main_panel_set_sample_3_header_label': {'text': 'Ch 3', 'position': (6, 0, 1, 1)},
                                                     '_daq_main_panel_set_sample_3_lineedit': {'position': (6, 1, 1, 1)},
                                                     '_daq_main_panel_set_sample_4_header_label': {'text': 'Ch 4', 'position': (6, 2, 1, 1)},
                                                     '_daq_main_panel_set_sample_4_lineedit': {'position': (6, 3, 1, 1)},
                                                     '_daq_main_panel_set_sample_5_header_label': {'text': 'Ch 5', 'position': (7, 0, 1, 1)},
                                                     '_daq_main_panel_set_sample_5_lineedit': {'position': (7, 1, 1, 1)},
                                                     '_daq_main_panel_set_sample_6_header_label': {'text': 'Ch 6', 'position': (7, 2, 1, 1)},
                                                     '_daq_main_panel_set_sample_6_lineedit': {'position': (7, 3, 1, 1)},
                                                     '_daq_main_panel_pump_header_label': {'text': 'Pump Used:', 'position': (8, 0, 1, 1)},
                                                     '_daq_main_panel_pump_lineedit': {'position': (8, 1, 1, 1)},
                                                     '_daq_main_panel_pump_oil_level_header_label': {'text': 'Oil Level:', 'position': (8, 2, 1, 1)},
                                                     '_daq_main_panel_pump_oil_level_lineedit': {'position': (8, 3, 1, 1)},
                                                     '_daq_main_panel_set_sample_dict_path_label': {'text': 'No Sample Dict Set (Optional)', 'alignment': 'Center',
                                                                                                    'position': (9, 0, 1, 4)},
                                                     '_daq_main_panel_create_sample_dict_path_pushbutton': {'text': 'Create Sample Dict Path', 'function': '_create_sample_dict_path', 'position': (10, 0, 1, 4)},
                                                     '_daq_main_panel_set_sample_dict_path_pushbutton': {'text': 'Load Sample Dict Path', 'function': '_set_sample_dict_path', 'position': (11, 0, 1, 4)},
                                                     '_daq_main_panel_close_pushbutton': {'text': 'Close', 'function': '_close_main', 'position': (12, 0, 1, 4)}
                                                     }

