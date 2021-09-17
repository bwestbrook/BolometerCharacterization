import matplotlib
import os
matplotlib.use('TkAgg')
import pylab as pl
#from DFT import *
import numpy as np
import numpy.polynomial.polynomial as poly
from scipy import signal
from scipy import optimize
from scipy import math
from scipy.fftpack import rfft, irfft, fftfreq, ifft, fft
from scipy.signal import argrelextrema
from scipy.signal import find_peaks_cwt
import scipy.integrate as integrate
import matplotlib.colors as colors
import matplotlib.ticker as ticker
import shutil
import statistics
from pprint import pprint
from statistics import median_low
from matplotlib import cm
from matplotlib import mlab
from math import exp, expm1
import sys
import bisect


class CosmicRayAnalyzer():

    def __init__(self):
        '''
        '''
        #define SQUID calibrations in uA/V
        self.squid_calibration_dict = {
                '1': 25.2,
                '2': 25.2,
                '3': 30.0,
                '4': 30.0,
                '5': 25.9,
                '6': 25.2
            }

        self.xaxes = []
        self.ymeansubs = []
        self.timeconsts = []
        self.energyhists = []
        self.rates = []
        self.allphases = []
        self.maxvalsxs = []
        self.maxvalsys = []


    def extract_raw_data(self, fn, colNames):
        '''
        Extract txt data from a LabVIEW output file fn and return
        a Python dictionary. colNames is a list of strings
        corresponding to each column in the txt file.

        d['filename'] returns the filename.
        d[column name] returns an array with the data from that column.
        '''
        f = open(fn)
        d = {}
        d['filename'] = fn
        llist = []
        for i in range(len(colNames)):
            llist.append([])
        for line in f:
            lineSplit = line.split()
            for i in range(len(colNames)):
                llist[i].append(float(lineSplit[i].replace(',','')))
        for i in range(len(colNames)):
            d[colNames[i]] = pl.array(llist[i])
        f.close()
        return d

    ###########################################################################

    def extract_raw_ts(self, fn):
        '''
        Extract XY data from a LabVIEW output file fn and
        return a Python dictionary with entries x and y.

        d['filename'] returns the filename.
        '''
        colNames = ['y0','y1','y2','y3','y4','y5','y6','y7']
        #colNames = ['y0','y1']
        return extract_raw_data(fn,colNames)

    def extract_raw_ts_3ch(self, fn):
        '''
        '''
        colNames = ['y0','y1', 'y2']
        return extract_raw_data(fn,colNames)

    def extract_raw_ts_1ch(self, fn):
        '''
        '''
        colNames = ['y0']
        return extract_raw_data(fn,colNames)


    ###########################################################################


    def template(self, x):
        '''
        '''
        xsc = 100.
        relsc = 100. / 7.
        phs = 0.4975
        if(x < 0.5):
            return 1 / (1 + math.exp(-xsc * relsc * (x - phs)))
        else:
            return math.exp(-xsc * (x - 0.499848))

    def filtertempl(self, x):
        '''
        '''
        return 1 - math.exp(-(10. * x))


    ###########################################################################


    def CR_combine(self, fnList, newfn):
        '''
        '''
        with open(newfn + '.dat','wb') as wfd:
            for f in fnList:
                with open(f,'rb') as fd:
                    shutil.copyfileobj(fd, wfd, 1024*1024*10)


    ###########################################################################


    def find_nearest(self, array, value):
        '''
        '''
        array = np.asarray(array)
        minarr = array - value
        idx = np.argmin(i for i in minarr if i > 0)
        idxx = (np.abs(array - value)).argmin()
        return array[idxx].tolist()

    def find_nearest_fix(self, array, value):
        '''
        '''
        array = np.asarray(array)
        minarr = array - value
        idx = np.argmin(i for i in minarr if i > 0)
        idxx = (np.abs(array - value)).argmin()
        return array[idx].tolist()

    def cra_analyze(self, d, squids, gains, biases, scantime, noisefilt = False, verbose=True, detrend=True, inv = False, pwrcnv = False, fit = True):
        '''
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # Parameter input explanations:
        # data: The name of the data file, up to the number. Should always end in "00x.txt", so this input is "dataname_" and the "00x.txt" is added to the string based on the 'sets' input
        # sets: A two value array of format [beginning data set, end data set]
        # SQs: Right now this is set up for three column inputs, so the inupt is of format [1,2,3] if the data was being taken with SQs 1, 2, and 3 for example
        # gain: An array of the channel gains used in the power conversion
        # bias: An array of biases used
        # scantime: Length of each data set in seconds
        # noisfilt: A work in progress function to remove certain noise components using a notch fitler applied to the power spectra
        # verbose: Outputs more information about jumped flux removal and eventually fits
        # detrend: Detrends each timestream
        # inv: Inverts the data. Right now we'll need to know before running if the peaks need to be inverted for this input. Will change this to detect automatically in the future.
        # pwrcnv: Converts y to units of power
        # fit: Option to fit the data
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        '''
        #Example parameter inputs: CR_analyze(["20210319_SQ1-contr1_SQ2-contr2_SQ6-contr3_biasthreeturnsintotrans_5-FTR-5min_Co60_"], [5,10], [1,2,6], [100.,100.,100.], [1.,1.,1.], 300., detrend=True, inv = True, pwrcnv = True)
        # note: will add input for number of channels in the future
        # Defining datasets to look at
        pl.clf()
        if False:
            datalist = []
            jfe_datasets = []
            if len(sets)==1:
                if sets[0] < 10:
                    dl = data[0] + "00" + str(sets[0]) + ".txt"
                if sets[0] >= 10 and sets[0] < 100:
                    dl = data[0] + "0" + str(sets[0]) + ".txt"
                if sets[0] >= 100:
                    dl = data[0] + str(sets[0]) + ".txt"
                datalist.append(dl)
            else:
                setnumb = len(range(sets[0], sets[1]+1))
                sn=[]
                for i in range(setnumb):
                    sn.append(sets[0]+i) # Make an array that starts with the first dataset number you input
                    if sn[i] < 10:
                        dl = data[0] + "00" + str(sn[i]) + ".txt"
                    if sn[i] >= 10 and i < 100:
                        dl = data[0] + "0" + str(sn[i]) + ".txt"
                    if sn[i] >= 100:
                        dl = data[0] + str(sn[i]) + ".txt"
                    datalist.append(dl)

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # Start of primary for loop
        #for i, channel in enumerate(d.keys()):
        #print(d[n])
        jfe_channels = [] #jumped flux events
        #d = extract_raw_ts_3ch(datalist[n])
        #loop for each channel in the data set
        ch = []
        dList0 = []
        ymeansub = []
        ymeansub_disc = []
        notchyms = []
        maxvalsy = []
        maxvalsx = []
        for j, squid in enumerate(squids):
            print()
            print(j, squid)
            dList0.append(d[str(j)]['ts'])
            #Assign SQ calibrations
            V2uA0 = self.squid_calibration_dict[squid]
            if pwrcnv:
                yList0 = (10**6)*(10**-5)*bias[j]*V2uA0*dList0[j]/gain[j]
            else:
                pprint(dList0)
                try:
                    yList0 = dList0[j]
                except IndexError:
                    import ipdb;ipdb.set_trace()

            # Define samplerate
            samplerate = len(yList0)/scantime
            # 'Normalize' x
            xList0 = range(0,len(yList0))
            xNorm0 = (scantime/len(xList0))
            xLn0 = []
            for i in range(len(xList0)):
                normd = xNorm0*xList0[i]
                xLn0.append(normd)
            #import ipdb;ipdb.set_trace()
            # # # # # # # # # # # # # # # # # # # #
            # Fixing jumped flux
            # Finding discontinuities 
            # # # # # # # # # # # # # # # # # # # #
            print()
            print()
            print()
            print()
            print()
            print(yList0)
            print(yList0)
            print(yList0)
            print(yList0)
            deryList0 = np.gradient(yList0) # Take the first derivative of the y-data
            discthresh = 10*np.std(deryList0) # Set the threshold for peakfinding, 10 standard deviations works well
            maxsx = []
            maxsy = []
            xdisc_N = []
            '''
            Jumped flux
            '''
            for i in range(len(yList0)):
                if abs(deryList0[i]) > discthresh and abs(np.mean(yList0[:i])-np.mean(yList0[i:])) > discthresh:
                    # Set the condition that the peaks found in the derivitive are above the descrimination threshold
                        # and also that the means of the data before and after the found peak are under a similar threshold.
                    # This distinguishes hits from jumped flux.
                    maxsx.append(xLn0[i])
                    maxsy.append(deryList0[i]) # Make a list of values above the threshold
            if len(maxsy) > 0: # If discontinuities are found 
                maxtime = maxsx[maxsy.index(max(maxsy))]
                roundedx = np.round(maxsx, 2) # Round the x values to find general locations
                xdisc = np.unique(roundedx) # Insert rounded x values into their own array, N_array = N_disc.
                roundxmain = np.array(np.round(xLn0, 2)) # Round all x data
                # Removing discontinuities
                remove = int(samplerate * 0.01) # Number of points to remove before and after disc location
                ind1 = []
                ind2 = []
                for i in range(len(xdisc)): # Loop over each found discontinuity
                    xdisc_N.append(np.where(roundxmain == xdisc[i])[0][0]) # Find index of x locations
                    if len(xdisc) == 1: # If there's only one discontinuity detected
                        ymeansub_disc.extend(yList0[:xdisc_N[i]] - np.mean(yList0[:xdisc_N[i]])) # Remove DC offset before disc.
                        ymeansub_disc.extend(yList0[xdisc_N[i]:] - np.mean(yList0[xdisc_N[i]:])) # Remove DC offset after disc.
                    else:
                        if i == 0: # Remove DC offset before first disc.
                            ymeansub_disc.extend(yList0[:xdisc_N[i]] - np.mean(yList0[:xdisc_N[i]]))
                        if i != len(xdisc)-1 and i != 0: # Remove DC offset after last disc., before next
                            ymeansub_disc.extend(yList0[xdisc_N[i-1]:xdisc_N[i]] - np.mean(yList0[xdisc_N[i-1]:xdisc_N[i]]))
                        if i == len(xdisc)-1: # Remove DC offset after the last disc.
                            ymeansub_disc.extend(yList0[xdisc_N[i-1]:xdisc_N[i]] - np.mean(yList0[xdisc_N[i-1]:xdisc_N[i]]))
                            ymeansub_disc.extend(yList0[xdisc_N[i]:] - np.mean(yList0[xdisc_N[i]:]))

                    # Replace datapoints where disc. occurs with mean values
                    ind1.append(xdisc_N[i]-remove)
                    ind2.append(xdisc_N[i]+remove)
                for i in range(len(ind1)):
                    ymeansub_disc[ind1[i]:ind2[i]] = [np.mean(ymeansub_disc)]*len(ymeansub_disc[ind1[i]:ind2[i]])
                yList0 = ymeansub_disc # Overwrite y data

            # Some print options for jumped flux info
            if verbose and False:
                if len(maxsy) == 0:
                    print("No jumped flux events found in channel %i, dataset "%j + datalist[n][-7:-3])
                    jfe_channels.extend([0])
                if len(maxsy) > 0:
                    if len(xdisc) == 1:
                        print("One jumped flux event found in channel %i, dataset "%j + datalist[n][-7:-3])
                        jfe_channels.extend([1])
                if len(maxsy) > 0:
                    if len(xdisc) > 1:
                        print("%i "%len(xdisc) + "jumped flux events found in channel %i, dataset "%j + datalist[n][-7:-3])
                        jfe_channels.extend([len(xdisc)])
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # Remaining dataset processing
            # Detrend sets with no jumped flux
            if detrend:
                yList0det = signal.detrend(yList0) #detrend raw data
            else:
                yList0det = yList0
            # Invert
            if inv:
                for i in range(len(yList0det)):
                    yList0det[i] = -1.*yList0det[i]
            # Remove DC offset
            if len(maxsy) == 0:
                ymeansub.append(yList0det - np.mean(yList0det))
            else:
                ymeansub.append(yList0det)
            pl.plot(xLn0, ymeansub[j])
            pl.show()

            '''
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # Noise filtering
            if noisefilt:
                fft_freq, fft_psd = signal.welch(ymeansub[j], samplerate)
                b, a = signal.iirnotch(215, 30, samplerate)
                notchymssub = signal.lfilter(b, a, ymeansub[j], axis=- 1, zi=None)
                notchyms.append(notchymssub)
                fft_freq2, fft_psd2 = signal.welch(notchyms[j], samplerate)
                pl.plot(fft_freq2, fft_psd2)
                pl.plot(fft_freq, fft_psd)
                pl.show()
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

            # Peak finder
            if fit:
                # Setup matched filter peak finder
                xmf = np.arange(0.4, 0.6, 0.0001) #define window/xaxis for convolving function
                ymf = []
                for k in range(len(xmf)):
                    ymf.append(template(xmf[k])) # Create matched filter convolving function

                #Convolve templates with data, take derivative to find rise location, find max
                pf = signal.fftconvolve(ymeansub[j], ymf, mode='same')
                fftpf = rfft(pf)
                yderiv = np.gradient(pf)
                yderivdetr = signal.detrend(yderiv)
                #ydstd = 0.02
                ydstd = 8*np.std(yderivdetr) # Seems to be a good threshold based on the noise of the data set and goodness of fits
                ydpks = []
                xydpks = []
                for i in range(len(yderiv)):
                    if yderivdetr[i] > ydstd:
                        ydpks.append(yderivdetr[i])
                        xydpks.append(xLn0[i])
                # Pick out max
                mvalsx = []
                mvalsy = []
                for i in range(len(ydpks)):
                    if (i+1) >= len(ydpks):
                        break
                    if (ydpks[i+1]<ydpks[i]) and (ydpks[i-1]<ydpks[i]):
                        mvalsy.append(ydpks[i])
                        mvalsx.append(xydpks[i])
                maxvalsx.append(mvalsx)
                maxvalsy.append(mvalsy)
                #rate = len(maxvalsy)/scantime
                #print(maxvalsx[j], maxvalsy[j])
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # Start fitting
            # Start fit for exponential tail
                # Define pulse windows
                if len(maxvalsx[j]) > 0:
                    fitlistsx = []
                    fitlistsx_sc = []
                    fitlistsy = []
                    datarange = int(0.05*samplerate) # Defines the window of each pulse fit
                    fitlistsx_re = []
                    fitlistsx_sc_re = []
                    fitlistsy_re = []
                    fitlistsx_p = []
                    fitlistsy_p = []
                    fitlistsx_sc_p = []
                    datarange_re = int(0.05*samplerate) # Defines the window of each pulse fit
                    datarange_p = int(0.004*samplerate)
                    def glitchfit(x, a, b, c): #defining a second degree polynomial to fit the event data in log space
                        return a*x + b + c*x*x
                    #datarange = int(0.015*samplerate) # Defines the window of each pulse fit
                    #datarange = int(0.035*samplerate)
                    #datarange_ext = int(0.04*samplerate)
                    #datarange_ext = int(0.1*samplerate)
                    for i in range(len(maxvalsx[j])):
                        fitlistx = []
                        fitlisty = []
                        fitlistx_sc = []
                        flaggedfits = []
                        taus = []
                        energies = []
                        threesigmas = []
                        fntointmods = []
                        phases = []
                        maxs = []
                        polyorder = 12
                        for l in range(datarange):
                            fitlistx.append(maxvalsx[j][i]+(float(l)/samplerate)) # For each event, add an x data point until the end of the defined window
                            fitlistx_sc.append(int(samplerate*maxvalsx[j][i])+(l)) # Do the same but in units of samples in order to define y-index
                            fitlisty = ymeansub[j][fitlistx_sc[0]:fitlistx_sc[-1]+1] # Define y window
                        fitlistsx.append(fitlistx)
                        fitlistsx_sc.append(fitlistx_sc)
                        fitlistsy.append(fitlisty)
                    # Start of fitter for exponential tail
                    # Here we will define the pulse window, then move to log space, fit a first degree polynomial, then convert back
                        phase = fitlistsx[i][np.argmax(fitlistsy[i])] # Defines the max of the y fit data's x location
                        fitlistx_chop = fitlistsx[i][np.argmax(fitlistsy[i]):] # Selecting only the tails for fitting in log space
                        fitlisty_chop = fitlistsy[i][np.argmax(fitlistsy[i]):]
                        # This chunk of code is to remove the negatives before going to log space
                        # I decided to remove the nans from log space in case it affected the fit later
                        #fitlisty_chop_zeros = np.where(fitlisty_chop > 0, fitlisty_chop, 0*-fitlisty_chop) # Setting all negative values to zero 
                        #fitlisty_chop_zeros_logic = np.logical_not(fitlisty_chop_zeros) # Logic array where 0 = True
                        #fitlisty_chop_nonzeros_logic = np.logical_not(fitlisty_chop_zeros_logic) # Inverse logic array
                        #fitlisty_chop_mod = fitlisty_chop[fitlisty_chop_nonzeros_logic] # Making array for interpolate function with zeros removed
                        #interp_y = np.interp(fitlisty_chop_zeros_logic.nonzero()[0], fitlisty_chop_nonzeros_logic.nonzero()[0], fitlisty_chop_mod) # Interpolating function
                        #fitlisty_chop[fitlisty_chop_zeros_logic] = interp_y # Setting the indexed values of the zero points to the interpolated function's values
                        np.seterr(invalid='ignore') # Ignore nan error from negative values in log
                        fitlistx_logchop = np.log(fitlistx_chop)  # Take the log of each event for fitting
                        fitlisty_logchop = np.log(fitlisty_chop)
                        # Remove nan values from the data and interpolate between them for fits
                        nan_indices = np.isnan(fitlisty_logchop) # Logic array where nan = True
                        real_indices = np.logical_not(nan_indices) # Inverse logic array
                        real_data = fitlisty_logchop[real_indices] # Making array for interpolate function with nans removed
                        interp_y = np.interp(nan_indices.nonzero()[0], real_indices.nonzero()[0], real_data) # Interpolate function
                        fitlisty_logchop[nan_indices] = interp_y # Setting the indexed values of the zero points to the interpolated function's values
                        #npts = 18
                        #npts = len(fitlistsx[i][:np.argmax(fitlistsy[i])]) # Set th number of points before the peak
                        #xlogfit = np.log(fitlistsx_chop)
                        # This is a seed fit to provide seed values for a higher order fit
                        coefs = poly.polyfit(fitlistx_logchop, fitlisty_logchop, 2) # Define a polynomial to fit the events in log space
                        #print(coefs) # Flag fits that have a positive slope
                        #if coefs[1] > 0:
                            #flaggedfits.append()
                            #continue
                        ffit = poly.polyval(fitlistx_logchop, coefs) # Creating the fit in log space
                        xfit = np.exp(fitlistx_logchop) # Convert back from log
                        ffitexp = np.exp(ffit)
                        # This is the primary fit (still in log space) that uses values from the seed fit for a more accurate fit
                        # Modeled with a second degree polynoial with seeds from the first degree fit in log space
                        # params, params_covariance = optimize.curve_fit(glitchfit, fitlistx_logchop, fitlisty_logchop, p0 = [coefs[1], coefs[0], -1.], bounds = ((-np.inf,-np.inf,-np.inf),(0.,np.inf,0.)))
                        # glitchfitlog = glitchfit(fitlistx_logchop, params[0], params[1], params[2])
                        # To 0th order correct fit overshoot at start of exp. curve
                        ffitexpmod = []
                        for k in range(len(ffitexp)):
                            if ffitexp[k] > np.max(fitlistsy[i]):
                                ffitexpmod.append(np.max(fitlistsy[i]))
                            else:
                                ffitexpmod.append(ffitexp[k])
                        #pl.figure(1)
                        #pl.plot(fitlistx_logchop, fitlisty_logchop)
                        #pl.plot(fitlistx_logchop, ffit)
                        #pl.show()
            # Start fit for rising edge
                # Define pulse windows, '_re' = 'rising edge'
                    fitlistx_re = []
                    fitlisty_re = []
                    fitlistx_sc_re = []
                    xshift = 50
                    for l in range(datarange_re):
                        fitlistx_re.append(maxvalsx[j][i] + (float(l)/samplerate) - (xshift/samplerate)) # For each event, subtract an x data point until the end of the defined window. Adding more points at the beginning to catch rising edge
                        fitlistx_sc_re.append(int(samplerate*maxvalsx[j][i])+(l) - xshift) # Do the same but in units of samples in order to define y-index
                        fitlisty_re = ymeansub[j][fitlistx_sc_re[0]:fitlistx_sc_re[-1]+1] # Define y window
                        #print(fitlistx_sc_re[0])
                        #print(fitlistx_sc_re[-1]+1)
                        fitlistsx_re.append(fitlistx_re)
                        fitlistsx_sc_re.append(fitlistx_sc_re)
                        fitlistsy_re.append(fitlisty_re)
                        #pl.plot(fitlistsx_re[i],fitlistsy_re[i])
                        #pl.show()
                        # Start of fitter for rising edge
                        # Here we'll define the rising edge's window and fit a line to it without going into log space
                        phase = fitlistsx_re[i][np.argmax(fitlistsy_re[i])] # Defines the max of the y fit data's x location
                        fitlistx_re_chop = fitlistsx_re[i][:np.argmax(fitlistsy_re[i])] # Selecting only the rising edges
                        fitlisty_re_chop = fitlistsy_re[i][:np.argmax(fitlistsy_re[i])]
                        meany = []
                        fitlisty_re_chop_temp = []
                        for l in range(len(fitlistx_re_chop)):
                            if (l+1) >= len(fitlistx_re_chop):
                                break
                            #print("check")
                            fitlisty_re_chop_temp.append(fitlisty_re_chop[l])
                            meany = 0.
                            meanystd = 0.
                            meany = np.mean(fitlisty_re_chop_temp)
                            meanystd = np.std(fitlisty_re_chop_temp)
                            #print(meanys, meanystd)
                            #print(fitlisty_re_chop[l] - meany, meanystd)
                            if l > 15 and fitlisty_re_chop[l] - meany > 2*meanystd:
                                rise_index = l - int(samplerate/5000)
                                #print(rise_index)
                                #print("rise is at %f"%fitlistx_re_chop[l])
                                break
                        fitlistx_re_fit = fitlistx_re_chop[rise_index:]
                        fitlisty_re_fit = fitlisty_re_chop[rise_index:]
                        index_last = rise_index + len(ffitexp)
                        totalfitx = fitlistx_re[rise_index:index_last]
                        totalfity = fitlisty_re[rise_index:index_last]
                        coefs_re = poly.polyfit(fitlistx_re_fit, fitlisty_re_fit, 2)#polyorder) # Define a first degree polynomial to fit the events
                        #print(coefs_re) # Flag fits that have a negative slope
                        #if coefs_re[1] < 0:
                            #flaggedfits.append()
                            #continue
                        ffit_re = poly.polyval(fitlistx_re_fit, coefs_re) # Creating the fit
            # Start fit for the peak
                    # Define pulse windows, 'p' = 'peak'
                        fitlistx_p = []
                        fitlisty_p = []
                        fitlistx_sc_p = []
                        xshift_p = -8
                        for l in range(datarange_p):
                            fitlistx_p.append(maxvalsx[j][i] + (float(l)/samplerate) - (xshift_p/samplerate)) # For each event, subtract an x data point until the end of the defined window. Adding more points at the beginning to catch rising edge
                            fitlistx_sc_p.append(int(samplerate*maxvalsx[j][i])+(l) - xshift_p) # Do the same but in units of samples in order to define y-index
                            fitlisty_p = ymeansub[j][fitlistx_sc_p[0]:fitlistx_sc_p[-1]+1] # Define y window
                        #print(fitlistx_sc_p[0])
                        #print(fitlistx_sc_p[-1]+1)
                        fitlistsx_p.append(fitlistx_p)
                        fitlistsx_sc_p.append(fitlistx_sc_p)
                        fitlistsy_p.append(fitlisty_p)
                        coefs_p = poly.polyfit(fitlistx_p, fitlisty_p, 2) # Define a second degree polynomial to fit the events
                        coeffs_lag_p = np.polynomial.laguerre.Laguerre.fit(fitlistx_p, fitlisty_p, 3)
                        ffit_lag_p = np.polynomial.laguerre.lagval(fitlistx_p, coeffs_lag_p.convert().coef)
                        #print(coefs_re) # Flag fits that have a negative slope
                        #if coefs_re[1] < 0:
                            #flaggedfits.append()
                            #continue
                        ffit_p = poly.polyval(fitlistx_p, coefs_p) # Creating the fit
                        ########################################################
                        index_last = rise_index + len(ffitexp)
                        totalfitx = fitlistx_re[rise_index:index_last]
                        totalfity = fitlisty_re[rise_index:index_last]
                        phase_index = np.argmax(totalfity)
                        totalfitx_re = totalfitx[:phase_index]
                        totalfitx_exp = totalfitx[phase_index:]
                        alpha1 = 100*len(totalfitx)
                        alpha2 = 5*len(totalfitx)
                        alpha3 = 10*len(totalfitx)
                        phase1 = fitlistsx_re[i][np.argmax(fitlistsy_re[i])-5]
                        phase2 = fitlistsx_re[i][np.argmax(fitlistsy_re[i])+0]
                        function1 = []
                        function2 = []
                        function3 = []
                        #print("test")
                        ffitexp_total = np.exp(poly.polyval(np.log(totalfitx), coefs))
                        ffit_p_total = poly.polyval(totalfitx, coefs_p)
                        ffitexp_totalmod = []
                        ffit_re_total = poly.polyval(totalfitx, coefs_re)
                        for k in range(len(ffitexp_total)):
                            if ffitexp_total[k] > np.max(fitlistsy[i]):
                                ffitexp_totalmod.append(np.max(fitlistsy[i]))
                            else:
                                ffitexp_totalmod.append(ffitexp_total[k])
                        #print(len(ffitexp_total, ffitexp_total))
                        ffit_re_total = poly.polyval(totalfitx, coefs_re)
                        ffitexp_total[:phase_index+3] = np.max(fitlistsy[i])
                        ffit_re_total[phase_index-3:] = np.max(fitlistsy[i])
                        #xx = np.linspace(-1, 1, len(totalfitx))
                        xx = np.linspace(totalfitx[0], totalfitx[-1], len(totalfitx))
                        sigma1 = 1/(1+np.exp((-xx+phase1)*alpha1))
                        sigma2 = 1/(1+np.exp((-xx+phase2)*alpha2))
                        sigma3 = 1/(1+np.exp((-xx+phase)*alpha3))
                        for l in range(len(totalfitx)): 
                            function1.append((1 - sigma1[l]) * ffit_re_total[l]+sigma1[l] * ffit_p_total[l])
                            function2.append((1 - sigma2[l]) * ffit_p_total[l]+sigma2[l] * ffitexp_totalmod[l])
                            function3.append((1 - sigma1[l]) * ffit_re_total[l] +sigma1[l] * function2[l])
                        pl.plot(totalfitx, totalfity)
                        #pl.plot(totalfitx, sigma1, 'g')
                        #pl.plot(fitlistx_p, ffit_p, 'g')
                        #print(ffit_lag_p)
                        #pl.plot(fitlistx_p, ffit_lag_p, 'r')
                        #pl.plot(fitlistx_p, ffit_lag_p, 'r')
                        #pl.plot(fitlistx_re_fit, ffit_re, 'r')
                        #pl.plot(xfit, ffitexp, 'r')
                        pl.plot(totalfitx, function3, 'r')
                        #pl.plot(totalfitx, ffitexp_totalmod, 'g')
                        #pl.plot(totalfitx[:np.argmax(function1)+10], function1[:np.argmax(function1)+10], 'r')
                        pl.plot(totalfitx[np.argmax(function2)], function2[np.argmax(function2)], 'o')
                        #pl.plot(totalfitx, ffit_re_total, 'r')
                        #pl.plot(totalfitx, function, 'g')
                        #pl.plot(xfit, ffitexp, 'r')
                        #pl.plot(fitlistx_re_fit, ffit_re, 'r')
                        #pl.plot(xfit, ffitexpmod, color='red')
                        pl.show()

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Plotting

		pl.xlabel("Time (s)")
		pl.ylabel("Energy (keV)")
		pl.plot(xLn0, ymeansub[j])
		jfe_datasets.append(jfe_channels)
    pl.show()
    print(jfe_datasets)
    TRE = np.sum(jfe_datasets)
    print("Total rejected events = %i"%TRE)
    print("Rate with hits rejected = ")
    print("Rate without hits rejected = ")
'''
