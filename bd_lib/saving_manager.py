import os
import datetime
from pprint import pprint

class SavingManager():

    def __init__(self, widget, data_folder, save_function, data_type):
        '''
        '''
        self.data_folder = data_folder
        self.widget = widget
        self.save_function = save_function
        self.data_type = data_type

    def smgr_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            file_name = '{0}_Scan_{1}.txt'.format(self.data_type, str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def smgr_auto_save(self):
        '''
        '''
        save_path = self.smgr_index_file_name()
        self.save_function(save_path)
        self.smgr_auto_log(save_path)

    def smgr_auto_log(self, save_path):
        '''
        '''
        now_str = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M:%S')
        new_dict = {'save_path': save_path, 't_finish': now_str}
        for dict_item, dict_value in self.widget.__dict__.items():
            if dict_item in ('sample_rate_x', 'int_time_x', 'sample_rate_x', 'int_time_y'):
                new_dict[dict_item] = dict_value
            elif dict_item.endswith('label'):
                new_dict[dict_item] = dict_value.text()
            elif dict_item.endswith('lineedit'):
                new_dict[dict_item] = dict_value.text()
            elif dict_item.endswith('combobox'):
                new_dict[dict_item] = dict_value.currentText()
            elif dict_item == 'x_data':
                new_dict['n_samples'] = len(dict_value)
            else:
                print(dict_item)

        pprint(new_dict)



