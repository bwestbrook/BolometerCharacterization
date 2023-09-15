import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
from matplotlib import rc
rc('text', usetex=False)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent, screen_resolution, monitor_dpi):
        '''
        '''
        self.screen_resolution = screen_resolution
        self.dpi = monitor_dpi

    def mplc_adjust_subplots(self,
            fig,
            left=None,
            right=None,
            top=None,
            bottom=None,
            wspace=None,
            hspace=None):
        '''
        '''
        fig.subplots_adjust(
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            wspace=wspace,
            hspace=hspace
            )
        return fig

    def mplc_create_blank_fig(
            self,
            frac_screen_width=0.5,
            frac_screen_height=0.5,
            fig_name=None):
        '''
        '''
        width = (frac_screen_width * self.screen_resolution.width()) / self.dpi # in pixels
        height = (frac_screen_height * self.screen_resolution.height()) / self.dpi # in pixels
        fig = Figure(figsize=(width, height), dpi=self.dpi)
        self.fig = fig
        super(MplCanvas, self).__init__(fig)
        return fig

    def mplc_create_basic_fig(self,
            left=None,
            right=None,
            top=None,
            bottom=None,
            frac_screen_width=0.5,
            frac_screen_height=0.5,
            wspace=None,
            hspace=None):
        '''
        '''
        fig = self.mplc_create_blank_fig(
            frac_screen_width=frac_screen_width,
            frac_screen_height=frac_screen_height)
        fig.canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        fig = self.mplc_adjust_subplots(
            fig=fig,
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            wspace=wspace,
            hspace=hspace)
        self.fig = fig
        self.ax = ax
        return fig, ax

    def mplc_create_fig_with_legend_axes(self,
            left=None,
            right=None,
            top=None,
            bottom=None,
            frac_screen_width=0.5,
            frac_screen_height=0.5,
            wspace=None,
            hspace=None):
        '''
        '''
        fig = self.mplc_create_blank_fig(
            frac_screen_width=frac_screen_width,
            frac_screen_height=frac_screen_height)
        gs = fig.add_gridspec(1, 2, width_ratios=[2.5,1])
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        ax2.set_axis_off()
        fig = self.mplc_adjust_subplots(
            fig=fig,
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            wspace=wspace,
            hspace=hspace)
        self.fig = fig
        self.ax1 = ax1
        self.ax2 = ax2
        return fig

    def mplc_create_horizontal_array_fig(self,
            axes_names=['CH 1', 'CH 2'],
            left=None,
            right=None,
            top=None,
            bottom=None,
            frac_screen_width=0.5,
            frac_screen_height=0.5,
            wspace=None,
            hspace=None):
        '''
        '''
        fig = self.mplc_create_blank_fig(
            frac_screen_width=frac_screen_width,
            frac_screen_height=frac_screen_height)
        #fig.add_subplot(111)
        for i, axes_name in enumerate(axes_names):
            plot_loc = '1{0}{1}'.format(len(axes_names), i + 1)
            fig.add_subplot(int(plot_loc))
        fig = self.mplc_adjust_subplots(
            fig=fig,
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            wspace=wspace,
            hspace=hspace)
        self.fig = fig
        return fig

    def mplc_create_cr_paneled_plot(self,
            axes_names=['CH 1', 'CH 2'],
            left=None,
            right=None,
            top=None,
            bottom=None,
            frac_screen_width=0.5,
            frac_screen_height=0.5,
            wspace=None,
            hspace=None):
        '''
        '''
        fig = self.mplc_create_blank_fig(
            frac_screen_width=frac_screen_width,
            frac_screen_height=frac_screen_height)
        ax1 = fig.add_subplot(221)
        ax2 = fig.add_subplot(223)
        ax3 = fig.add_subplot(222)
        ax4 = fig.add_subplot(224)
        fig = self.mplc_adjust_subplots(
            fig=fig,
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            wspace=wspace,
            hspace=hspace)
        self.fig = fig
        self.ax1 = ax1
        self.ax2 = ax2
        self.ax3 = ax3
        self.ax4 = ax4
        return fig

    def mplc_create_iv_paneled_plot(self,
            axes_names=['CH 1', 'CH 2'],
            left=None,
            right=None,
            top=None,
            bottom=None,
            frac_screen_width=0.5,
            frac_screen_height=0.5,
            wspace=None,
            hspace=None):
        '''
        '''
        fig = self.mplc_create_blank_fig(
            frac_screen_width=frac_screen_width,
            frac_screen_height=frac_screen_height)
        ax1 = fig.add_subplot(221)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(223)
        ax4 = fig.add_subplot(224)
        ax2.set_axis_off()
        fig = self.mplc_adjust_subplots(
            fig=fig,
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            wspace=wspace,
            hspace=hspace)
        self.fig = fig
        self.ax1 = ax1
        self.ax2 = ax2
        self.ax3 = ax3
        self.ax4 = ax4
        return fig

    def mplc_create_two_pane_plot(self,
            axes_names=['CH 1', 'CH 2'],
            left=None,
            right=None,
            top=None,
            bottom=None,
            frac_screen_width=0.5,
            frac_screen_height=0.5,
            wspace=None,
            hspace=None):
        '''
        '''
        fig = self.mplc_create_blank_fig(
            frac_screen_width=frac_screen_width,
            frac_screen_height=frac_screen_height)
        fig.canvas = FigureCanvas(fig)
        gs = gridspec.GridSpec(1, 2,width_ratios=[2,1])
        ax1 = fig.add_subplot(gs[0])
        ax1_twinx= ax1.twinx()
        ax2 = fig.add_subplot(gs[1])
        ax2_twinx= ax2.twinx()
        fig = self.mplc_adjust_subplots(
            fig=fig,
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            wspace=wspace,
            hspace=hspace)
        self.fig = fig
        self.ax1 = ax1
        self.ax2 = ax2
        return fig

