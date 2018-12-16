import os
import numpy as np
from copy import copy
from datetime import datetime
from PyQt4 import QtGui
#from gen_class import Class
from libraries.gen_class import Class
from daq_gui_library import GuiTemplate


class BoloDAQ(GuiTemplate):

    def __init__(self):
        self.hello = 'hello'

    def create_gui(self):
        qt_app = QtGui.QApplication([])
        screen_resolution = qt_app.desktop().screenGeometry()
        gui = GuiTemplate(screen_resolution)
        exit(qt_app.exec_())

    def run(self):
        self.create_gui()


if __name__ == '__main__':
    bdaq = BoloDAQ()
    bdaq.run()
