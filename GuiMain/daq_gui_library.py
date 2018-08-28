import sys
import os
import subprocess
import shutil
import time
import numpy as np
import datetime
import pylab as pl
import matplotlib.pyplot as plt
import time
import threading
from Tkinter import *
from PyPDF2 import PdfFileMerger
from pprint import pprint
from copy import copy
from PyQt4 import QtCore, QtGui
from libraries.gen_class import Class
from ba_settings.all_settings import settings
from RT_Curves.plot_rt_curves import RTCurve
from IV_Curves.plot_iv_curves import IVCurve
from FTS_Curves.plot_fts_curves import FTSCurve
from FTS_Curves.numerical_processing import Fourier
from POL_Curves.plot_pol_curves import POLCurve
from FTS_DAQ.fts_daq import FTSDAQ
from BeamMapping.beam_map_daq import BeamMapDAQ
from Motor_Driver.stepper_motor import stepper_motor
from FTS_DAQ.analyzeFTS import FTSanalyzer
#from DAQ.daq import DAQ
from realDAQ.daq import DAQ


#Global variables
continue_run = True
root = Tk()

class GuiTemplate(QtGui.QWidget):


    def __init__(self):
        super(GuiTemplate, self).__init__()
        self.grid = QtGui.QGridLayout()
        self.grid.setVerticalSpacing(0)
        self.setLayout(self.grid)
        self.__apply_settings__(settings)
        self._create_main_window('daq_main_panel_widget')
        self.data_folder = './data'
        self.selected_files = []
        self.current_stepper_position = 100
        self.daq_main_panel_widget.show()
        self.daq = DAQ()
        self.user_desktop_path = os.path.expanduser('~')
        self.fts_analyzer = FTSanalyzer()
        self.fts_daq = FTSDAQ()
        self.real_daq = DAQ()

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

    def _dummy(self):
        print 'Dummy Function'

    def _add_daq_types_to_combobox(self):
        for daq_function in settings.daq_functions:
            daq_combo_box_string = ' '.join(daq_function.split('_'))[1:].title()
            entry = QtCore.QString(daq_combo_box_string)
            getattr(self, '_daq_main_panel_daq_select_combobox').addItem(entry)

    def _launch_daq(self):
        function_name = '_'.join(str(' ' + self.sender().currentText()).split(' ')).lower()
        getattr(self, function_name)()

    def populate_combobox(self, unique_combobox_name, entries):
        for entry_str in entries:
            entry = QtCore.QString(entry_str)
            getattr(self, unique_combobox_name).addItem(entry)

    def _get_com_port(self, combobox):
        com_port = str(getattr(self, combobox).currentText())
        return com_port


    def _get_all_scan_params(self, popup=None):
        if popup is None:
            popup = str(self.sender().whatsThis()).split('_popup')[0]

        function = '_get_all{0}_scan_params'.format(popup)
        if hasattr(self, function):
            return getattr(self, function)()

    def _connect_to_com_port(self, beammapper=None,single_channel_fts=None):
        combobox = str(self.sender().whatsThis())
        if combobox == '_daq_main_panel_daq_select_combobox':
            popup = str(self.sender().currentText())
	    if popup == 'Pol Efficiency':
                com_port = 'COM6'
                connection = '_pol_efficiency_popup_successful_connection_header_label'
	    elif popup == 'Beam Mapper':
                if beammapper == 1:
	            com_port = 'COM6'
		    connection = '_beam_mapper_popup_x_successful_connection_header_label'
		    popup_combobox = '_beam_mapper_popup_x_current_com_port_combobox'
                    getattr(self, popup_combobox).setCurrentIndex(0)
		elif beammapper == 2:
		    com_port = 'COM2'
		    connection = '_beam_mapper_popup_y_successful_connection_header_label'
		    popup_combobox = '_beam_mapper_popup_y_current_com_port_combobox'
                    getattr(self, popup_combobox).setCurrentIndex(1)
	    elif popup == 'Single Channel Fts':
                 if single_channel_fts == 1:
	            com_port = 'COM6'
		    connection = '_single_channel_fts_popup_successful_connection_header_label'
		    popup_combobox = '_single_channel_fts_popup_current_com_port_combobox'
                    getattr(self, popup_combobox).setCurrentIndex(0)
		 elif single_channel_fts == 2:
		    com_port = 'COM2'
		    connection = '_single_channel_fts_popup_grid_successful_connection_header_label'
		    popup_combobox = '_single_channel_fts_popup_grid_current_com_port_combobox'
	    elif popup == 'User Move Stepper':
	        com_port = 'COM6'
	        connection = '_user_move_stepper_popup_successful_connection_header_label'
	else:
       	    com_port = self._get_com_port(combobox=combobox)
            connection = combobox.replace('current_com_port_combobox','successful_connection_header_label')

#	port_number = int(com_port.strip('COM')) - 1
#	init_string = '/dev/ttyUSB{0}'.format(port_number)
        if com_port not in ['COM1','COM2','COM3']:
            if not hasattr(self, 'sm_{0}'.format(com_port)):
	        setattr(self, 'sm_{0}'.format(com_port), stepper_motor(com_port))
	        current_string = getattr(self, 'sm_{0}'.format(com_port)).get_motor_current().strip('CC=')
                position_string = getattr(self, 'sm_{0}'.format(com_port)).get_position().strip('SP=')
                velocity_string = getattr(self, 'sm_{0}'.format(com_port)).get_velocity().strip('VE=')
            else:
                current_string, position_string,velocity_string = '0','0','0'
        else:
            current_string, position_string,velocity_string = '0','0','0'
            
        getattr(self,connection).setText('Successful Connection to '+ com_port +'!' )
        return current_string, position_string, velocity_string

    def _draw_time_stream(self,data_time_stream, min_, max_, label,integration_time=1000):
         fig = pl.figure(figsize=(3,1.5))
         ax = fig.add_subplot(111)
         yticks = np.linspace(min_,max_,5)
         yticks = [round(x,2) for x in yticks]
         ax.set_yticks(yticks)
         ax.set_yticklabels(yticks,fontsize = 6)
         num = len(data_time_stream)
         time = np.linspace(0,integration_time,num)
         xticks = np.linspace(0,integration_time,5)
#         xticks = [round(s,2) for s in xticks]
         ax.set_xticks(xticks)
         ax.set_xticklabels(xticks,fontsize = 6)
         

         fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
         ax.plot(time,data_time_stream)
         ax.set_title('Timestream')
         ax.set_xlabel('Integration time(ms)')
         ax.set_ylabel('Amplitude')
         fig.savefig('temp_files/temp_ts.png')
         pl.close('all')
         image = QtGui.QPixmap('temp_files/temp_ts.png')
         image = image.scaled(600, 300)
         getattr(self, label).setPixmap(image)


    def _final_plot(self):
        current =  str(self.sender().whatsThis())
        self.is_fft = False
        self.is_beam = False
        self.is_iv = False
        if not hasattr(self, 'final_plot_popup'):
            self._create_popup_window('final_plot_popup')
        else:
            self._initialize_panel('final_plot_popup')
        self._build_panel(settings.final_plot_build_dict)
        self.final_plot_popup.showMaximized()
        self.final_plot_popup.setWindowTitle('Result')
        if current == '_beam_mapper_popup_save_pushbutton':
            title = 'Beam Mapper'
            self.is_beam = True
            self._draw_beammaper_final()
        elif current == '_xycollector_popup_save_pushbutton':
            title = 'IV Curve'
            self.is_iv = True
            self._draw_final_plot(self.xdata,self.ydata,title = title)            
        else:
            xdata = self.xdata
            ydata = self.ydata
            stds = self.stds
        if current == '_pol_efficiency_popup_save_pushbutton':
            title = 'Pol Efficiency'
            self._draw_final_plot(xdata,ydata,stds=stds,title=title)
        elif current == '_single_channel_fts_popup_save_pushbutton':
            title = 'Single Channel FTS'
            self.is_fft = True
            self.fts_analyzer.plotCompleteFT(self.posFreqArray,self.FTArrayPosFreq)
            image = QtGui.QPixmap('temp_files/temp_fft.png')
            image = image.scaled(600, 300)
            getattr(self, '_final_plot_popup_fft_label').setPixmap(image)
            self._draw_final_plot(xdata,ydata,stds=stds,title=title)


            

    def _close_final_plot(self):
        self.final_plot_popup.close()


    def _draw_final_plot(self, x, y, stds=None, save_path=None,title='Result',legend=None):
        print x
        print y
        fig = plt.figure(figsize=(3,1.5))
        ax = fig.add_subplot(111)
        if stds is not None:
            if legend:
                ax.errorbar(x,y,yerr=stds,label = legend)
                ax.legend(prop={'size':6})
            else:
                ax.errorbar(x,y,yerr=stds)
        yticks = np.linspace(min(y),max(y),5)
        yticks = [round(s,2) for s in yticks]
        xticks = np.linspace(x[0],x[len(y)-1],5)
        xticks = [round(s,2) for s in xticks]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticks,fontsize = 6)
        ax.set_yticks(yticks)
        ax.set_yticklabels(yticks,fontsize = 6)
        fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
        xlabel = 'Sample'
#        if title == 'Beam Mapper':
 #           xlabel = 'Position'
            
        if title == 'Pol Efficiency':
            xlabel = 'Angle'
        elif title == 'Single Channel FTS':
            xlabel = 'Position'
#        elif title == 'Result':
 #           xlabel = 'Sample'
        ax.set_title(title, fontsize=12)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel('Amplitude', fontsize=10)
        if save_path is not None:
            fig.savefig(save_path)
        else:
            fig.savefig('temp_files/temp_fp.png')
            image = QtGui.QPixmap('temp_files/temp_fp.png')
            image = image.scaled(800, 400)
            getattr(self,  '_final_plot_popup_result_label').setPixmap(image)
        pl.close('all')


    def _draw_beammaper_final(self,save_path=None):
        fig = pl.figure()
        ax = fig.add_subplot(111)
        ax.pcolor(self.X, self.Y, self.Z_data)
        ax.set_title('BEAM DATA', fontsize=12)
        ax.set_xlabel('Position (cm)', fontsize=12)
        ax.set_ylabel('Position (cm)', fontsize=12)
        fig.savefig('temp_files/temp_beam.png')
        pl.close('all')
        image = QtGui.QPixmap('temp_files/temp_beam.png')
        image = image.scaled(600, 300)
        if save_path is not None:
            fig.savefig(save_path)
        else:
            fig.savefig('temp_files/temp_beam.png')
            image = QtGui.QPixmap('temp_files/temp_beam.png')
            image = image.scaled(800, 400)
            getattr(self,  '_final_plot_popup_result_label').setPixmap(image)
        pl.close('all')
        

    def _replot(self):
        title = getattr(self, '_final_plot_popup_plot_title_lineedit').text()
        legend = getattr(self,'_final_plot_popup_data_label_lineedit').text()
        if title != '':
            if legend != '':
                self._draw_final_plot(self.xdata,self.ydata,stds=self.stds,title = title, legend = legend)
            else:
                self._draw_final_plot(self.xdata,self.ydata,stds=self.stds,title = title)
        else:
             if legend != '':
                self._draw_final_plot(self.xdata,self.ydata,stds=self.stds, legend = legend)

    def _save_final_plot(self):
        save_path = QtGui.QFileDialog.getSaveFileName(self, 'Save Location', self.user_desktop_path,
                                                            "Image files (*.png *.jpg *.gif)")
        plot_path = copy(save_path).replace('csv','png')
        if self.is_beam:
            self._draw_beammaper_final(str(plot_path))
            self.write_file(self.X,self.Y,save_path,self.Z_data,stds=self.stds)
        elif self.is_iv:
            self._draw_final_plot(self.xdata,self.ydata,str(plot_path))
            self.write_file(self.xdata,self.ydata,save_path)
        else:
            self._draw_final_plot(self.xdata,self.ydata,str(plot_path),stds=self.stds)
            self.write_file(self.xdata,self.ydata,save_path,stds=self.stds)
        if self.is_fft:
            fft_path = str(copy(save_path)).strip('.csv')
            fft_path += '_fft.csv'
            self.write_file(self.posFreqArray,self.FTArrayPosFreq,[0]*len(self.posFreqArray),data_path = fft_path)
            filenameRoot = copy(fft_path).replace('csv','png')
            self.fts_analyzer.plotCompleteFT(self.posFreqArray,self.FTArrayPosFreq,filenameRoot)
    
            
    def write_file(self,xdata,ydata,data_path,stds=None,zdata=None):
        with open(data_path,'w') as f:
            if zdata is None:
                if stds is None:
                    for x, y in zip(xdata, ydata):
                        f.write('{:f}\t{:f}\n'.format(x, y))
                else:
                    for x, y,std in zip(xdata, ydata,stds):
                        f.write('{:f}\t{:f}\t{:f}\n'.format(x, y, std))
            else:
                for i, x in enumerate(self.x_grid):
                    for j, y in enumerate(self.y_grid):
                        f.write('{0},{1},{2},{3}\n'.format(x, y, zdata[j,i], stds[j,i]))
                    


    def _pause(self):
        global continue_run
        continue_run = False






    #################################################
    #################################################
    # DAQ TYPE SPECFIC CODES
    #################################################
    #################################################


    #################################################
    # XY COLLECTOR
    #################################################

    def _close_xycollector(self):
        self.xycollector_popup.close()

    def _xycollector(self):
        if not hasattr(self, 'xycollector_popup'):
            self._create_popup_window('xycollector_popup')
        else:
            self._initialize_panel('xycollector_popup')
        self._build_panel(settings.xycollector_build_dict)
        for combobox_widget, entry_list in self.xycollector_combobox_entry_dict.iteritems():
            self.populate_combobox(combobox_widget, entry_list)
        self.xycollector_popup.showMaximized()
        self.xycollector_popup.setWindowTitle('XY COLLECTOR')
#        self._update_pol_efficiency_popup()


    def _run_xycollector(self):
        global continue_run
        continue_run = True
        visa_x = getattr(self,'_xycollector_popup_visa_resource_name_x_combobox').currentText()
        visa_x = getattr(self, '_xycollector_popup_visa_resource_name_y_combobox').currentText()
        self.xdata,self.ydata = [],[]
        while continue_run:
            x,y = self.real_daq.get_data2()
            self.xdata.append(x)
            self.ydata.append(y)
            self._draw_x()
            self._draw_y()
            self._draw_xycollector()
            root.update()


    def _draw_x(self):
        fig = pl.figure(figsize=(3,2))
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
        ax.plot(self.xdata)
        ax.set_title('Applied Voltage', fontsize=10)
        ax.set_xlabel('Sample', fontsize=8)
        ax.set_ylabel('Applied Voltage', fontsize=8)
        fig.savefig('temp_files/temp_xv.png')
        pl.close('all')
        image = QtGui.QPixmap('temp_files/temp_xv.png')
        image = image.scaled(600,400)
        getattr(self, '_xycollector_popup_xdata_label').setPixmap(image)  

    def _draw_y(self):
        fig = pl.figure(figsize=(3,2))
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
        ax.plot(self.ydata)
        ax.set_title('Bolometer Voltage', fontsize=10)
        ax.set_xlabel('Sample', fontsize=8)
        ax.set_ylabel('Bolometer Voltage', fontsize=8)
        if len(self.ydata)>1:
            yticks = np.linspace(min(self.ydata),max(self.ydata),5)
            yticks = [round(x,2) for x in yticks]
            ax.set_yticks(yticks)
            ax.set_yticklabels(yticks,fontsize = 6)
        fig.savefig('temp_files/temp_yv.png')
        pl.close('all')
        image = QtGui.QPixmap('temp_files/temp_yv.png')
        image = image.scaled(600,400)
        getattr(self, '_xycollector_popup_ydata_label').setPixmap(image)       


    def _draw_xycollector(self):
        fig = pl.figure(figsize=(3,2))
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
        ax.plot(self.xdata,self.ydata)
        ax.set_title('IV Curve', fontsize=10)
        ax.set_xlabel('Applied Voltage', fontsize=8)
        ax.set_ylabel('Bolometer Voltage', fontsize=8)
        if len(self.ydata)>1:
            yticks = np.linspace(min(self.ydata),max(self.ydata),5)
            yticks = [round(x,2) for x in yticks]
            ax.set_yticks(yticks)
            ax.set_yticklabels(yticks,fontsize = 6)
            xticks = np.linspace(min(self.xdata),max(self.xdata),5)
            xticks = [round(s,2) for s in xticks]
            ax.set_xticks(xticks)
            ax.set_xticklabels(xticks,fontsize = 6)                             
       
        fig.savefig('temp_files/temp_iv.png')
        pl.close('all')
        image = QtGui.QPixmap('temp_files/temp_iv.png')
        image = image.scaled(600,400)
        getattr(self, '_xycollector_popup_xydata_label').setPixmap(image)
        
            

    #################################################
    # POL EFFICIENCY
    #################################################


    def _close_pol_efficiency(self):
        self.pol_efficiency_popup.close()

    def _pol_efficiency(self):
        if not hasattr(self, 'pol_efficiency_popup'):
            self._create_popup_window('pol_efficiency_popup')
        else:
            self._initialize_panel('pol_efficiency_popup')
        self._build_panel(settings.pol_efficiency_build_dict)
        for combobox_widget, entry_list in self.pol_efficiency_combobox_entry_dict.iteritems():
            self.populate_combobox(combobox_widget, entry_list)
        self._connect_to_com_port()
        self.pol_efficiency_popup.showMaximized()
        self.pol_efficiency_popup.setWindowTitle('POL EFFICIENCY')
        self._update_pol_efficiency_popup()
        self._blank_pol_plot()
        getattr(self, '_pol_efficiency_popup_save_pushbutton').setDisabled(True)
        self._draw_time_stream([0]*5, -1, -1,'_pol_efficiency_popup_time_stream_label')



    def _update_pol_efficiency_popup(self):
        scan_params = self._get_all_scan_params(popup='_pol_efficiency')
        if type(scan_params) is not dict:
            return None
        if 'starting_angle' in scan_params and 'ending_angle' in scan_params:
            start_angle = scan_params['starting_angle']
            end_angle = scan_params['ending_angle']
            step_size = scan_params['step_size']
            num_steps = (end_angle-start_angle)/step_size
            getattr(self,'_pol_efficiency_popup_number_of_steps_label').setText(str(num_steps))
            getattr(self,'_pol_efficiency_popup_position_slider_min_label').setText(str(start_angle))
            getattr(self,'_pol_efficiency_popup_position_slider_max_label').setText(str(end_angle))
            getattr(self, '_pol_efficiency_popup_position_monitor_slider').setMinimum(start_angle)
            getattr(self, '_pol_efficiency_popup_position_monitor_slider').setMaximum(end_angle)
        self.pol_efficiency_popup.repaint()

    def _close_pol_efficiency(self):
        self.pol_efficiency_popup.close()

    def _run_pol_efficiency(self):
        scan_params = self._get_all_pol_efficiency_scan_params()
        self.take_pol_efficiency(scan_params,1)

    def get_simulated_data(self, datatype, current_position, noise=10):
        '''
        noise is in percent and is of the max-min of data
        '''
        in_degree = current_position*np.pi/180
        dev = (np.random.randn()-0.5)*2/100*noise
        simulated_data = np.sin(in_degree) + dev
        return simulated_data


    def _blank_pol_plot(self):
        fig = pl.figure(figsize=(3,1.5))
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
        ax.plot([0]*5)
        ax.set_title('POL EFFICICENCY', fontsize=12)
        ax.set_xlabel('Angle', fontsize=10)
        ax.set_ylabel('Amplitude', fontsize=10)
        fig.savefig('temp_files/temp_pol.png')
        pl.close('all')
        image = QtGui.QPixmap('temp_files/temp_pol.png')
        image = image.scaled(600,300)
        getattr(self, '_pol_efficiency_popup_data_label').setPixmap(image)

    def take_pol_efficiency(self, scan_params, noise=10):
        global continue_run
        continue_run = True
        com_port = self._get_com_port('_pol_efficiency_popup_current_com_port_combobox')
        stepnum = (scan_params['ending_angle']-scan_params['starting_angle'])/scan_params['step_size']+1
        self.xdata = np.linspace(scan_params['starting_angle'],scan_params['ending_angle'],stepnum)
        self.ydata = []
        angles = []
        self.stds = []
        i = 0
        while continue_run and i < len(self.xdata):
            step = self.xdata[i]
#        for i, step in enumerate(self.xdata):
            data_point = self.get_simulated_data(int, step, noise=noise)
            angles.append(step)
            if step != 0:
                getattr(self, 'sm_{0}'.format(com_port)).finite_rotation(scan_params['step_size'])
                time.sleep(scan_params['pause_time']/1000)
            current_angle = getattr(self, 'sm_{0}'.format(com_port)).get_position()
            data_time_stream, mean, min_, max_, std = self.real_daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
                                                                        sample_rate=scan_params['sample_rate'],central_value=data_point)
            self.ydata.append(mean)
            self.stds.append(std)
            getattr(self,'_pol_efficiency_popup_mean_label').setText('{0:.3f}'.format(mean))
            getattr(self,'_pol_efficiency_popup_current_angle_label').setText(str(step))
            getattr(self,'_pol_efficiency_popup_std_label').setText('{0:.3f}'.format(std))
            start = scan_params['starting_angle']
            end = scan_params['ending_angle']

            self._draw_time_stream(data_time_stream, min_, max_, '_pol_efficiency_popup_time_stream_label',int(scan_params['integration_time']))
            fig = pl.figure(figsize=(3,2))
            ax = fig.add_subplot(111)
            fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
            ax.plot(angles,self.ydata)
            ax.set_title('POL EFFICICENCY', fontsize=12)
            yticks = np.linspace(min(self.ydata),max(self.ydata),5)
            yticks = [round(x,2) for x in yticks]
            ax.set_yticks(yticks)
            ax.set_yticklabels(yticks,fontsize = 6)
            xticks = np.linspace(start,end,5)
            ax.set_xticks(xticks)
            ax.set_xlabel('Angle', fontsize=10)
            ax.set_ylabel('Amplitude', fontsize=10)
            fig.savefig('temp_files/temp_pol.png')
            pl.close('all')
            image = QtGui.QPixmap('temp_files/temp_pol.png')
            image = image.scaled(600,400)
            getattr(self, '_pol_efficiency_popup_data_label').setPixmap(image)
            self.pol_efficiency_popup.repaint()
            getattr(self, '_pol_efficiency_popup_position_monitor_slider').setSliderPosition(step)
            i += 1
            root.update()
        getattr(self, '_pol_efficiency_popup_save_pushbutton').setEnabled(True)
#        return steps, data


    def read_file(self, filename):
        x, y = np.loadtxt(filename, unpack=True)
        return x,y

    def _get_all_pol_efficiency_scan_params(self):
        scan_params = {}
        for pol_efficiency_setting in settings.pol_int_run_settings:
            pull_from_widget_name = '_pol_efficiency_popup_{0}_lineedit'.format(pol_efficiency_setting)
            if hasattr(self, pull_from_widget_name):
                value = getattr(self, pull_from_widget_name).text()
                if len(str(value)) == 0:
                    value = 0
                else:
                    value = int(value)
                scan_params[pol_efficiency_setting] = value
        for pol_efficiency_setting in settings.pol_pulldown_run_settings:
            pull_from_widget_name = '_pol_efficiency_popup_{0}_combobox'.format(pol_efficiency_setting)
            if hasattr(self, pull_from_widget_name):
                value = str(getattr(self, pull_from_widget_name).currentText())
                scan_params[pol_efficiency_setting] = value
        return scan_params


   
    #################################################
    # USER MOVE STEPPER
    #################################################

    def _close_user_move_stepper(self):
        self.user_move_stepper_popup.close()

    def _user_move_stepper(self):
        if not hasattr(self, 'user_move_stepper_popup'):
            self._create_popup_window('user_move_stepper_popup')
        else:
            self._initialize_panel('user_move_stepper_popup')
        self._build_panel(settings.user_move_stepper_build_dict)
        for combobox_widget, entry_list in self.user_move_stepper_combobox_entry_dict.iteritems():
            self.populate_combobox(combobox_widget, entry_list)
        current_string, position_string, velocity_string = self._connect_to_com_port()

       	getattr(self, '_user_move_stepper_popup_current_act_label').setText(current_string)
        getattr(self,'_user_move_stepper_popup_velocity_act_label').setText(velocity_string)
        getattr(self,'_user_move_stepper_popup_current_position_label').setText(position_string)
        self._update_stepper_position()
        self.user_move_stepper_popup.showMaximized()
        self.user_move_stepper_popup.setWindowTitle('User Move Stepper')


    def _add_comports_to_user_move_stepper(self):
        for i, com_port in enumerate(settings.com_ports):
            com_port_entry = QtCore.QString(com_port)
            getattr(self, '_user_move_stepper_popup_current_com_port_combobox').addItem(com_port_entry)

    def _set_velocity(self):
        com_port = self._get_com_port('_user_move_stepper_popup_current_com_port_combobox')
        speed =  str(getattr(self, '_user_move_stepper_popup_velocity_set_lineedit').text())
        getattr(self, 'sm_{0}'.format(com_port)).set_speed(float(speed))
        actual = getattr(self, 'sm_{0}'.format(com_port)).get_velocity().strip('VE=')
        getattr(self,'_user_move_stepper_popup_velocity_act_label').setText(str(actual))

    def _set_current(self):
        com_port = self._get_com_port('_user_move_stepper_popup_current_com_port_combobox')
        current =  getattr(self, '_user_move_stepper_popup_current_set_lineedit').text()
        getattr(self, 'sm_{0}'.format(com_port)).set_current(float(current))
        actual =  getattr(self, 'sm_{0}'.format(com_port)).get_motor_current().strip('CC=')
        getattr(self,'_user_move_stepper_popup_current_act_label').setText(str(actual))


    def _move_stepper(self):
        move_to_pos = int(str(getattr(self, '_user_move_stepper_popup_move_to_position_lineedit').text()))
        com_port = self._get_com_port('_user_move_stepper_popup_current_com_port_combobox')
        getattr(self, 'sm_{0}'.format(com_port)).move_to_position(move_to_pos)
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
        com_port = self._get_com_port('_user_move_stepper_popup_current_com_port_combobox')
        stepper_position = getattr(self, 'sm_{0}'.format(com_port)).get_position().strip('SP=')
        header_str = '{0} Current Position:'.format(com_port)
        getattr(self, '_user_move_stepper_popup_current_position_header_label').setText(header_str)
        getattr(self, '_user_move_stepper_popup_current_position_label').setText(str(stepper_position))


    #################################################
    # SINGLE CHANNEL FTS BILLS
    #################################################

    def _close_single_channel_fts(self):
        self.single_channel_fts_popup.close()

    def _single_channel_fts(self):
        self.fts_daq = FTSDAQ()
        self.fourier = Fourier()
        if not hasattr(self, 'single_channel_fts_popup'):
            self._create_popup_window('single_channel_fts_popup')
        else:
            self._initialize_panel('single_channel_fts_popup')
        self._build_panel(settings.single_channel_fts_build_dict)
        for unique_combobox, entries in settings.combobox_entry_dict.iteritems():
            self.populate_combobox(unique_combobox, entries)
        self._update_single_channel_fts()
        self._connect_to_com_port(single_channel_fts=1)
        self._connect_to_com_port(single_channel_fts=2)
        self. _blank_fts_plot()
        getattr(self, '_single_channel_fts_popup_save_pushbutton').setDisabled(True)
        self.single_channel_fts_popup.showMaximized()
        self.single_channel_fts_popup.setWindowTitle('Single Channel FTS')
        self._draw_time_stream([0]*5, -1, -1,'_single_channel_fts_popup_time_stream_label')

    def _get_all_single_channel_fts_scan_params(self):
        scan_params = {}
        for fts_run_setting in settings.fts_int_run_settings:
            pull_from_widget_name = '_single_channel_fts_popup_{0}_lineedit'.format(fts_run_setting)
            if hasattr(self, pull_from_widget_name):
                value = getattr(self, pull_from_widget_name).text()
                if len(str(value)) == 0:
                    value = 0
                else:
                    value = int(value)
                scan_params[fts_run_setting] = value
        for fts_run_setting in settings.fts_pulldown_run_settings:
            pull_from_widget_name = '_single_channel_fts_popup_{0}_combobox'.format(fts_run_setting)
            if hasattr(self, pull_from_widget_name):
                value = str(getattr(self, pull_from_widget_name).currentText())
                scan_params[fts_run_setting] = value
        for fts_run_setting in settings.fts_float_run_settings:
            pull_from_widget_name = '_single_channel_fts_popup_{0}_lineedit'.format(fts_run_setting)
            if hasattr(self, pull_from_widget_name):
                value = getattr(self, pull_from_widget_name).text()
                if len(str(value)) == 0:
                    value = 0
                else:
                    value = float(value)
                scan_params[fts_run_setting] = value
        return scan_params

    def _compute_fft(self, positions, data, scan_params):
        frequency_vector, fft_vector = self.fourier.convert_IF_to_FFT_data(positions, data)
        fig = pl.figure(figsize=(3.5,1.5))
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.24, right=0.99, top=0.80, bottom=0.35)
        ax.plot(frequency_vector, fft_vector)
        ax.set_xlabel('Frequency (GHz)')
        ax.set_ylabel('Amplitude')
        ax.set_title('Spectra')
        fig.savefig('temp_files/temp_fft.png')
        del fig
        image = QtGui.QPixmap('tempfft.png')
        image = image.scaled(350, 175)
        getattr(self, '_single_channel_fts_popup_fft_label').setPixmap(image)

    def _compute_resolution_and_max_frequency(self, scan_params):
        total_steps = scan_params['ending_position'] - scan_params['starting_position']
        total_distance = total_steps * scan_params['DistPerStep'] #nm
        min_distance = scan_params['step_size'] * scan_params['DistPerStep'] #nm
        nyquist_distance = 2 * min_distance
        highest_frequency = ((2.99792458 * 10 ** 8) / nyquist_distance) / (10 ** 9) # GHz

        resolution = ((3 * 10 ** 8) / total_distance) / (10 ** 9) # GHz
        resolution = '{0:.4}'.format(0.5 * resolution * 1e9)
        highest_frequency = '{0:.4}'.format(0.5 * highest_frequency * 1e9)
        return resolution, highest_frequency

    def _update_single_channel_fts(self):
        scan_params = self._get_all_scan_params(popup='_single_channel_fts')
        if type(scan_params) is not dict:
            return None
        # Update Slider
        if 'starting_position' in scan_params and 'ending_position' in scan_params:
            resolution, highest_frequency = self._compute_resolution_and_max_frequency(scan_params)
            resolution_widget = '_single_channel_fts_popup_resolution_label'
            getattr(self, resolution_widget).setText(resolution)
            highest_frequency_widget = '_single_channel_fts_popup_highest_frequency_label'
            getattr(self, highest_frequency_widget).setText(highest_frequency)
            num_steps = (scan_params['ending_position']-scan_params['starting_position'])/scan_params['step_size']
            getattr(self, '_single_channel_fts_popup_number_of_steps_label').setText(str(num_steps))
            self._update_slider_setup(scan_params)
        self.single_channel_fts_popup.repaint()

    def _update_slider(self, slider_pos):
        print slider_pos

    def _apodize(self):
        scan_params = self._get_all_single_channel_fts_scan_params()
        self.apodization = scan_params['apodization_type']
        print self.apodization

    def _update_slider_setup(self, scan_params):
        min_slider = '_single_channel_fts_popup_position_slider_min_label'
        max_slider = '_single_channel_fts_popup_position_slider_max_label'
        getattr(self, min_slider).setText(str(scan_params['starting_position']))
        getattr(self, max_slider).setText(str(scan_params['ending_position']))
        slider = '_single_channel_fts_popup_position_monitor_slider'
        getattr(self, slider).setMinimum(scan_params['starting_position'])
        getattr(self, slider).setMaximum(scan_params['ending_position'])
        com_port = self._get_com_port('_single_channel_fts_popup_current_com_port_combobox')
        motor_position = 0
        getattr(self, slider).setSliderPosition(motor_position)
        getattr(self, slider).sliderPressed.connect(self._dummy)
        self.starting_position = scan_params['starting_position']

    def _blank_fts_plot(self):
        data = [0]*5
        fig = pl.figure(figsize=(3,1.5))
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
        ax.plot(data)
        ax.set_xlabel('Mirror Position (m)',fontsize = 10)
        ax.set_ylabel('Amplitude',fontsize = 10)
        ax.set_title('Interferogram')
        fig.savefig('temp_files/temp_int.png')
        pl.close('all')
        image = QtGui.QPixmap('temp_files/temp_int.png')
        image = image.scaled(600,300)
        getattr(self, '_single_channel_fts_popup_interferogram_label').setPixmap(image)


    def _rotate_grid(self):
        polar_com_port = self._get_com_port('_single_channel_fts_popup_grid_current_com_port_combobox')
        angle = getattr(self,'_single_channel_fts_popup_desired_grid_angle_lineedit').text()
        getattr(self, 'sm_{0}'.format(polar_com_port)).finite_rotation(int(angle))


    def _run_fts(self):
        global continue_run
        continue_run = True
        scan_params = self._get_all_scan_params(popup='_single_channel_fts')
        linear_com_port = self._get_com_port('_single_channel_fts_popup_current_com_port_combobox')
        self._apodize()
        positions, data, self.stds = [], [], []
        pause = int(scan_params['pause_time'])/1000
        #dummy_x, dummy_y = self.fts_daq.simulate_inteferogram(scan_params['starting_position'], scan_params['ending_position'],scan_params['step_size'])
        amplitude = self.fts_daq.read_inteferogram('SQ5_Pix101_90T_Spectra_09.if',1)
        i = 0
        helper = np.arange(scan_params['starting_position'], scan_params['ending_position'] + scan_params['step_size'], scan_params['step_size'])
        while continue_run and i < len(helper):
            position = helper[i]
#        for i,position in enumerate( np.arange(scan_params['starting_position'], scan_params['ending_position'] + scan_params['step_size'], scan_params['step_size'])):
            getattr(self, 'sm_{0}'.format(linear_com_port)).move_to_position(position)
            time.sleep(pause)
            #data_time_stream, mean, min_, max_, std = self.daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
            #                                                            sample_rate=scan_params['sample_rate'],central_value = amplitude[i])

            data_time_stream, mean, min_, max_, std = self.real_daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
                                     sample_rate=scan_params['sample_rate'],central_value = amplitude[i])
            self.stds.append(std)
            getattr(self, '_single_channel_fts_popup_std_label').setText('{0:.3f}'.format(std))
            getattr(self, '_single_channel_fts_popup_mean_label').setText('{0:.3f}'.format(mean))
            getattr(self, '_single_channel_fts_popup_current_position_label').setText('{0:.3f}'.format(position))
            self._draw_time_stream(data_time_stream, min_, max_,'_single_channel_fts_popup_time_stream_label',int(scan_params['integration_time']))
            positions.append(position * scan_params['DistPerStep'])
            data.append(mean)
            fig = pl.figure(figsize=(3.5,1.5))
            ax = fig.add_subplot(111)
            fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
            ax.plot(positions, data)
            yticks = np.linspace(min(data),max(data),5)
            yticks = [round(x,2) for x in yticks]
            xticks = np.linspace(positions[0],positions[-1],5)
            xticks = [round(x,2) for x in xticks]
            ax.set_xticks(xticks)
            ax.set_xticklabels(xticks,fontsize = 6)
            ax.set_yticks(yticks)
            ax.set_yticklabels(yticks,fontsize = 6)
            ax.set_xlabel('Mirror Position (in)')
            ax.set_ylabel('Amplitude')
            ax.set_title('Inteferogram')
            fig.savefig('temp_files/temp_int.png')
            pl.close('all')
            image = QtGui.QPixmap('temp_files/temp_int.png')
            image = image.scaled(600, 300)
            getattr(self, '_single_channel_fts_popup_interferogram_label').setPixmap(image)
            self.single_channel_fts_popup.repaint()
            getattr(self, '_single_channel_fts_popup_position_monitor_slider').setSliderPosition(position)
            i += 1
            root.update() 
        self.posFreqArray,self.FTArrayPosFreq = self.fts_analyzer.analyzeBolo(positions, data,apodization=self.apodization)
        image = QtGui.QPixmap('temp_files/temp_fft.png')
        image = image.scaled(600, 300)
        getattr(self, '_single_channel_fts_popup_fft_label').setPixmap(image)
        self.xdata = positions
        self.ydata = data
        getattr(self, '_single_channel_fts_popup_save_pushbutton').setEnabled(True)


    #################################################
    # BEAM MAPPER
    #################################################

    def _close_beam_mapper(self):
        '''
        Description: Closes the Beam Mapper popup window
        Input: None
        Output: None
        '''

        self.beam_mapper_popup.close()

    def _beam_mapper(self):
        self.beam_map_daq = BeamMapDAQ()
        if not hasattr(self, 'beam_mapper_popup'):
            self._create_popup_window('beam_mapper_popup')
        else:
            self._initialize_panel('beam_mapper_popup')
        self._build_panel(settings.beam_mapper_build_dict)
        for combobox_widget, entry_list in self.beam_mapper_combobox_entry_dict.iteritems():
            self.populate_combobox(combobox_widget, entry_list)
        self._connect_to_com_port(beammapper=1)
        self._connect_to_com_port(beammapper=2)
        self._draw_time_stream([0]*5, -1, -1,'_beam_mapper_popup_time_stream_label')
        self.beam_mapper_popup.showMaximized()
        self._initialize_beam_mapper()
        self.beam_mapper_popup.repaint()
        getattr(self, '_beam_mapper_popup_save_pushbutton').setDisabled(True)


    def _get_all_beam_mapper_scan_params(self):
        scan_params = {}
        for beam_map_setting in settings.beam_map_int_settings:
            pull_from_widget_name = '_beam_mapper_popup_{0}_lineedit'.format(beam_map_setting)
            if hasattr(self, pull_from_widget_name):
                value = getattr(self, pull_from_widget_name).text()
                if len(str(value)) == 0:
                    value = 0
                else:
                    value = int(value)
                scan_params[beam_map_setting] = value
        for beam_map_setting in settings.beam_map_pulldown_run_settings:
            pull_from_widget_name = '_beam_mapper_popup_{0}_combobox'.format(beam_map_setting)
            if hasattr(self, pull_from_widget_name):
                value = str(getattr(self, pull_from_widget_name).currentText())
                scan_params[beam_map_setting] = value
        scan_params = self._get_grid(scan_params)
        return scan_params

    def _get_grid(self, scan_params):
        x_total = scan_params['end_x_position'] - scan_params['start_x_position']
        x_steps = scan_params['step_size_x']
        n_points_x = (scan_params['end_x_position']-scan_params['start_x_position'])/scan_params['step_size_x']
        n_points_y = (scan_params['end_y_position']-scan_params['start_y_position'])/scan_params['step_size_y']
        scan_params['n_points_x'] = n_points_x
        scan_params['n_points_y'] = n_points_y
        scan_params['x_total'] = x_total
        getattr(self, '_beam_mapper_popup_total_x_label').setText('{0} in'.format(str(x_total)))
        y_total = scan_params['end_y_position'] - scan_params['start_y_position']
        y_steps = scan_params['step_size_y']
        getattr(self, '_beam_mapper_popup_total_y_label').setText('{0} in'.format(str(y_total)))
        scan_params['y_total'] = y_total
        return scan_params

    def _create_beam_grid(self, scan_params):
        fig = pl.figure(figsize=(3,3))
        ax = fig.add_subplot(111)
        #fig.savefig('temp_files/temp_beam_map.png')
        pl.close('all')

    def _initialize_beam_mapper(self):
        if len(str(self.sender().whatsThis())) == 0:
            return None
        else:
            scan_params = self._get_all_scan_params(popup='_beam_mapper')
            if scan_params is not None and len(scan_params) > 0:
                self.beam_map_daq.simulate_beam(scan_params)
                image = QtGui.QPixmap('temp_files/temp_beam.png')
                image = image.scaled(600, 300)
                getattr(self, '_beam_mapper_popup_2D_plot_label').setPixmap(image)
                n_points_x= scan_params['n_points_x']
                n_points_y= scan_params['n_points_y']
                getattr(self,'_beam_mapper_popup_n_points_x_label').setText(str(n_points_x))
                getattr(self,'_beam_mapper_popup_n_points_y_label').setText(str(n_points_y))

    def _take_beam_map(self):
        global continue_run
        continue_run = True
        scan_params = self._get_all_scan_params(popup='_beam_mapper')
        x_grid = np.linspace(scan_params['start_x_position'], scan_params['end_x_position'],  scan_params['n_points_x'])
        y_grid = np.linspace(scan_params['start_y_position'], scan_params['end_y_position'],  scan_params['n_points_y'])
        X, Y = np.meshgrid(x_grid, y_grid)
        Z_data = np.zeros(shape=X.shape)
        self.stds = np.zeros(shape=X.shape)
        X_sim, Y_sim, Z_sim = self.beam_map_daq.simulate_beam(scan_params)
        i = 0
        while continue_run and i < len(x_grid):
            x_pos = x_grid[i]
#        for i, x_pos in enumerate(x_grid):
            for j, y_pos in enumerate(y_grid):
                central_value = Z_sim[i][j]
                data_time_stream, mean, min_, max_, std = self.real_daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
                                                                            sample_rate=scan_params['sample_rate'], central_value=central_value)
                self.stds[j][i]=std
                Z_datum = mean
                Z_data[j][i] = Z_datum
                fig = pl.figure()
                ax = fig.add_subplot(111)
                ax.pcolor(X, Y, Z_data)
                ax.set_title('BEAM DATA', fontsize=12)
                ax.set_xlabel('Position (cm)', fontsize=12)
                ax.set_ylabel('Position (cm)', fontsize=12)
                fig.savefig('temp_files/temp_beam.png')
                pl.close('all')
                self._draw_time_stream(data_time_stream, min_, max_,'_beam_mapper_popup_time_stream_label')
                image = QtGui.QPixmap('temp_files/temp_beam.png')
                image = image.scaled(600, 300)
                getattr(self, '_beam_mapper_popup_2D_plot_label').setPixmap(image)
                getattr(self, '_beam_mapper_popup_data_mean_label').setText('{0:.3f}'.format(mean))
                getattr(self, '_beam_mapper_popup_x_position_label').setText('{0:.3f}'.format(x_pos))
                getattr(self, '_beam_mapper_popup_y_position_label').setText('{0:.3f}'.format(y_pos))
                getattr(self, '_beam_mapper_popup_data_std_label').setText('{0:.3f}'.format(std))
                self.beam_mapper_popup.repaint()
                i += 1
                root.update()                
        self.X = X
        self.Y = Y
        self.Z_data = Z_data
        self.x_grid = x_grid
        self.y_grid = y_grid
        getattr(self, '_beam_mapper_popup_save_pushbutton').setEnabled(True)


    #################################################
    # WIDGET GENERATORS AND FUNCTIONS
    #################################################

    def _initialize_panel(self, panel=None):
        panel = getattr(self, panel)
        for index in reversed(range(panel.layout().count())):
            widget = panel.layout().itemAt(index).widget()
            widget.setParent(None)

    def _unpack_widget_function(self, function_text):
        if function_text is None:
            return None
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
