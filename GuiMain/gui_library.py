import sys
import os
import subprocess
import shutil
import time
import numpy as np
import datetime
import pylab as pl
from PyPDF2 import PdfFileMerger
from pprint import pprint
from copy import copy
from PyQt4 import QtCore, QtGui
from libraries.gen_class import Class

# Globals for use between classes
timing = False
open_camera_window = True
run_timer = True
photo_taken = False
pysketch.pen_size = 1
fgcolor = QtCore.Qt.black
bgcolor = QtCore.Qt.white


class GuiTemplate(QtGui.QWidget):

    def __init__(self, all_tools):
        super(GuiTemplate, self).__init__()
        self.credentials_file = './resources/google_api_credentials.dat'
        self.google_drive = GoogleDrive()
        self.__apply_settings__(settings)
        if not os.path.exists(self.credentials_file):
            print self.google_drive.authorize_url
            self._authorize_google_drive(self.google_drive.authorize_url)
        else:
            # Initialize
            self.all_tools = all_tools
            self.tools = all_tools.tools_list
            # Google Stuff
            self.credentials = Storage(self.credentials_file).get()
            self.google_drive.create_drive(self.credentials)
            self.pb2_folder_on_drive_id = self.google_drive.get_top_level_id()
            self._get_all_files_and_folders_on_drive()
            self.grid = QtGui.QGridLayout()
            self.grid.setVerticalSpacing(0)
            self.setLayout(self.grid)
            self.today = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
            self.palette_gray = self.palette()
            self.palette_gray.setColor(self.backgroundRole(), QtCore.Qt.gray)
            self.setPalette(self.palette_gray)
            self.title = 'UC BERKELEY EXPERIMENTAL COSMOLOGY FABRICATION TRACKER'
            # Populate and Start GUI
            for unique_panel_name, placement_dict in self.panels.iteritems():
                 position = placement_dict['position']
                 row = position[0]
                 stretch_factor = placement_dict['stretch_factor']
                 self.grid.setRowStretch(row, stretch_factor)
                 widget_settings = {'layout': 'QGridLayout', 'position': position}
                 if 'main_panel' in unique_panel_name:
                     widget_settings.update({'height': settings.main_panel_height})
                 self._create_and_place_widget(unique_panel_name, **widget_settings)
            self.grid.setRowMinimumHeight(2, 300)
            self.grid.setRowStretch(2, 2000)
            self.saved_state_label_unique_name = '_buttons_panel_saved_state_label'
            self.upload_state_label_unique_name = '_buttons_panel_upload_state_label'
            self.populate_gui()
            self.showMaximized()
        #query = 'fullText contains "_image_"'
        #queried_files = self.google_drive.query_file_name(query, isfull_query=True)
        #print [x['title'] for x in queried_files]
