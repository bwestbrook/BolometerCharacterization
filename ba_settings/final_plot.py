from libraries.gen_class import Class

final_plot_settings = Class()

final_plot_settings.final_plot_build_dict = {                '_common_settings': {'font': 'large'},

# CONTROL BUTTONS
                                                             '_final_plot_popup_plot_title_header_label': {'text': 'Plot Title:', 'position': (1, 0, 1, 1)},
                                                             '_final_plot_popup_plot_title_lineedit': {'text': '', 'position': (1, 1, 1, 1)},
                                                             '_final_plot_popup_data_label_header_label': {'text': 'Data Label:', 'position': (1, 2, 1, 1)},
                                                             '_final_plot_popup_data_label_lineedit': {'text': '', 'position': (1, 3, 1, 1)},
                                                             '_final_plot_popup_title_label': {'text': 'Final Plot', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (0, 0, 1, 4)},


                                                             '_final_plot_popup_replot_pushbutton': {'text': 'Replot', 'function': '_replot', 'position': (8, 0, 1, 2)},

                                                             '_final_plot_popup_save_pushbutton': {'text': 'Save', 'function': '_save_final_plot', 'position': (9, 0, 1, 2)},

                                                             '_final_plot_popup_close_pushbutton': {'text': 'Close', 'function': '_close_final_plot', 'position': (10, 0, 1, 2)},

# VISUAL DATA MONITORING

                                                             '_final_plot_popup_result_label': {'alignment': 'Center', 'position': (2, 0, 6, 6)},
                                                             '_final_plot_popup_fft_label': {'alignment': 'Center', 'position': (2, 6, 6, 6)},                                                             

}



