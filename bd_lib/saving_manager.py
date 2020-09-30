import os

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
