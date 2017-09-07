import os
import numpy as np
from copy import copy
from datetime import datetime
from PyQt4 import QtGui
from libraries.gen_class import Class
from gui_library import GuiTemplate


class BoloAnalyzer(GuiTemplate):

    def __init__(self):
        self.analysis_types = ('IV Curves', 'Tc Curves')

    def create_gui(self, analysis_types):
        qt_app = QtGui.QApplication([])
        gui = GuiTemplate(analysis_types)
        exit(qt_app.exec_())

    def run(self, analysis_types):
        self.create_gui(analysis_types)


if __name__ == '__main__':
    ba = BoloAnalyzer()
    ba.run(ba.analysis_types)
