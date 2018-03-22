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
from ba_settings.all_settings import settings
from RT_Curves.plot_rt_curves import RTCurve
from IV_Curves.plot_iv_curves import IVCurve
from FTS_Curves.plot_fts_curves import FTSCurve
from POL_Curves.plot_pol_curves import POLCurve
from Stepper_Motor.stepper import Stepper


class GuiTemplate(QtGui.QWidget):

    def __init__(self):
        super(GuiTemplate, self).__init__()
        self.grid = QtGui.QGridLayout()
        self.grid.setVerticalSpacing(0)
        self.setLayout(self.grid)
        self.__apply_settings__(settings)
        self._create_main_window('daq_main_panel_widget')
        self.daq_main_panel_widget.showMaximized()
        self.data_folder = './data'
        self.selected_files = []
        self.current_stepper_position = 100
        self.stepper = Stepper()

    def __apply_settings__(self, settings):
        for setting in dir(settings):
            if '__' not in setting:
                setattr(self, setting, getattr(settings, setting))

    def _create_main_window(self, name):
        self._create_popup_window(name)
        self._build_panel(settings.daq_main_panel_build_dict)
        self._add_daq_types_to_combobox()


    def _close_main(self):
        self.daq_main_panel_widget.close()
        sys.exit()

    #################################################
    #################################################
    # DAQ TYP SPECFIC CODES 
    #################################################
    #################################################

    def _add_daq_types_to_combobox(self):
        for daq_function in settings.daq_functions:
            daq_combo_box_string = ' '.join(daq_function.split('_'))[1:].title()
            entry = QtCore.QString(daq_combo_box_string)
            getattr(self, '_daq_main_panel_daq_select_combobox').addItem(entry)
            print daq_combo_box_string, daq_function

    def _launch_daq(self):
        print 'hello'
        function_name = '_'.join(str(' ' + self.sender().currentText()).split(' ')).lower()
        getattr(self, function_name)()

    #################################################
    # USER MOVE STEPPER
    #################################################

    def _close_user_move_stepper(self):
        self.user_move_stepper_popup.close()

    def _user_move_stepper(self):
        print 'code for moving stepper'
        if not hasattr(self, 'user_move_stepper_popup'):
            self._create_popup_window('user_move_stepper_popup')
        else:
            self._initialize_panel('user_move_stepper_popup')
        self._build_panel(settings.user_move_stepper_build_dict)
        self._add_comports_to_user_move_stepper()
        self._update_stepper_position()
        print self.stepper.connect_to_com_port('COM1')
        self.user_move_stepper_popup.show()
        self.user_move_stepper_popup.setWindowTitle('User Move Stepper')

    def _add_comports_to_user_move_stepper(self):
        for com_port in settings.com_ports:
            com_port_entry = QtCore.QString(com_port)
            getattr(self, '_user_move_stepper_popup_current_com_port_combobox').addItem(com_port_entry)

    def _connect_to_com_port(self):
        com_port = self._get_com_port()
        self.stepper.connect_to_com_port(com_port)
        #### SOME CODE HERE TO CONNECT TO BACKEND ####
        connected_to_com_port = self.stepper.connect_to_com_port(com_port)
        print connected_to_com_port
        old_stepper_position = self._get_stepper_position()
        move_to_position = getattr(self, '_user_move_stepper_popup_lineedit').setText(str(old_stepper_position))
        self._update_stepper_position()

    def _move_stepper(self):
        move_to_position = int(str(getattr(self, '_user_move_stepper_popup_lineedit').text()))
        old_stepper_position = self._get_stepper_position()
        com_port = self._get_com_port()
        print 'Code would physically get this to move {0} from {1} to {2}'.format(com_port, old_stepper_position,
                                                                                  move_to_position)
        self.stepper.stepper_position_dict[com_port] = move_to_position
        self._update_stepper_position()

    def _reset_stepper_zero(self):
        com_port = self._get_com_port()
        self.stepper.stepper_position_dict[com_port] = 0
        self._update_stepper_position()
        getattr(self, '_user_move_stepper_popup_lineedit').setText(str(0))

    def _get_stepper_position(self):
        com_port = self._get_com_port()
        stepper_position = self.stepper.stepper_position_dict[com_port]
        return stepper_position

    def _update_stepper_position(self):
        com_port = self._get_com_port()
        stepper_position = self.stepper.stepper_position_dict[com_port]
        header_str = '{0} Current Position:'.format(com_port)
        getattr(self, '_user_move_stepper_popup_current_position_header_label').setText(header_str)
        getattr(self, '_user_move_stepper_popup_current_position_label').setText(str(stepper_position))

    def _get_com_port(self):
        com_port = str(getattr(self, '_user_move_stepper_popup_current_com_port_combobox').currentText())
        return com_port

    #################################################
    # SINGLE CHANNEL FTS BILLS 
    #################################################

    def _single_channel_fts(self):
        print 'code for running fts'

    #################################################
    # WIDGET GENERATORS AND FUNCTIONS
    #################################################

    def _initialize_panel(self, panel=None):
        panel = getattr(self, panel)
        for index in reversed(range(panel.layout().count())):
            widget = panel.layout().itemAt(index).widget()
            widget.setParent(None)

    def _unpack_widget_function(self, function_text):
        if '.' in function_text:
            if len(function_text.split('.')) == 2:
                base_function, attribute_function = function_text.split('.')
                base_function = getattr(self, base_function)
                widget_function = getattr(base_function, attribute_function)
        else:
            widget_function = getattr(self, function_text)
        return widget_function

    def _build_panel(self, build_dict, parent=None):
        for unique_widget_name, widget_settings in build_dict.iteritems():
            widget_settings_copy = copy(build_dict['_common_settings'])
            if unique_widget_name != '_common_settings':
                widget_settings_copy.update(widget_settings)
                widget_settings_copy.update({'parent': parent})
                for widget_param, widget_param_value in widget_settings.iteritems():
                    if 'function' == widget_param:
                        widget_function = self._unpack_widget_function(widget_param_value)
                        widget_settings_copy.update({'function':  widget_function})

                self._create_and_place_widget(unique_widget_name, **widget_settings_copy)

    def _create_popup_window(self, name):
        popup_window = QtGui.QWidget()
        popup_window.setGeometry(100, 100, 400, 200)
        popup_window.setLayout(QtGui.QGridLayout())
        setattr(self, name, popup_window)

    def _create_and_place_widget(self,
                                 unique_widget_name,
                                 parent=None,
                                 function=None,
                                 text=None,
                                 font=None,
                                 color=None,
                                 width=None,
                                 height=None,
                                 layout=None,
                                 url=None,
                                 orientation=None,
                                 tick_interval=None,
                                 tick_range=None,
                                 check_state=None,
                                 word_wrap=None,
                                 pixmap=None,
                                 alignment=None,
                                 keep_aspect_ratio=True,
                                 image_scale=(100, 100),
                                 widget_alignment=None,
                                 position=None,
                                 place_widget=True,
                                 **widget_setttings):
        widget_type = self.widget_to_object_dict[unique_widget_name.split('_')[-1]]
        if orientation is not None and widget_type == 'QSlider':
            widget = QtGui.QSlider(getattr(QtCore.Qt, orientation))
            widget.setTracking(True)
        else:
            if parent is not None:
                widget = getattr(QtGui, widget_type)(parent)
            else:
                widget = getattr(QtGui, widget_type)()
        if function is not None:
            if widget_type == 'QSlider':
                widget.valueChanged.connect(function)
            elif widget_type in ('QPushButton', 'QCheckBox'):
                widget.clicked.connect(function)
                #button_icon = QtGui.QIcon()
                #button_icon.addFile('./resources/Bolo_Chip.jpg')
                #widget.setIcon(button_icon)
                #widget.setIconSize(QtCore.QSize(50, 50))
            elif widget_type in ('QLineEdit', 'QTextEdit'):
                widget.textChanged.connect(function)
            elif widget_type in ('QComboBox',):
                widget.activated.connect(function)
        if text is not None:
            if url is not None:
                text = '<a href=\"{0}\">{1}</a>'.format(url, text)
                widget.setOpenExternalLinks(True)
            widget.setText(text)
        if font is not None:
            widget.setFont(getattr(self, '{0}_font'.format(font)))
        if width is not None:
            widget.setFixedWidth(width)
        if height is not None:
            widget.setFixedHeight(height)
        if word_wrap is not None:
            widget.setWordWrap(word_wrap)
        if color is not None:
            widget.setStyleSheet('%s {color: %s}' % (widget_type, color))
        if pixmap is not None:
            image = QtGui.QPixmap(pixmap)
            if keep_aspect_ratio:
                image = image.scaled(image_scale[0], image_scale[1], QtCore.Qt.KeepAspectRatio)
            else:
                image = image.scaled(image_scale[0], image_scale[1])
            widget.setPixmap(image)
        if alignment is not None:
            qt_alignment = getattr(QtCore.Qt, 'Align{0}'.format(alignment))
            widget.setAlignment(qt_alignment)
        if layout is not None:
            widget.setLayout(getattr(QtGui, layout)())
        if tick_interval is not None:
            widget.setTickInterval(1)
        if tick_range is not None:
            widget.setRange(tick_range[0], tick_range[1])
        if check_state is not None:
            widget.setCheckState(check_state)
        if place_widget:
            row, col, row_span, col_span = position[0], position[1], position[2], position[3]
            if 'widget' in unique_widget_name:
                if widget_alignment is not None:
                    self.grid.addWidget(widget, row, col, row_span, col_span,
                                        getattr(QtCore.Qt, widget_alignment))
                else:
                    self.grid.addWidget(widget, row, col, row_span, col_span)
            else:
                if 'panel' in unique_widget_name:
                    panel = '{0}_{1}'.format(unique_widget_name.split('_panel')[0][1:], 'panel_widget')
                if 'popup' in unique_widget_name:
                    panel = '{0}_{1}'.format(unique_widget_name.split('_popup')[0][1:], 'popup')
                if 'panel' in unique_widget_name and 'popup' in unique_widget_name and widget_type != 'QWidget':
                    panel = '_{0}_{1}'.format(unique_widget_name.split('_panel')[0][1:], 'panel')
                if widget_alignment is not None:
                    getattr(self, panel).layout().addWidget(widget, row, col, row_span, col_span,
                                                            getattr(QtCore.Qt, widget_alignment))
                else:
                    getattr(self, panel).layout().addWidget(widget, row, col, row_span, col_span)
        else:
            widget.close()
        setattr(self, unique_widget_name, widget)
        widget.setWhatsThis(unique_widget_name)
        return widget
