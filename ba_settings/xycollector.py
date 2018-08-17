from libraries.gen_class import Class

xycollector_settings = Class()

xycollector_settings.xycollector_build_dict = {
                                                             '_common_settings': {'font': 'large'},
# HARDWARE SETUP 
                                                             '_xycollector_popup_hardware_setup_label': {'text': 'HARDWARE SETUP', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (0, 0, 1, 4)},

                                                             '_xycollector_popup_visa_resource_name_x_header_label': {'text': 'VISA resource name X:', 'position': (1, 0, 1, 1)},
                                                             '_xycollector_popup_visa_resource_name_x_combobox': { 'position': (1, 1, 1, 1)},

                                                             '_xycollector_popup_visa_resource_name_y_header_label': {'text': 'VISA resource name Y:', 'position': (1, 2, 1, 1)},
                                                             '_xycollector_popup_visa_resource_name_y_combobox': { 'position': (1, 3, 1, 1)},



# CONTROL BUTTONS 
                                                             '_xycollector_popup_control_buttons_label': {'text': 'CONTROLS', 'font': 'huge', 'color': 'blue', 'alignment': 'Center', 'position': (16, 0, 1, 4)},

                                                             '_xycollector_popup_start_pushbutton': {'text': 'Start', 'function': '_run_xycollector', 'position': (17, 0, 1, 1)},

                                                             '_xycollector_popup_pause_pushbutton': {'text': 'Pause', 'function': '_dummy', 'position': (17, 1, 1, 1)},

                                                             '_xycollector_popup_close_pushbutton': {'text': 'Close', 'function': '_close_xycollector', 'position': (17, 3, 1, 1)},

                                                             '_xycollector_popup_save_pushbutton': {'text': 'Save', 'function': '_final_plot', 'position': (18, 5, 1, 1)},

# VISUAL DATA MONITORING
                                                             '_xycollector_popup_data_monitor_label': {'text': 'VISUAL DATA MONITOR', 'font': 'huge', 'color': 'blue',
                                                                                                              'alignment': 'Center', 'position': (0, 7, 1, 4)},
                                                            
                                                             '_xycollector_popup_xdata_label': {'alignment': 'Center', 'width': 700, 'position': (1, 7, 6, 6)},

                                                             '_xycollector_popup_ydata_label': {'alignment': 'Center', 'position': (7, 7, 6, 6)},

                                                             '_xycollector_popup_xydata_label': {'alignment': 'Center', 'position': (13, 7, 6, 6)},

}



xycollector_settings.xycollector_combobox_entry_dict = {
                                                  
                                                   '_xycollector_popup_visa_resource_name_x_combobox': ['COM1', 'COM2', 'COM3', 'COM4','GPIB0:20'],
                                                   '_xycollector_popup_visa_resource_name_y_combobox': ['COM1', 'COM2', 'COM3', 'COM4','GPIB0:22'],    


                                                   }




