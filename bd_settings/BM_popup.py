from GuiBuilder.gui_builder import GenericClass

beammap_settings_popup_settings = GenericClass()

beammap_settings_popup_settings.beammap_settings_popup_build_dict = {
                                                                     '_common_settings': {'font ': 'large'},
                                                                     '_beammap_settings_popup_file_path_label': {'position': (0, 0, 1, 1)},
                                                                     '_beammap_settings_popup_run_pushbutton': {'position': (2, 0, 1, 1), 'text': 'Run', 'function': '_plot_beammap'},
                                                                     '_beammap_settings_popup_close_pushbutton': {'position': (3, 0, 1, 1), 'text': 'Close', 'function': '_close_beammap'},
                                                                     }
