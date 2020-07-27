from libraries.gen_class import Class

ftscurve_settings_popup_settings = Class()
ftscurve_settings_popup_settings.simulated_bands = ['90', '150', '220', '270']

ftscurve_settings_popup_settings.ftscurve_popup_build_dict = {
                                                              '_common_settings': {'font': 'med'},
                                                              '_ftscurve_settings_popup_close_pushbutton': {'text': 'Close', 'function': '_close_fts',
                                                                                                            'width': 200, 'height': 150, 'position': (0, 0, 1, 2)},
                                                              '_ftscurve_settings_popup_run_pushbutton': {'text': 'Run', 'function': '_run_analysis',
                                                                                                          'width': 200, 'height': 150, 'position': (0, 3, 1, 2)},
                                                              '_ftscurve_settings_popup_selected_file_label': {'text': 'Selected File', 'position': (2, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_sample_name_label': {'text': 'Sample Name', 'position': (3, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_plot_title_label': {'text': 'Plot Title', 'position': (4, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_plot_label_label': {'text': 'Plot Label', 'position': (5, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_normalize_label': {'text': 'Normalize?', 'position': (6, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_divide_bs_label': {'text': 'Divide BS:', 'position': (7, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_divide_mmf_label': {'text': 'Divide MMF:', 'position': (8, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_add_atm_model_label': {'text': 'Add ATM:', 'position': (9, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_add_co_lines_label': {'text': 'Add CO Lines:', 'position': (10, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_simulation_band_label': {'text': 'Add Sim:', 'position': (11, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_step_size_point_label': {'text': 'Step Size (nm)', 'position': (13, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_steps_per_point_label': {'text': 'Step Interval:', 'position': (14, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_color_label': {'text': 'Color', 'position': (15, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_xlim_clip_label': {'text': 'Data Clip [low/high]', 'position': (16, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_xlim_plot_label': {'text': 'Plot Clip [low/high]', 'position': (17, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_smoothing_factor_label': {'text': 'Smoothing:', 'position': (18, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_interferogram_data_select_label': {'text': 'Int Data Select:', 'position': (19, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_apodization_label': {'text': 'Apodization:', 'position': (20, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_plot_interferogram_label': {'text': 'Plot Interferogram?', 'position': (21, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_add_loacl_fft_label': {'text': 'Plot Local FFT?', 'position': (22, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_normalize_post_clip_label': {'text': 'Normalize Post Clip', 'position': (23, 0, 1, 1)},
                                                              '_ftscurve_settings_popup_divide_ffts_label': {'text': 'Divide FFTs?', 'position': (24, 0, 1, 1)},
                                                              }
