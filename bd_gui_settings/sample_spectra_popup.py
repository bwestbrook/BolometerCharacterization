from GuiBuilder.gui_builder import GenericClass

sample_spectra_settings_popup_settings = GenericClass()
sample_spectra_settings_popup_settings.simulated_bands = ['90', '150', '220', '270']

sample_spectra_settings_popup_settings.sample_spectra_settings_popup_build_dict = {
                                                                                   '_common_settings': {'font': 'med'},
                                                                                   '_sample_spectra_settings_popup_load_open_pushbutton': {'text': 'Load Open Data', 'function': '_load_sample_data', 'position': (0, 0, 1, 1)},
                                                                                   '_sample_spectra_settings_popup_loaded_open_files_label': {'position': (1, 0, 1, 1)},
                                                                                   '_sample_spectra_settings_popup_load_sample_in_pushbutton': {'text': 'Load Sample in Data', 'function': '_load_sample_data', 'position': (0, 1, 1, 1)},
                                                                                   '_sample_spectra_settings_popup_loaded_sample_in_files_label': {'position': (1, 1, 1, 1)},
                                                                                   '_sample_spectra_settings_popup_average_then_divide_checkbox': {'text': 'Average Then Divide', 'position': (2, 0, 1, 1)},
                                                                                   '_sample_spectra_settings_popup_divide_then_average_checkbox': {'text': 'Divide Then Average', 'position': (2, 1, 1, 1)},
                                                                                   '_sample_spectra_settings_popup_create_average_spectra_pushbutton': {'text': 'Create Average Specra',
                                                                                                                                                        'function': '_create_average_spectra', 'position': (3, 0, 1, 2)},
                                                                                   '_sample_spectra_settings_popup_close_pushbutton': {'text': 'Close', 'function': '_close_sample_spectra', 'position': (10, 0, 1, 2)},
                                                                                  }
