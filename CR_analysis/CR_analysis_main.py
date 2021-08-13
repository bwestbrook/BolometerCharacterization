'''

Standalone script - v 1.0.1
08/13/2021
Shawn Beckman

'''




#!/usr/bin/env python
# coding: utf-8

# In[16]:


print('Cosmic Ray Analysis Code by Shawn - main function outline:', end = '\n 1 ')
print('Import data file', end = '\n 2 ')
print('Modify data - rescale, detrend, remove re-zeros, etc.', end = '\n 3 ')
print('Matched filter peak finder', end = '\n 4 ')
print('Initial analysis tools - spectrum analyzer, etc.', end = '\n 5 ')
print('Fitter and fit rejection', end = '\n 6 ')
print('Coincidence analysis', end = '\n 7 ')
print('Plot')


# In[17]:


print('Imports')
import matplotlib
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
from scipy.optimize import curve_fit
import scipy.integrate as integrate
import matplotlib.colors as colors
import matplotlib.ticker as ticker
import shutil
import statistics
from statistics import median_low
from matplotlib import cm
from matplotlib import mlab
from math import exp, expm1
import sys
import bisect
import os
import gc
import pickle


# In[18]:


print('Defining things')
V2uA_SQ1 = 25.2 #define SQUID calibrations in uA/V
V2uA_SQ2 = 25.2
V2uA_SQ3 = 30.0
V2uA_SQ4 = 30.0
V2uA_SQ5 = 25.9
V2uA_SQ6 = 25.2

xaxes = []
ymeansubs = []
timeconsts = []
energyhists = []
rates = []
allphases = []
maxvalsxs = []
maxvalsys = []


# In[19]:


print('Supporting functions')

def extract_raw_data(fn,colNames):
    '''
    Extract txt data from a txt file fn and return
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


def extract_raw_ts(fn):
    '''
    Extract XY data from a txt file fn and
    return a Python dictionary with entries x and y.

    d['filename'] returns the filename.
    '''
    
    colNames = ['y0','y1','y2','y3','y4','y5','y6','y7']
    #colNames = ['y0','y1']
    return extract_raw_data(fn,colNames)

def extract_raw_ts_3ch(fn):
    colNames = ['y0','y1', 'y2']
    return extract_raw_data(fn,colNames)

def extract_raw_ts_1ch(fn):
    colNames = ['y0']
    return extract_raw_data(fn,colNames)


###########################################################################

# Template function for the matched filter peak finder

def template(x):
    xsc = 100.
    relsc = 100./7.
    phs = 0.4975
    if(x<0.5): 
        return 1/(1+math.exp(-xsc*relsc*(x-phs)))
    else:
        return math.exp(-xsc*(x-0.499848))

def filtertempl(x):
    return 1 - math.exp(-(10.*x))


###########################################################################

# Function to combine two data sets (legacy)

def CR_combine(fnList,newfn):
    with open(newfn + '.dat','wb') as wfd:
        for f in fnList:
            with open(f,'rb') as fd:
                shutil.copyfileobj(fd, wfd, 1024*1024*10)


###########################################################################

# Functions to find the closest value to a specified value in an array

def find_nearest(array, value):
    array = np.asarray(array)
    minarr = array - value
    idx = np.argmin(i for i in minarr if i > 0)
    idxx = (np.abs(array - value)).argmin()

    return array[idxx].tolist()

def find_nearest_fix(array, value):
    array = np.asarray(array)
    minarr = array - value
    idx = np.argmin(i for i in minarr if i > 0)
    idxx = (np.abs(array - value)).argmin()

    return array[idx].tolist()


# In[20]:


print('Start of the primary function')


def CR_analyze(data, sets, SQs, gain, bias, scantime, inv, pklsuffix, savefits = True, savefigs = True, showfits=False,                fluxfix = True, noisefilt = False, coincidence = False, verbose=True, detrend=True, pwrcnv = False, fit = True):


    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    '''
    
    Parameter input explanations:
    
    data: The name of the data file, up to the number. Should always end in "00x.txt", so this input is "dataname_" and the "00x.txt" is added to the string based on the 'sets' input
    sets: A two value array of format [beginning data set, end data set]
    SQs: Right now this is set up for three column inputs, so the inupt is of format [1,2,3] if the data was being taken with SQs 1, 2, and 3 for example
    gain: An array of the channel gains used in the power conversion
    bias: An array of biases used
    scantime: Length of each data set in seconds
    inv: An array to invert each channel or not
    plksuffix: Suffix used to name the pickle files, plot titles, etc. Should describe exactly what you're running
    savefits: Saves pngs of each fit to a new directory
    savefigs: Saves energy and time constant histograms, as well as text files of relevant run info
    showfits: Shows each pulse fit in real time
    fluxfix: Overwrites timestreams with fixed jumped flux events
    noisefilt: A work in progress function to remove certain noise components using a notch fitler applied to the power spectra
    coincidence: Looks at coincidence events and prints out a pickle file with relevant info
    verbose: Outputs more information about jumped flux removal and eventually fits
    detrend: Detrends each timestream
    inv: Inverts the data. Right now we'll need to know before running if the peaks need to be inverted for this input. Will change this to detect automatically in the future.
    pwrcnv: Converts y to units of power
    fit: Option to fit the data
    
 

    #Example parameter inputs: 
        # CR_analyze(["/Users/shawn/Google Drive/My Drive/Python/Cosmic Rays/2021_05_16-control_nosource/CR_Scan_002/_"], \
              # [2,259], [1,2,6], [100.,100.,100.], [3.457,3.187,3.165], 300., [False, False, True], ["20210516_controlbolos_nosource_2-256"], \
              # showfits=False, noisefilt=False, verbose = False, fit = True, pwrcnv = True)

    
    # note: will add input for number of channels in the future
   
   '''
    

   
    pl.clf()
    datalist = []
    jfe_datasets = []
    energies = [[],[],[]]
    energies_data = [[],[],[]]
    energies_nojfes = [[],[],[]]
    timeconsts = [[],[],[]]
    rates = [[],[],[]]
    peakvals = [[],[],[]]
    errors = []
    e_tot = [] #[[datalists][channels][energies]]
    tau_tot = [] #[[datalists][channels][tau]]
    rt_tot = [] #[[datalists][channels][risetimes]]
    coinc_tot = [] #[[datalists][x value]
    
    
    # Defining the string to find the correct data set based on function inputs
    
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
            e_tot.append(sn[i]) # Count up from first dataset
            tau_tot.append(sn[i])
            rt_tot.append(sn[i])
            coinc_tot.append(sn[i])
            
    # Defining the directory
    numslashes = 9
    slashes = []
    for i in range(len(data[0])):
        if data[0][i] =='/':
            slashes.append(0)
        if len(slashes) == numslashes:
            writepath = data[0][:i+1]
            break
    wpsuffix = pklsuffix[0]
            
     
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    
    # Start of primary for loop
    
    for n in range(len(datalist)): 
        if verbose:
            print(datalist[n])   
        print("running data set", datalist[n][-7:-4])
        dList0 = []
        jfe_channels = [] #jumped flux events
        
        
        d = extract_raw_ts_3ch(datalist[n])
        dList0.append(d)
        ch = []
        ymeansub = [] # main y data
        
        notchyms = []
        maxvalsy = []
        maxvalsx = []
    
        # Telling the code which SQUIDs you're using
        for j in range(len(SQs)): 
            ymeansub_disc = []
            c = "y"+ str(j)
            ch.append(c)
            print("channel", SQs[j])
        
            #Assign SQ calibrations
            
            if SQs[j]==1:
                V2uA0 = V2uA_SQ1
            else:
                if SQs[j]==2:
                    V2uA0 = V2uA_SQ2
                else:
                    if SQs[j]==3:
                        V2uA0 = V2uA_SQ3
                    else:
                        if SQs[j]==4:
                            V2uA0 = V2uA_SQ4
                        else:
                            if SQs[j]==5:
                                V2uA0 = V2uA_SQ5
                            else:
                                if SQs[j]==6:
                                    V2uA0 = V2uA_SQ6
            
           
            # Defining the y-scale
            if pwrcnv:
                yList0 = (10**6)*(10**-5)*bias[j]*V2uA0*dList0[0][ch[j]]/gain[j] 
            else:
                yList0 = dList0[0][ch[j]]    

            # Define samplerate in Hz
            samplerate = len(yList0)/scantime
            
            # 'Normalize' x
            xList0 = range(0,len(yList0))
            xNorm0 = (scantime/len(xList0))
            xLn0 = []
            for i in range(len(xList0)):
                normd = xNorm0*xList0[i]
                xLn0.append(normd)

                
                
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            
            
    # Fixing jumped flux
            
            # Finding discontinuities 
            deryList0 = np.gradient(yList0) # Take the first derivative of the y-data
            discthresh = 50*np.std(deryList0) # Set the threshold for peakfinding, 50 standard deviations works well
            
            maxsx = []
            maxsy = []
            xdisc_N = []
            
            # This is the condition for finding the JFEs - if the data point is above the threshold value AND the 
            # difference in the mean of the 500 points before and after the event is also above the threshold
            
            for i in range(len(yList0)):
                if abs(deryList0[i]) > discthresh and abs(np.mean(yList0[i - int(samplerate*0.1):i])-np.mean(yList0[i:i + int(samplerate*0.1)])) > discthresh:
                    maxsx.append(xLn0[i])
                    maxsy.append(deryList0[i]) # Make a list of values above the threshold
            
            if len(maxsy) > 0: # If discontinuities are found 
                
                # Finding the x location of the discontinuity
                maxtime = maxsx[maxsy.index(max(maxsy))] # Find the x location of the max value
                roundedx = np.round(maxsx, 2) # Round the x values to find general locations
                xdisc = np.unique(roundedx) # Insert rounded x values into their own array, N_array = N_disc.
                roundxmain = np.array(np.round(xLn0, 2)) # Round all x data
                
                
                # Removing discontinuities
                remove = int(samplerate * 0.015) # Number of points to remove before disc location
                remove_last = int(samplerate * 0.01) # Number of point to remove after disc location. Charactaristic of most jumped flux recover times - would like to make mroe robust in the future
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
                    ind2.append(xdisc_N[i]+remove_last)
                
                for i in range(len(ind1)):
                    ymeansub_disc[ind1[i]:ind2[i]] = [np.mean(ymeansub_disc)]*len(ymeansub_disc[ind1[i]:ind2[i]])
                if fluxfix:
                    yList0 = ymeansub_disc # Overwrite y data
                
            
            # Some print options for jumped flux info
            # These lines also append the JFE ararys
            
            if verbose: 
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
            else:
                if len(maxsy) == 0:
                    jfe_channels.extend([0])
                if len(maxsy) > 0:
                    if len(xdisc) >= 1:
                        jfe_channels.extend([len(xdisc)])
                        
                      
            
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

            
    # Remaining dataset processing
        
            # Detrend data
            
            if detrend:
                yList0det = signal.detrend(yList0) #detrend raw data
            else:
                yList0det = yList0
            
            # Invert
            if inv[j]:
                for i in range(len(yList0det)):
                    yList0det[i] = -1.*yList0det[i]

            # First DC offset removal before finding noise threshold
           
            if len(maxsy) == 0:
                ymeansub.append(yList0det - np.mean(yList0det))
            else:
                ymeansub.append(yList0det)
            
                      
      
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    
    # Noise filtering code - not complete
    # This code defines a notch filter to remove certain parts of the noise spectra
    # Additions need to be made to output noise value from welch
            
            if noisefilt:
                fft_freq, fft_psd = signal.welch(ymeansub[j], samplerate)
                b, a = signal.iirnotch(215, 30, samplerate)
                notchymssub = signal.lfilter(b, a, ymeansub[j], axis=- 1, zi=None)

                
                hpfilt100 = signal.butter(1, 100, 'hp', output = 'sos', fs=5000)
                filtered100 = signal.sosfilt(hpfilt100, ymeansub[j])
                
                hpfilt20 = signal.butter(1, 20, 'hp', output = 'sos', fs=5000)
                filtered20 = signal.sosfilt(hpfilt20, ymeansub[j])
                filtered20_0_float = signal.sosfilt(hpfilt20, ymeansub[j])
                filtered20_1_HS = signal.sosfilt(hpfilt20, ymeansub[j])
                filtered20_0_float_source = signal.sosfilt(hpfilt20, ymeansub[j])
                filtered20_1_HS_source = signal.sosfilt(hpfilt20, ymeansub[j])
        
               
                if n==0 and j == 0:
                    filtered20_0_ns = signal.sosfilt(hpfilt20, ymeansub[j])
                
                if n==0 and j == 1:
                    filtered20_1_ns = signal.sosfilt(hpfilt20, ymeansub[j])
                    
                if n==0 and j == 2:
                    filtered20_2_ns = signal.sosfilt(hpfilt20, ymeansub[j])
                    
                if n==1 and j == 0:
                    filtered20_0_s = signal.sosfilt(hpfilt20, ymeansub[j])
                
                if n==1 and j == 1:
                    filtered20_1_s = signal.sosfilt(hpfilt20, ymeansub[j])
                    
                if n==1 and j == 2:
                    filtered20_2_s = signal.sosfilt(hpfilt20, ymeansub[j])
                
                notchyms.append(notchymssub)
                fft_freq2, fft_psd2 = signal.welch(notchyms[j], samplerate)
                
            
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        
    # Peak finder
            
            if fit:
                # Setup matched filter peak finder
                xmf = np.arange(0.4, 0.6, 0.0001) #define window/xaxis for convolving function
                ymf = []
                for k in range(len(xmf)):
                    ymf.append(template(xmf[k])) # Create matched filter convolving function

                # Convolve templates with data, take derivative to find rise location, find max
                pf = signal.fftconvolve(ymeansub[j], ymf, mode='same')
                fftpf = rfft(pf)
                yderiv = np.gradient(pf)
                yderivdetr = signal.detrend(yderiv)
                peakthresh = 8.0
                ydstd = peakthresh*np.std(yderivdetr) # Seems to be a good threshold based on the noise of the data set and goodness of fits
                ydpks = []
                xydpks = []
                yderivdetr_temp = []
                ymeansub_temp = []
                indextemp = []
               
                # Removing peaks from timestreams to get an accurate std of the noise
                for i in range(len(yderiv)):
                    
                    if i>25 and 0.75*yderivdetr[i-25] > ydstd or yderivdetr[i-25] < -0.75*ydstd: #numbers tweaked to optimize peak removal
                        yderivdetr_temp.append(0)
                        ymeansub_temp.append(0) # Defining the 'temporary' y array to grab the standard deviation from
                        indextemp.append(i)
                        
                    else:
                        yderivdetr_temp.append(yderivdetr[i])
                        ymeansub_temp.append(ymeansub[j][i])
                
                stddata = 3*np.std(ymeansub_temp) #3 times the standard deviation
                ydstdtemp = []
                stdtemp = []
                
                # Finding peaks using new std      
                for i in range(len(yderiv)):
                    ydstdtemp.append(ydstd)
                    stdtemp.append(stddata)
                    if yderivdetr[i] > stddata:
                        ydpks.append(yderivdetr[i])
                        xydpks.append(xLn0[i])
                        
                        
                # Final DC offset removal using peak-removed data
                ymeansub[j] = ymeansub[j] - np.mean(ymeansub_temp)
                
               
                # Pick out max
                mvalsx_init = []
                mvalsy_init = []
                mvalsx = []
                mvalsy = []
                for i in range(len(ydpks)):
                    if (i+1) >= len(ydpks):
                        break
                    
                    if (ydpks[i+1]<ydpks[i]) and (ydpks[i-1]<ydpks[i]):
                        mvalsy_init.append(ydpks[i])
                        mvalsx_init.append(xydpks[i])
               
                
                # remove duplicate peaks that occur within 5 ms of each other
                for i in range(len(mvalsx_init)):
                    if (i+1) >= len(mvalsx_init):
                        mvalsx.append(mvalsx_init[i])
                        mvalsy.append(mvalsy_init[i])
                        break
                    if mvalsx_init[i+1] - mvalsx_init[i] > 0.005:
                        mvalsx.append(mvalsx_init[i])
                        mvalsy.append(mvalsy_init[i])
                
                
                maxvalsx.append(mvalsx)
                maxvalsy.append(mvalsy)
                
                
                if len(maxvalsx[j]) > 0:
                    rates[j].append(len(maxvalsx[j]))
                else:
                    rates[j].append(0)
                    
                    
                
                
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    
    # Start fitting 
    # Fits pulses in three sections: Exponential tail, rising edge, and peak, the combines the three fits
    
                
                if len(maxvalsx[j]) > 0:
                    
                    fitlistsx = []
                    fitlistsx_sc = []
                    fitlistsy = []
                    datarange = int(0.02*samplerate) # Used to define sample window
                    fitlistsx_re = []
                    fitlistsx_sc_re = []
                    fitlistsy_re = []
                    fitlistsx_p = []
                    fitlistsy_p = []
                    fitlistsx_sc_p = []
                    datarange_re = int(0.1*samplerate) 
                    datarange_p = int(0.005*samplerate)
                    
                    def glitchfit(x, a, b): #defining a second degree polynomial to fit the event data in log space
                        return a + x**b
                    
                    
                    for i in range(len(maxvalsx[j])):
                        
                        fitlistx = []
                        fitlisty = []
                        fitlistx_sc = []
                        flaggedfits = []
                        threesigmas = []
                        fntointmods = []
                        phases = []
                        maxs = []
                        polyorder = 12
      
                    # Defining pulse windows
        
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
                        
                        np.seterr(invalid='ignore') # Ignore nan error from negative values in log
                        fitlistx_logchop = np.log(fitlistx_chop)  # Take the log of each event for fitting
                        fitlisty_logchop = np.log(fitlisty_chop)
                        
                        # Remove nan values from the data and interpolate between them for fits
                        nan_indices = np.isnan(fitlisty_logchop) # Logic array where nan = True
                        real_indices = np.logical_not(nan_indices) # Inverse logic array
                        real_data = fitlisty_logchop[real_indices] # Making array for interpolate function with nans removed
                        if len(real_data) == 0:
                            print("error in fit, moving to next")
                            errors.append(1)
                            break
                        
                        interp_y = np.interp(nan_indices.nonzero()[0], real_indices.nonzero()[0], real_data) # Interpolate function
                        fitlisty_logchop[nan_indices] = interp_y # Setting the indexed values of the zero points to the interpolated function's values
            
                        
                        # This is a seed fit to provide seed values for a higher order fit
                        coefs = poly.polyfit(fitlistx_logchop, fitlisty_logchop, 2) # Define a polynomial to fit the events in log space
                        ffit = poly.polyval(fitlistx_logchop, coefs) # Creating the fit in log space
                        xfit = np.exp(fitlistx_logchop) # Convert back from log
                        ffitexp = np.exp(ffit)
                        
                        # To 0th order correct fit overshoot at start of exp. curve
                        ffitexpmod = []
                        for k in range(len(ffitexp)):
                            if ffitexp[k] > np.max(fitlistsy[i]):
                                ffitexpmod.append(np.max(fitlistsy[i]))
                            else:
                                ffitexpmod.append(ffitexp[k])
                                
            
    
        # Start fit for rising edge
        
                    # Define pulse windows, '_re' = 'rising edge'
                    
                        fitlistx_re = []
                        fitlisty_re = []
                        fitlistx_sc_re = []
                        xshift = 10
                        for l in range(datarange_re):
                            fitlistx_re.append(maxvalsx[j][i] + (float(l)/samplerate) - (xshift/samplerate)) # For each event, subtract an x data point until the end of the defined window. Adding more points at the beginning to catch rising edge
                            fitlistx_sc_re.append(int(samplerate*maxvalsx[j][i])+(l) - xshift) # Do the same but in units of samples in order to define y-index
                            fitlisty_re = ymeansub[j][fitlistx_sc_re[0]:fitlistx_sc_re[-1]+1] # Define y window

                        fitlistsx_re.append(fitlistx_re)
                        fitlistsx_sc_re.append(fitlistx_sc_re)
                        fitlistsy_re.append(fitlisty_re)

                        
                        # Start of fitter for rising edge
                        # Here we'll define the rising edge's window and fit a line to it without going into log space
                        
                        if len(fitlistsy_re[i]) == 0: # Accounts for error in very few data sets where fitlistys_re[i] is not populated
                            print("defined window invalid (line 676)")
                            errors.append(1)
                            continue
                        
                        phase = fitlistsx_re[i][np.argmax(fitlistsy_re[i])] # Defines the max of the y fit data's x location
                        
                        fitlistx_re_chop = fitlistsx_re[i][:np.argmax(fitlistsy_re[i])] # Selecting only the rising edges
                        fitlisty_re_chop = fitlistsy_re[i][:np.argmax(fitlistsy_re[i])]
                        
                        startrise = []
                        meany = []
                        fitlisty_re_chop_temp = []
                        for l in range(len(fitlistx_re_chop)):
                            if (l+1) >= len(fitlistx_re_chop):
                                break
                            
                            fitlisty_re_chop_temp.append(fitlisty_re_chop[l])
                            meany = 0.
                            meanystd = 0.
                            meany = np.mean(fitlisty_re_chop_temp)
                            meanystd = np.std(fitlisty_re_chop_temp)
                           
                            if l > 5 and fitlisty_re_chop[l] - meany > 2*meanystd: # Get data for a few points first, then look to see if the difference from the current point to the mean is larger than 2x the standard deviation of the points 
                                rise_index = l - int(samplerate/5000)
                                break
                            else:
                                rise_index = 0
                        
                        if rise_index == 0: #if it can't find the rising edge, lower the threshold
                            for l in range(len(fitlistx_re_chop)):
                                if (l+1) >= len(fitlistx_re_chop):
                                    break
                                if l > 5 and fitlisty_re_chop[l] - meany > 1.5*meanystd: # Get data for a few points first, then look to see if the difference from the current point to the mean is larger than 2x the standard deviation of the points 
                                    rise_index = l - int(samplerate/5000)
                                    break
                        
                        fitlistx_re_fit = fitlistx_re_chop[rise_index:]
                        fitlisty_re_fit = fitlisty_re_chop[rise_index:]
                        
                        index_last = rise_index + len(ffitexp)
                        totalfitx = fitlistx_re[rise_index:index_last]
                        totalfity = fitlisty_re[rise_index:index_last]
                        
                        coefs_re = poly.polyfit(fitlistx_re_fit, fitlisty_re_fit, 3) #polyorder) # Define a second degree polynomial to fit the events
                        ffit_re = poly.polyval(fitlistx_re_fit, coefs_re) # Creating the fit
                        
                    
 
                        
            # Start fit for the peak
        
                    # Define pulse windows, 'p' = 'peak'
                    
                    
                        fitlistx_p = []
                        fitlisty_p = []
                        fitlistx_sc_p = []
                        xshift_p = -5
                        for l in range(datarange_p):
                            fitlistx_p.append(maxvalsx[j][i] + (float(l)/samplerate) - (xshift_p/samplerate)) # For each event, subtract an x data point until the end of the defined window. Adding more points at the beginning to catch rising edge
                            fitlistx_sc_p.append(int(samplerate*maxvalsx[j][i])+(l) - xshift_p) # Do the same but in units of samples in order to define y-index
                            fitlisty_p = ymeansub[j][fitlistx_sc_p[0]:fitlistx_sc_p[-1]+1] # Define y window

                        fitlistsx_p.append(fitlistx_p)
                        fitlistsx_sc_p.append(fitlistx_sc_p)
                        fitlistsy_p.append(fitlisty_p)

                        coefs_p = poly.polyfit(fitlistx_p, fitlisty_p, 10) # Define a second degree polynomial to fit the events
              

                        ffit_p = poly.polyval(fitlistx_p, coefs_p) # Creating the fit
                        
                        ########################################################
   
            # Combine the three fit functions

                        # Setting up parameters and windows for combine funcitons
        
                        index_last = rise_index + len(ffitexp) + 100
                        totalfitx = fitlistx_re[rise_index:index_last]
                        totalfity = fitlisty_re[rise_index:index_last]
                        phase_index = np.argmax(totalfity)
                        totalfitx_re = totalfitx[:phase_index]
                        totalfitx_exp = totalfitx[phase_index:]
                        
                        alpha1 = 100*len(totalfitx)
                        alpha2 = 5*len(totalfitx)
                        alpha3 = 10*len(totalfitx)
                        phase1 = fitlistsx_re[i][np.argmax(fitlistsy_re[i])-10]
                        phase2 = fitlistsx_re[i][np.argmax(fitlistsy_re[i])+0]
                        phase3 = fitlistsx_re[i][np.argmax(fitlistsy_re[i])-10]
                        function1 = []
                        function2 = []
                        function3 = []
                        
                        
                        ffitexp_total = np.exp(poly.polyval(np.log(totalfitx), coefs))
                        ffit_p_total = poly.polyval(totalfitx, coefs_p)
                        ffitexp_totalmod = []
                        ffit_re_total = poly.polyval(totalfitx, coefs_re)
                        
                        # This loop is to fix the issue of the start of the exponential fits going way above the peak in the data
                        for k in range(len(ffitexp_total)):
                            if ffitexp_total[k] > np.max(fitlistsy[i]):
                                ffitexp_totalmod.append(np.max(fitlistsy[i]))
                            else:
                                ffitexp_totalmod.append(ffitexp_total[k])
 
                        ffit_re_total = poly.polyval(totalfitx, coefs_re)
                        ffitexp_total[:phase_index+3] = np.max(fitlistsy[i])
                        ffit_re_total[phase_index-3:] = np.max(fitlistsy[i])
                        
                        # Creating the functions to define the combined function (funciton3)
                        xx = np.linspace(totalfitx[0], totalfitx[-1], len(totalfitx))
                        sigma1 = 1/(1+np.exp((-xx+phase1)*alpha1))
                        sigma2 = 1/(1+np.exp((-xx+phase2)*alpha2))
                        sigma3 = 1/(1+np.exp((-xx+phase3)*alpha3))
                        for l in range(len(totalfitx)): 
                            function1.append((1 - sigma1[l]) * ffit_re_total[l]+sigma1[l] * ffit_p_total[l])
                            function2.append((1 - sigma2[l]) * ffit_p_total[l]+sigma2[l] * ffitexp_totalmod[l])
                            function3.append((1 - sigma3[l]) * ffit_re_total[l] +sigma3[l] * function2[l])
                        
                        #Record all values for histogramming
                        energies[j].append(sum(function3))
                        energies_data[j].append(sum(totalfity)/len(totalfity))
                        peakvals[j].append(fitlistsx[i][np.argmax(fitlistsy[i])])
                        

                        #define params for time constants
                        maxval = np.max(function3)
                        maxvalindex = function3.index(maxval)
                        onesigma = maxval*(1/np.exp(1))
                        sigmaminx = totalfitx[ffitexp_totalmod.index(find_nearest(ffitexp_totalmod,onesigma))]
                        sigmaminy = function3[ffitexp_totalmod.index(find_nearest(ffitexp_totalmod,onesigma))]
                        thistau = 1*(sigmaminx - totalfitx[maxvalindex])
   
                        
                        # Normalizing discontinuities from jumped flux
                        gl_zeros = []
                        normxdisc = []
                        if len(xdisc_N) > 0:
                            for k in range(len(xdisc_N)):
                                gl_zeros.append(discthresh)
                                normxdisc.append(xNorm0*xdisc_N[k])
                          
                        
                        # Handler for if the fit finds a negative time constant, usually caused by bad higher order exp fits to the tail
                        # Multiple degree polynomial fits for the tails usual fit them better, but sometimes can cause problems
                        
                        if thistau < 0.0:
                       
                            coefs = poly.polyfit(fitlistx_logchop, fitlisty_logchop, 1) # Define a polynomial to fit the events in log space
                            ffit = poly.polyval(fitlistx_logchop, coefs) # Creating the fit in log space
                            xfit = np.exp(fitlistx_logchop) # Convert back from log
                            ffitexp = np.exp(ffit)
                            function1 = []
                            function2 = []
                            function3 = []
                            ffitexp_total = np.exp(poly.polyval(np.log(totalfitx), coefs))
                            ffitexp_totalmod = []
                            # this loop is to fix the issue of the start of the exponential fits going way above the peak in the data
                            for k in range(len(ffitexp_total)):
                                if ffitexp_total[k] > np.max(fitlistsy[i]):
                                    ffitexp_totalmod.append(np.max(fitlistsy[i]))
                                else:
                                    ffitexp_totalmod.append(ffitexp_total[k])

                            ffitexp_total[:phase_index+3] = np.max(fitlistsy[i])
                            
                            # Re-defining combined functions based off of new exponential
                            for l in range(len(totalfitx)): 
                                function1.append((1 - sigma1[l]) * ffit_re_total[l]+sigma1[l] * ffit_p_total[l])
                                function2.append((1 - sigma2[l]) * ffit_p_total[l]+sigma2[l] * ffitexp_totalmod[l])
                                function3.append((1 - sigma1[l]) * ffit_re_total[l] +sigma1[l] * function2[l])
                            print("failed fit found, correcting")
                            
                            maxval = np.max(function3)
                            maxvalindex = function3.index(maxval)
                            onesigma = maxval*(1/np.exp(1))
                            sigmaminx = totalfitx[ffitexp_totalmod.index(find_nearest(ffitexp_totalmod,onesigma))]
                            sigmaminy = function3[ffitexp_totalmod.index(find_nearest(ffitexp_totalmod,onesigma))]
                            thistau = 1*(sigmaminx - totalfitx[maxvalindex])
                            timeconsts[j].append(thistau)
                            
                        else:
                            timeconsts[j].append(thistau)
                        
                        # If there's still an issue then this skips over the pulse and appends the error array
                        if thistau < 0.0:
                            print("could not correct")
                            errors.append(1)
                        
                        
                        # Show each fit
                        if showfits:
                            pl.clf()
                            pl.figure()
                            pl.title('dataset: ' + str(datalist[n][-7:-4]) + ', channel: ' + str(SQs[j]))
                            pl.plot(totalfitx, totalfity)
                            pl.plot(totalfitx, function3, 'r')
                            pl.pause(0.05)
                            pl.show(block=False)
                        
                        
                        # Save each fit
                        if savefits:
                            newdir = os.path.join(writepath+'fitplots/')
                            if not os.path.exists(newdir):
                                os.mkdir(newdir)
                            pl.clf()
                            pl.figure()
                            pl.title('dataset: ' + str(datalist[n][-7:-4]) + ', channel: ' + str(SQs[j]))
                            pl.plot(totalfitx, totalfity)
                            pl.plot(totalfitx, function3, 'r')
                            pl.savefig(newdir + wpsuffix + '_dataset-' + str(datalist[n][-7:-4]) + '_channel-' + str(SQs[j])+  '.png')
                 
        
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # Coincidence finding! 
        # This still needs to be worked on - loops in current method add significant compute time to analysis (for triple coincidence)
        
        if coincidence:
            meantcs = []
            meantimeconst = []
            for j in range(len(SQs)):
                meantcs.append(np.mean(timeconsts[j]))
            meantimeconst = np.mean(meantcs)

            if len(SQs)==3:
                coinc01 = []
                coinc01_time = []
                coinc02 = []
                coinc02_time = []
                coinc12 = []
                coinc12_time = []
                coinc012 = []
  

        # If two peaks in different channels are within three time constants
                for i in range(len(peakvals[0])):
                    for j in range(len(peakvals[1])):
                        if np.abs(peakvals[0][i] - peakvals[1][j]) < meantimeconst*3:
                            coinc01.append(datalist[n][-7:-4])
                            coinc01_time.append(peakvals[0][i] - peakvals[1][j])

                for i in range(len(peakvals[0])):
                    for j in range(len(peakvals[2])):
                        if np.abs(peakvals[0][i] - peakvals[2][j]) < meantimeconst*3:
                            coinc02.append(datalist[n][-7:-4])
                            coinc02_time.append(peakvals[0][i] - peakvals[2][j])

                for i in range(len(peakvals[1])):
                    for j in range(len(peakvals[2])):
                        if np.abs(peakvals[1][i] - peakvals[2][j]) < meantimeconst*3:
                            coinc12.append(datalist[n][-7:-4])
                            coinc12_time.append(peakvals[1][i] - peakvals[2][j])

                allcoinc = [coinc01, coinc01_time, coinc02, coinc02_time, coinc12, coinc12_time, coinc012]
                print(allcoinc)
        
        
        
     # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    
        # Defines an array for the hit rates in each channel
        
        ratesall = [sum(rates[0])/(len(datalist)*scantime), sum(rates[1])/(len(datalist)*scantime), sum(rates[2])/(len(datalist)*scantime)]
    
    
    
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        
        jfe_datasets.append(jfe_channels) # Appending the JFE data sets in the fit loop
        
    # End of the fit loop
    
    fe_array = np.array(jfe_datasets)
    totaljfe = np.sum(jfe_array)
    TRE = np.sum(jfe_datasets)
    numerrors = sum(errors)

    # Write all pertinent information to pickle files
    
    with open(writepath + 'rates_' + wpsuffix, 'wb') as fp1:
        pickle.dump(ratesall, fp1)
    
    with open(writepath + 'energies_' + wpsuffix, 'wb') as fp2:
        pickle.dump(energies, fp2)
        
    with open(writepath + 'energies-data_' + wpsuffix, 'wb') as fp3:
        pickle.dump(energies_data, fp3)
        
    with open(writepath + 'timeconsts_' + wpsuffix, 'wb') as fp4:
        pickle.dump(timeconsts, fp4)
        
    with open(writepath + 'peakvals_' + wpsuffix, 'wb') as fp5:
        pickle.dump(peakvals, fp5)
        
    if coincidence:
        with open(writepath + 'coincidence_' + wpsuffix, 'wb') as fp6:
            pickle.dump(allcoinc, fp6)
        print("allcoinc:", allcoinc)
    
    with open(writepath + 'jfedatasets_' + wpsuffix, 'wb') as fp7:
        pickle.dump(jfe_datasets, fp7)

    with open(writepath + 'errors_' + wpsuffix, 'wb') as fp8:
        pickle.dump(numerrors, fp8)
    print("numerrors:", numerrors)
        
    
    # Saving figures
    
    if savefigs:
        
        transp = 0.75
        # energies from fits
        pl.clf() 
        n1, bins1, patchs1 = pl.hist(energies[0], bins='auto', alpha = transp, log=True,  label = 'bolo 1')
        n2, bins2, patchs2 = pl.hist(energies[1], bins='auto', alpha = transp, log=True, label = 'bolo 2')
        n3, bins3, patchs3 = pl.hist(energies[2], bins='auto', alpha = transp, log=True, label = 'bolo 3')
        #pl.xscale('log')
        #pl.xlim(xmin = 0., xmax =200.)
        pl.title(wpsuffix)
        pl.xlabel("Pulse energy (arb. units)")
        pl.legend(loc='upper right')
        #pl.show()
        pl.savefig(writepath + 'energiesfromfits_' + wpsuffix + '.png')
        
        # energies from data
        pl.clf() 
        n1, bins1, patchs1 = pl.hist(energies_data[0], bins='auto', alpha = transp, log=True,  label = 'bolo 1')
        n2, bins2, patchs2 = pl.hist(energies_data[1], bins='auto', alpha = transp, log=True, label = 'bolo 2')
        n3, bins3, patchs3 = pl.hist(energies_data[2], bins='auto', alpha = transp, log=True, label = 'bolo 3')
        #pl.xscale('log')
        #pl.xlim(xmin = 0., xmax =200.)
        pl.title(wpsuffix)
        pl.xlabel("Pulse energy (arb. units)")
        pl.legend(loc='upper right')
        #pl.show()
        pl.savefig(writepath + 'energiesfromdata_' + wpsuffix + '.png')
        
        # timeconstants
        pl.clf() 
        n1, bins1, patchs1 = pl.hist(timeconsts[0], bins='auto', alpha = transp, log=True,  label = 'bolo 1')
        n2, bins2, patchs2 = pl.hist(timeconsts[1], bins='auto', alpha = transp, log=True, label = 'bolo 2')
        n3, bins3, patchs3 = pl.hist(timeconsts[2], bins='auto', alpha = transp, log=True, label = 'bolo 3')
        #pl.xscale('log')
        #pl.xlim(xmin = 0., xmax =200.)
        pl.title(wpsuffix)
        pl.xlabel("Pulse energy (arb. units)")
        pl.legend(loc='upper right')
        #pl.show()
        pl.savefig(writepath + 'timeconstants_' + wpsuffix + '.png')
        
        
        # writing values of interest to a text file
        
        txtfile = open(writepath + 'vals3_' + wpsuffix + '.txt', 'w')
        
        txtfile.write("Total number of events in " + str((len(datalist)*scantime)/3600.) + " hours of data: " + str(len(energies[0]+energies[1]+energies[2])) + " \n \n \n")
        
        txtfile.write("Jumped flux events: \n")
        txtfile.write("Total number of JFEs in bolo 1: "+ str(np.sum(jfe_array, axis=0)[0]) + " \n")
        txtfile.write("Total number of JFEs in bolo 2: "+ str(np.sum(jfe_array, axis=0)[1]) + " \n")
        txtfile.write("Total number of JFEs in bolo 3: "+ str(np.sum(jfe_array, axis=0)[2]) + " \n")
        txtfile.write("Total number of JFEs in all detectors: "+ str(np.sum(jfe_array)) + " \n")
        if len(energies[0]+energies[1]+energies[2]) != 0:
            txtfile.write("% of total events that were jumped flux: "+ str(100.*totaljfe/len(energies[0]+energies[1]+energies[2])) + "% \n \n \n")
        else:
            txtfile.write("not enough data \n \n \n")
            
        txtfile.write("Rates \n")
        txtfile.write("bolo 1 rate: " + str(ratesall[0]) + " Hz \n")
        txtfile.write("bolo 2 rate: " + str(ratesall[1]) + " Hz \n")
        txtfile.write("bolo 3 rate: " + str(ratesall[2]) + " Hz \n")
        if len(ratesall) != 0:
            txtfile.write("Average rate of all three channels: " + str(sum(ratesall)/len(ratesall)) + " Hz \n \n \n")
        else:
            txtfile.write("not enough data \n \n \n")
        
        
        txtfile.write("Time constants \n")
        txtfile.write("Mean time constant in bolo 1: " + str(timeconsts[0]) + " s \n")
        txtfile.write("Mean time constant in bolo 2: " + str(timeconsts[1]) + " s \n")
        txtfile.write("Mean time constant in bolo 3: " + str(timeconsts[2]) + " s \n")
        
        if len(timeconsts[0]+timeconsts[1]+timeconsts[2]) != 0:
            txtfile.write("Average time constant in all three channels: " + str(sum(timeconsts[0]+timeconsts[1]+timeconsts[2])/(len(timeconsts[0]+timeconsts[1]+timeconsts[2]))) + " seconds \n \n \n")
        else:
            txtfile.write("not enough data \n \n \n")
            
        if coincidence:
            txtfile.write("Number of double coincidence events:" + str(len(allcoinc[0])+len(allcoinc[2])+len(allcoinc[4]))+ "\n")
            txtfile.write("Number of triple coincidence events: N/A \n \n \n")
        
        
        
        txtfile.write("Number of fit errors: \n")
        txtfile.close


# In[21]:


#print("Running 2021_03_19 - bolo 1: heatsunk control, bolo 2: floating control, bolo 3: floating bling, no source")

#CR_analyze(["/Users/shawn/Google Drive/My Drive/Python/Cosmic Rays/2021_03_19/CR_Scan_023/20210319_SQ1-contr1_SQ2-contr2_SQ6-contr3_biasthreeturnsintotrans_5-FTR-5min_"], \
           #[44,999], [1,2,6], [100.,100.,100.], [0.34,0.365,0.367], 300., [True, True, True], ["20210319_b1-hscontr_b2-fltcontr_b3-fltblng_nosource_44-999"], showfits=False, noisefilt=False, verbose = False, fit = True, pwrcnv = True)

#print("Running 2021_03_23 - bolo 1: heatsunk control, bolo 2: floating control, bolo 3: floating bling, source")
#CR_analyze(["/Users/shawn/Google Drive/My Drive/Python/Cosmic Rays/2021_03_23/CR_Scan_002/20210319_SQ1-contr1_SQ2-contr2_SQ6-contr3_biasthreeturnsintotrans_5-FTR-5min_Co60_"], \
          #[1,847], [1,2,6], [100.,100.,100.], [0.34,0.365,0.367], 300., [True, True, True],["20210323_b1-hscontr_b2-fltcontr_b3-fltblng_Co60_1-847"], showfits=False, noisefilt=False, verbose = False, fit = True, pwrcnv = True)

print("Running 20210516 - control bolos, no source")
CR_analyze(["/Users/shawn/Google Drive/My Drive/Python/Cosmic Rays/2021_05_16-control_nosource/CR_Scan_002/_"],            [2,259], [1,2,6], [100.,100.,100.], [3.457,3.187,3.165], 300., [False, False, True], ["20210516_controlbolos_nosource_2-256"], showfits=False, noisefilt=False, verbose = False, fit = True, pwrcnv = True)

print("Running 20210517 - control bolos, source")
CR_analyze(["/Users/shawn/Google Drive/My Drive/Python/Cosmic Rays/2021_05_17-control_source/CR_Scan_002/source_"],            [1,824], [1,2,6], [100.,100.,100.], [3.517,3.164,3.150], 300., [False, False, True], ["20210517_controlbolos_Co-60_1-824"], showfits=False, noisefilt=False, verbose = False, fit = True, pwrcnv = True)

print("Running 20210528 - mitigated bolos, source")
CR_analyze(["/Users/shawn/Google Drive/My Drive/Python/Cosmic Rays/2021_05_28-mitig_source/CR_Scan_003/_"],            [1,727], [1,2,6], [100.,100.,100.], [2.809,2.911,1.48], 300., [False, False, True], ["20210528_controlbolos_Co-60_1-727"], showfits=False, noisefilt=False, verbose = False, fit = True, pwrcnv = True)

print("Running 20210604 - mitigated bolos, no source")
CR_analyze(["/Users/shawn/Google Drive/My Drive/Python/Cosmic Rays/2021_06_04-mitig_nosource/CR_Scan_002/BT10-02-CR-with-mitigation-no-source_"],            [1,999], [1,2,6], [100.,100.,100.], [2.809,2.911,1.48], 300., [False, False, True], ["20210604_controlbolos_nosource_1-999"], showfits=False, noisefilt=False, verbose = False, fit = True, pwrcnv = True)












# In[ ]:




