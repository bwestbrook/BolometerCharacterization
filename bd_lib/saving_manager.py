import os

class SavingManager():

    def __init__(self, widget, data_folder):
        '''
        '''
        self.data_folder = data_folder
        self.widget = widget


    def smgr_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            file_name = '{0}_{1}.txt'.format(self.sample_name_lineedit.text(), str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def smgr_auto_save(self):
        '''
        '''
        for x in dir(widget):
            print(x)
        for x in os.listdir(data_folder):
            print(x)
