import os

class SavingManager():

    def __init__(self, widget, data_folder):
        '''
        '''
        self.data_folder = data_folder
        self.widget = widget


    def auto_save(self):
        '''
        '''
        for x in dir(widget):
            print(x)
        for x in os.listdir(data_folder):
            print(x)
