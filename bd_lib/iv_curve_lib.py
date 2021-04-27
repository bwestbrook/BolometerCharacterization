import os
import bisect
import numpy as np
import pylab as pl
from pprint import pprint
from copy import copy


class IVCurveLib():

    def __init__(self):
        self.r_n_fraction = 0.75
        self.simulated_bands_folder = 'bd_filter_bands'
        self.dewar_transmission = 0.75

    def ivlib_plot_all_curves(self, bolo_voltage_bias, bolo_current, bolo_current_stds=None, fit_clip=None, plot_clip=None,
                              label='', sample_name='', t_bath='275', t_load='300', pturn=True,
                              left=0.1, right=0.98, top=0.9, bottom=0.13, hspace=0.8,
                              show_plot=False):
        '''
        This function creates an x-y scatter plot with v_bolo on the x-axis and
        bolo curent on the y-axis.  The resistance value is reported as text annotation
        Inputs:
            bolo_votlage_bias: bolo_voltage in Volts
            bolo_current: bolo_current in Amps
        '''
        fig = pl.figure(figsize=(9, 4))
        fig.subplots_adjust(left=left, right=right, bottom=bottom, hspace=hspace)
        ax1 = fig.add_subplot(221)
        # Make Title from sample name T_bath and T_load
        title = '{0}\n@{1}mK with {2}K Load'.format(sample_name, t_bath, t_load)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(223)
        ax4 = fig.add_subplot(224)
        ax2.set_axis_off()
        fit_selector = np.logical_and(fit_clip[0] < bolo_voltage_bias, bolo_voltage_bias < fit_clip[1])
        plot_selector = np.logical_and(plot_clip[0] < bolo_voltage_bias, bolo_voltage_bias < plot_clip[1])

        add_fit = False
        fit_vals = (1, 1)
        if len(bolo_voltage_bias[fit_selector]) > 2:
            fit_vals = np.polyfit(bolo_voltage_bias[fit_selector], bolo_current[fit_selector], 1)
            v_fit_x_vector = np.arange(fit_clip[0], fit_clip[1], 0.2)
            selector_2 = np.logical_and(fit_clip[0] < v_fit_x_vector, v_fit_x_vector < fit_clip[1])
            poly_fit = np.polyval(fit_vals, v_fit_x_vector[selector_2])
            add_fit = True
        resistance_vector = bolo_voltage_bias / bolo_current
        power_vector = bolo_voltage_bias * bolo_current
        ax1.plot(bolo_voltage_bias[plot_selector], bolo_current[plot_selector], '.', label=label)
        if bolo_current_stds is not None:
            ax1.errorbar(bolo_voltage_bias[plot_selector], bolo_current[plot_selector], yerr=bolo_current_stds[plot_selector],
                         label='error', marker='.', linestyle='None', alpha=0.25)
        if pturn and len(bolo_voltage_bias) > 2 and len(bolo_current[plot_selector]) > 0:
            pt_idx = np.where(bolo_current[plot_selector] == min(bolo_current[plot_selector]))[0][0]
            pl_idx = np.where(bolo_voltage_bias[plot_selector] == min(bolo_voltage_bias[plot_selector]))[0][0]
            pturn_pw = bolo_current[plot_selector][pt_idx] * bolo_voltage_bias[plot_selector][pt_idx]
            plast_pw = bolo_current[plot_selector][pl_idx] * bolo_voltage_bias[plot_selector][pl_idx]
            ax1.plot(bolo_voltage_bias[plot_selector][pt_idx], bolo_current[plot_selector][pt_idx],
                     '*', markersize=10.0, color='g', label='Pturn = {0:.2f} pW'.format(pturn_pw))
            ax1.plot(bolo_voltage_bias[plot_selector][pl_idx], bolo_current[plot_selector][pl_idx],
                     '*', markersize=10.0, color='m', label='Plast = {0:.2f} pW'.format(plast_pw))
        ax3.plot(bolo_voltage_bias[plot_selector], resistance_vector[plot_selector], 'b', label='Res {0:.4f} ($\Omega$)'.format(1.0 / fit_vals[0]))
        #ax4.plot(bolo_voltage_bias[power_selector], power_vector[power_selector], resitance_vector[plot_selector], 'r', label='Power (pW)')
        power_selector = np.logical_and(0 < power_vector, power_vector < 0.25 * np.max(power_vector))
        ax4.plot(resistance_vector[plot_selector], power_vector[plot_selector], 'r', label='Power (pW)')
        if add_fit:
            ax1.plot(v_fit_x_vector[selector_2], poly_fit, label='Fit: {0:.5f}$\Omega$'.format(1.0 / fit_vals[0]))
        # Label the axis
        ax1.set_xlabel("Voltage ($\mu$V)", fontsize=12)
        ax1.set_ylabel("Current ($\mu$A)", fontsize=12)
        ax3.set_xlabel("Voltage ($\mu$V)", fontsize=12)
        ax3.set_ylabel("Res ($\Omega$)", fontsize=12)
        ax4.set_xlabel("Res ($\Omega$)", fontsize=12)
        ax4.set_ylabel("Power ($pW$)", fontsize=12)
        # Set the titles
        ax1.set_title('IV of {0}'.format(title))
        ax3.set_title('RV of {0}'.format(title))
        ax4.set_title('PR of {0}'.format(title))
        # Grab all the labels and combine them 
        handles, labels = ax1.get_legend_handles_labels()
        handles += ax3.get_legend_handles_labels()[0]
        labels += ax3.get_legend_handles_labels()[1]
        handles += ax4.get_legend_handles_labels()[0]
        labels += ax4.get_legend_handles_labels()[1]
        ax2.legend(handles, labels, numpoints=1, mode="expand", bbox_to_anchor=(0, 0.1, 1, 1))
        #ax4.set_ylim(0, 0.5 * max(power_vector[plot_selector]))
        #ax4.set_xlim(0, 1.1 * max(power_vector[plot_selector]))
        #(max(power_vector[plot_selector]) - 0.8 * max(power_vector[plot_selector]),
        xlim_range = max(plot_clip) - min(plot_clip)
        ax1.set_xlim((plot_clip[0] - 0.1 * xlim_range, plot_clip[1] + 0.1 * xlim_range))
        ax3.set_xlim((plot_clip[0] - 0.1 * xlim_range, plot_clip[1] + 0.1 * xlim_range))
        #ax4.set_xlim((plot_clip[0], plot_clip[1]))
        if show_plot:
            pl.show()
        return fig
