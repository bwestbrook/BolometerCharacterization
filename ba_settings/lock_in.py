from libraries.gen_class import Class

lock_in_settings = Class()

lock_in_settings.lock_in_popup_build_dict = {
                                             '_common_settings': {'font': 'large'},
                                             '_lock_in_popup_header_label': {'text': 'Configure the lock-in remotely', 'alignment': 'Center', 'position': (0, 0, 1, 2)},
                                             # Sensitivity
                                             '_lock_in_popup_lock_in_sensitivity_range_up_pushbutton': {'text': 'Lock-in Sensitivity Range Up', 'function': '_change_lock_in_sensitivity_range', 'position': (1, 0, 1, 1)},
                                             '_lock_in_popup_lock_in_sensitivity_range_down_pushbutton': {'text': 'Lock-in Sensitivity Range Down', 'function': '_change_lock_in_sensitivity_range', 'position': (1, 1, 1, 1)},
                                             '_lock_in_popup_lock_in_sensitivity_range_combobox': {'function': '_change_lock_in_sensitivity_range', 'position': (1, 2, 1, 1)},
                                             # Time Constant
                                             '_lock_in_popup_lock_in_time_constant_up_pushbutton': {'text': 'Lock-in Time Constant Up', 'function': '_change_lock_in_time_constant', 'position': (2, 0, 1, 1)},
                                             '_lock_in_popup_lock_in_time_constant_down_pushbutton': {'text': 'Lock-in Time Constant Down', 'function': '_change_lock_in_time_constant', 'position': (2, 1, 1, 1)},
                                             '_lock_in_popup_lock_in_time_constant_combobox': {'function': '_change_lock_in_time_constant', 'position': (2, 2, 1, 1)},
                                             '_lock_in_popup_zero_lock_in_phase_pushbutton': {'text': 'Zero Lock-in Phase', 'function': '_zero_lock_in_phase', 'position': (3, 0, 1, 1)},
                                             # General Control
                                             '_lock_in_popup_close_lock_in_pushbutton': {'text': 'Close Lock-in', 'function': '_close_lock_in', 'position': (8, 0, 1, 4)},
                                             }

lock_in_settings.lock_in_combobox_entry_dict = {
                                                '_lock_in_popup_lock_in_sensitivity_range_combobox': [str(x) for x in range(27)],
                                                '_lock_in_popup_lock_in_time_constant_combobox': [str(x) for x in range(20)],
                                                }
