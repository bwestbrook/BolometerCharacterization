# analyzeFTSscan.py
# Created by Ari Cukierman
#
# use pkl file to make interferogram and Fourier transform
# Use the directory of the pkl file you want to analyze as the first 
# argument, or use no argument to analyze the most recently modified
# FTS subdirectory.

import os,pickle,sys
#from matplotlib.pyplot import *
import pylab as pl
#import numpy as np
from numpy import *
from PyQt4 import QtCore, QtGui

class FTSanalyzer():

#### Analysis functions ####

# for each bolo, make interferograms and Fourier transforms

    '''def main():
        for bolo in boloList:
            analyzeBolo(bolo)'''



# get the average of an array as an array of the same length
    def getAvgAsArray(self,inputArray):
        avg = average(inputArray)
        return array(zeros(len(inputArray))) + avg

# make an interferogram
    def makeInterferogram(self,posArray,magArray,filenameRoot=None,\
                          xAxisLabel = 'Inches'):
        deltaX = posArray[1] - posArray[0]
        xMin = min(posArray) - deltaX
        xMax = max(posArray) + deltaX

        figure()
        plot(posArray,magArray,color = 'b')
        plot(posArray,getAvgAsArray(magArray),linestyle = '--',color = 'r')
        xlim(xMin,xMax)
        ylim(ymin = 0.0)
        grid()
        xlabel(xAxisLabel)
#        title('')
        if filenameRoot:
            savefig(filenameRoot)

# plot raw interferogram data with error bars
    def makeRawInterferogram(self, posArray,magArray,noiseArray,filenameRoot,\
                             xAxisLabel = 'Inches'):
        deltaX = posArray[1] - posArray[0]
        xMin = min(posArray) - deltaX
        xMax = max(posArray) + deltaX
        
        figure()
        plot(posArray,magArray,linestyle = 'none',marker = '.',color = 'b')
        errorbar(posArray,magArray,yerr = noiseArray,linestyle = 'none',\
                     color = 'b')
        plot(posArray,self.getAvgAsArray(magArray),linestyle = '--',color = 'r')
        xlim(xMin,xMax)
        ylim(ymin = 0.0)
        grid()
        xlabel(xAxisLabel)
        title('FFT Complete')
        savefig(filenameRoot)

# strip the interferogram data of negative positions
    def stripNegPos(self,posInput,magInput):
        posList = list()
        magList = list()
        for i in range(len(posInput)):
            posTemp = posInput[i]
            if posTemp >= 0.0:
                posList.append(posTemp)
                magList.append(magInput[i])
        return array(posList),array(magList)

# from non-negative interferogram data, make artificial interferogram data
# which is symmetric about 0
    def mirrorPositiveData(self,posInput,magInput):
        negPos = - posInput[::-1][:-1]
        magNegPos = magInput[::-1][:-1]
        return append(negPos,posInput),append(magNegPos,magInput)

# use positive-positions to symmetrize the interferogram
    def symmetrizeIF(self,posInput,magInput):
        posNonNeg,magNonNeg = self.stripNegPos(posInput,magInput)
        return self.mirrorPositiveData(posNonNeg,magNonNeg)

# Take a time array and a magnitude array as inputs.
# Return the Fourier transform with correct frequencies.
# This differs from the numpy function which makes several
# assumptions about the input array.
# The assumption here is that the t values are evenly spaced.
# Don't trust the overall normalization.
    def fourierTransform(self,timeArray,magArray):
        # use numpy's fft function
        magFFT = fft.fft(magArray)
        
        # determine time spacing
        deltaT = timeArray[1] - timeArray[0]
        # number of points
        n = len(magArray)

        # numpy's frequencies assume deltaT = 1; correct for this
        freq = fft.fftfreq(n) / deltaT

        # numpy's fft uses "standard order"; we can use the shift
        # function to put them in n order in which frequency increases
        # with index
        magFFTOrdered = fft.fftshift(magFFT)
        freqOrdered = fft.fftshift(freq)

        # numpy's fft also assumes that we are starting at t = 0;
        # correct for this with a phase in frequency space
        magFFTOrderedPhased = \
            magFFTOrdered * exp(-2j * pi * freqOrdered * timeArray[0])

        return freqOrdered,magFFTOrderedPhased

# apodize the interferogram
# over time, add multiple types of apodization
    def apodize(self,posArray,magArray,apodization):

        if apodization == 'TIANGULAR':
            # subtract out the DC signal when apodizing;
            # add it it back in afterwards
            triangle = (max(magArray) - average(magArray)) * \
                    (1 - abs(posArray) / max(abs(posArray)))
            magArray = (magArray - average(magArray)) * triangle + \
                    average(magArray)

        return posArray,magArray

# find the maximum of the interferogram and make that the origin of the 
# coordinate system
    def moveOriginToZPD(self,posArray,magArray):
        maxMag = max(magArray)
        for i in range(len(posArray)):
            if magArray[i] == maxMag:
                posOffset = posArray[i]
        posArray -= posOffset
        return posArray,magArray

# turn interferogram data into frequency-space data;
# only uses positive-position data (assumes full interferogram is symmetric)
# the speed of light in inches per second is 1.18e10
    def ifToFT(self,posArray,magArray,c = 1.18e10,makeSymmetricIF = True,\
                   apodization = 'None'):

        # make the ZPD occur at the origin of the coordinate system
        posArray,magArray = self.moveOriginToZPD(posArray,magArray)

        # can symmetrize the interferogram if you want to
        if makeSymmetricIF:
            # take the positive-position data only and artificially make the
            # interferogram symmetric
            posArray,magArray = self.symmetrizeIF(posArray,magArray)
            
        # apodize the interferogram
        posArray,magArray = self.apodize(posArray,magArray,apodization)

        # Double the distances in the posArray since we want the position 
        # coordinates to describe the path difference; the light ray 
        # travels to the mirror and back, so it traverses the mirror distance
        # twice.
        posEffArray = 2 * array(posArray)
        
        # Take the Fourier transform as if the position array were time;
        # we will correct for that afterwards
        freqUnconverted,magFFT = self.fourierTransform(posEffArray,magArray)
        
        # The fourierTransform function is giving us 1/lambda instead of
        # frequency. This is because we really want "i k x" in the exponential, 
        # but it assumes we have "i w t". It thinks it's giving us w / 2 pi, but
        # it is actually giving us k / 2 pi = 1 / lambda. We can get frequency from
        # this by multiplying by c.
        freq = array(freqUnconverted) * c

        return freq,magFFT

# truncate the frequency and magnitude arrays so that they only include
# frequencies greater than 0 Hz
    def stripNonPosFreq(self,freqInput,FTInput):
        freq = list()
        FT = list()
        for i in range(len(freqInput)):
            freqTemp = freqInput[i]
            if freqTemp > 0:
                freq.append(freqTemp)
                FT.append(FTInput[i])
        return array(freq),array(FT)

# plot the real part of the Fourier transform
    '''def plotRealFT(self,freq,FT,filenameRoot,outputDir = outputDir):
        freqGHz = freq / 10.0**9
        figure()
        plot(freqGHz,real(FT))
        xlabel('GHz')
        filename = filenameRoot + '_fft_real'
        title(filename)
        savefig(outputDir + '/' + filename)'''

# plot both the real and the imaginary parts of the Fourier transform
    def plotCompleteFT(self,freq,FT,filenameRoot = None):
        freqGHz = freq / 10.0**9
        fig = pl.figure(figsize=(3,1.5))
        ax = fig.add_subplot(111)
        yticks = linspace(min(real(FT)),max(real(FT)),5)
        yticks = [round(x,2) for x in yticks]
        ax.set_yticks(yticks)
        ax.set_yticklabels(yticks,fontsize = 6)
        '''xticks = linspace(freqGHZ[0],freqGHZ[-1],5)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticks,fontsize = 6)'''
        ax.plot(freqGHz,real(FT),color = 'b',label = 'Real')
        ax.plot(freqGHz,imag(FT),color = 'r',label = 'Imag')
        ax.set_xlabel('Frequency(GHz)')
        ax.set_ylabel('Amplitude')        
        pl.legend(prop={'size': 6})
        fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
        ax.set_title('FFT Complete')
#        grid()
        if filenameRoot:
            fig.savefig(filenameRoot)
        else:
            fig.savefig('temp_files/temp_fft.png')
        pl.close('all')
        image = QtGui.QPixmap('temp_files/temp_fft.png')
        image = image.scaled(600, 300)

# analyze the data for a given bolo
    def analyzeBolo(self, posArray, magArray, filenameRoot = None,apodization=None):

 #       if filenameRoot:
        # plot the raw data
  #          makeRawInterferogram(posArray,magArray,noise,filenameRoot)
        
        # turn the raw data into the frequency response of the detectors
        freqArray,FTArray = self.ifToFT(posArray,magArray,\
                                       makeSymmetricIF = True,\
                                        apodization = apodization)

        # strip the non-positive frequencies
        posFreqArray,FTArrayPosFreq = self.stripNonPosFreq(freqArray,FTArray)


        # plot both the imaginary and real parts of the Fourier transform
        self.plotCompleteFT(posFreqArray,FTArrayPosFreq,filenameRoot = filenameRoot)
        return posFreqArray,FTArrayPosFreq



        
