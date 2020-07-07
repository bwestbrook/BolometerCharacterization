from libraries.gen_class import Class

final_plot_settings = Class()

final_plot_settings.final_plot_build_dict = {                '_common_settings': {'font': 'large'},

# CONTROL BUTTONS
                                                             '_final_plot_popup_title_label': {'text': 'Final Plot', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (0, 0, 1, 5)},

                                                             '_final_plot_popup_plot_title_header_label': {'text': 'Plot Title:', 'position': (1, 0, 1, 1)},
                                                             '_final_plot_popup_plot_title_lineedit': {'text': '', 'position': (1, 1, 1, 4)},

                                                             '_final_plot_popup_data_path_pushbutton': {'text': 'Change Data Save Path:', 'function': '_get_parsed_data_save_path',
                                                                                                        'position': (2, 0, 1, 1)},
                                                             '_final_plot_popup_data_path_label': {'text': '', 'font': 'small',  'position': (2, 1, 1, 1)},

                                                             '_final_plot_popup_plot_path_pushbutton': {'text': 'Change Plot Save Path:', 'function': '_get_plotted_data_save_path',
                                                                                                        'position': (2, 2, 1, 1)},
                                                             '_final_plot_popup_plot_path_label': {'text': '', 'font': 'small', 'position': (2, 3, 1, 1)},

                                                             '_final_plot_popup_x_label_header_label': {'text': 'X Label:', 'position': (3, 0, 1, 1)},
                                                             '_final_plot_popup_x_label_lineedit': {'text': '', 'position': (3, 1, 1, 1)},

                                                             '_final_plot_popup_y_label_header_label': {'text': 'Y Label:', 'position': (3, 2, 1, 1)},
                                                             '_final_plot_popup_y_label_lineedit': {'text': '', 'position': (3, 3, 1, 1)},

                                                             '_final_plot_popup_error_bars_checkbox': {'text': 'Add Error Bars', 'position': (3, 4, 1, 1)},

                                                             '_final_plot_popup_subplots_margins_header_label': {'text': 'Subplot Margins (L, R, T, B):', 'position': (4, 0, 1, 1)},

                                                             '_final_plot_popup_subplots_left_margin_lineedit': {'text': '0.12', 'position': (4, 1, 1, 1)},
                                                             '_final_plot_popup_subplots_right_margin_lineedit': {'text': '0.98', 'position': (4, 2, 1, 1)},
                                                             '_final_plot_popup_subplots_top_margin_lineedit': {'text': '0.80', 'position': (4, 3, 1, 1)},
                                                             '_final_plot_popup_subplots_bottom_margin_lineedit': {'text': '0.23', 'position': (4, 4, 1, 1)},

                                                             '_final_plot_popup_x_conversion_header_label': {'text': 'X data Conversion Factor:', 'aligment': 'Right',
                                                                                                             'position': (5, 0, 1, 1)},
                                                             '_final_plot_popup_x_conversion_label': {'text': '', 'position': (5, 1, 1, 1)},

                                                             '_final_plot_popup_y_conversion_header_label': {'text': 'Y data Conversion Factor:', 'aligment': 'Right',
                                                                                                             'position': (5, 2, 1, 1)},
                                                             '_final_plot_popup_y_conversion_label': {'text': '', 'position': (5, 3, 1, 1)},

# Plot Labels 
                                                             '_final_plot_popup_result_label': {'alignment': 'Center', 'position': (6, 0, 1, 6)},
                                                             '_final_plot_popup_fft_label': {'alignment': 'Center', 'position': (7, 6, 1, 6)},


# Contrl Buttons Labels 
                                                             '_final_plot_popup_load_pushbutton': {'text': 'Load', 'function': '_load_plot_data', 'position': (8, 0, 1, 6)},
                                                             '_final_plot_popup_replot_pushbutton': {'text': 'Replot', 'function': '_replot', 'position': (9, 0, 1, 6)},
                                                             '_final_plot_popup_save_pushbutton': {'text': 'Save', 'function': '_save_final_plot', 'position': (10, 0, 1, 6)},
                                                             '_final_plot_popup_close_pushbutton': {'text': 'Close', 'function': '_close_final_plot', 'position': (11, 0, 1, 6)},


}



