# from numpy import*

# from scipy import*



from __future__ import division, print_function; # compatibility in python 3.x



import sys

import numpy  as np

import scipy.constants as PC # physical constants

import os

import matplotlib.pyplot as plt  # for ploting

import pylab as pl

import pdb # for debugging the code

import time # for measuring elapsed time

from scipy.optimize import leastsq

start_time = time.time()

n2 = np.sqrt(9.7);

n0 = 1.0;

n3 = 1.0;

dEps1 = None;

dThickness_alumina = 6.3e-3 #meters

dThickness_coat = 0.550e-3 #meters

dThickness_coat = 0.250e-3 #meters

dFrq_const = 160.0e9; #Hz



# improved input with pause option: single/multiple number(s)/character(s)

# p --> pdb

def myInput (txtIn, defVals): # improved input for both number and string

    outputOpts = None;

    flag = ['c']; # continue 



    if (type(defVals)!=list): defVals = [defVals];



    txt = txtIn + ': [';

    for i in range(len(defVals)):

        txt += defVals[i] if (type(defVals[i]) == str) else str(defVals[i]);

        txt += ', ' if (i < (len(defVals) - 1)) else ']';



    try: 

       if sys.version_info >= (2, 7) and sys.version_info < (3, 0):

          inputOptStr = raw_input( txt + ': [p/pause]: ' );

       elif sys.version_info >= (3, 0):

          inputOptStr = input( txt + ': p/pause: ' );

       else: raise " ! Wrong python version."



       if (len(inputOptStr) != 0):

           optStrArr = inputOptStr.replace(',',' ').split();

           if (optStrArr[0].isalpha() and optStrArr[0] == 'p'): flag = 'p';



           if (len(optStrArr) < len(defVals) and flag != 'p'):

               print ("# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #\
                    \n#  WARNING: not enough number of input values --> Re-Enter values.  #\
                    \n# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #");



               txt += ": Re-Enter %d values" % len(defVals);

               if sys.version_info >= (2, 7) and sys.version_info < (3, 0):

                  inputOptStr = raw_input( txt );

               elif sys.version_info >= (3, 0): inputOptStr = input( txt );

               else: raise " ! Wrong python version."



       if (len(inputOptStr) == 0 or flag == 'p' or len(inputOptStr.replace(',','').split()) < len(defVals)):

           outputOpts = defVals;

       else:

          optStrArr = inputOptStr.replace(',',' ').split();



          if optStrArr[0].isalpha(): 

             if optStrArr[0] == 'p':

                print ("pdb: EKJ> h/help, c/resume, l/list, n/next ....\
                      \npdb: EKJ> investigate the variable(s).");

                flag = ['p'];



             outputOpts = optStrArr; 

          else: outputOpts = np.array(optStrArr,type(defVals[0])).tolist();

    except SyntaxError: outputOpts = defVals ;



    if flag == 'p': pdb.set_trace();



    return outputOpts; # convert to single-level list





def refraction_index():

    global n0, n2, dEps1;

    #pdb.set_trace();

    n1 = np.sqrt(dEps1);

    return np.array([n0, n1, n2, n3])



def reflection_coef():

    dRefTmp = []



    n = refraction_index();

    for i in range(3):

        dRefTmp.append( (n[i] - n[i+1])/(n[i] + n[i+1]) );

        

    return np.array(dRefTmp)

    

def calcX(dFrq_Hz):

    global dThickness_coat, dThickness_alumina;

    n = refraction_index();

    X01 = np.exp(1j*(2. * np.pi * dFrq_Hz * dThickness_coat * n[1]/PC.c)) #* (1-(2. * np.pi * dFrq_Hz * dThickness_coat * n[1] * 0.005/PC.c));

    X12 = np.exp(1j*(2. * np.pi * dFrq_Hz * dThickness_alumina * n[2]/PC.c));

    #X01 = (1-(2. * np.pi * dFrq_Hz * dThickness_coat * n[1] * 0.005/PC.c));

    #X12 = (1-(2. * np.pi * dFrq_Hz * dThickness_alumina * n[2] * 4.5e-4/PC.c));

    #X23 = (1-(2. * np.pi * dFrq_Hz * dThickness_coat * n[1] * 0.005/PC.c));

    return np.array([X01, X12])



def calcD(dFrq_Hz):

    dRef = reflection_coef();

    X = calcX(dFrq_Hz);

    D = [];

    d = [[1,dRef[0]],[dRef[0],1]];

    D.append(d);

    for i in range(2):

        d = np.dot(np.array([[X[i], 0], [0, X[i]**-1]]), np.array([[1,dRef[i+1]],[dRef[i+1],1]]));

        D.append(d)   

    return np.array(D), dRef



def calcM(dFrqHz):

    D, Ref = calcD(dFrqHz);

    M = [];

    #pdb.set_trace();

    for i in range(len(D)):

        m = (1+Ref[i])**-1*D[i];

        M.append(m);

    return np.array(M)


# read an external text file and return a numpy array with dimension (nLinesInTxt, 3)

# It will skip a line starting with #.

# Each line has three numbers, separated by space ( ) or comma (,).

# example: 

'''

# this is an example file.

0.001	0.002	0.003

0.001,	0.002,	0.003 

'''         

#def readData(fileName):
#
#    data = [];
#
#
#
#    fIn = open(fileName, 'rb')
#
#    # fIn.seek(0, 0)
#
#
#
#    for line in fIn:
#
#        str = line.replace(';',' ').replace(',',' ').split()
#
#        if (len(str) > 0 and str[0] != '#'): 
#
#            data.append( [float(str[0]), float(str[1]), float(str[2])] );
#
#
#
#    fIn.close()
#
#
#
#    return np.array(data);
#


# input frequency in Hz unit

def transmittance(dFrqHz):

    M = calcM(dFrqHz);

    #pdb.set_trace();

    N = np.dot(M[0], np.dot(M[1], M[2]));

    dT = abs((N[0,0])**-1)**2;

    return dT;
    

# main program

'''

NOTE: Physical unit is imported as PC. 

c = PC.c

g = PC.g

...

'''

if __name__ == '__main__': 

    plt.ion(); # interactive plot

    # plt.close('all');

    

    # create a array for frequency

    dFrqIncrement_GHz = 0.1;



    txt = "ENTER> Starting frequency in GHz: "

    dFrqStart_GHz = myInput(txt, 0.0)[0];
    #dFrqStart_GHz, dFrqEnd_GHz = myInput (txt, [0.0, 300.])[0:2]

    txt = "ENTER> Ending frequency in GHz: "

    dFrqEnd_GHz = myInput(txt, 300.0)[0];

    dFrqArr_GHz = np.arange(dFrqStart_GHz, dFrqEnd_GHz, dFrqIncrement_GHz); # in GHz unit



    txt = "ENTER> Relative permitivity of the coating layer "

    dEps1 = myInput (txt, 5.0)[0];

    trans_theory = transmittance(1e9*dFrqArr_GHz);

    #pdb.set_trace();

    # plot thermalspray data

    fig1 = plt.figure();
    
    ax1 = fig1.add_subplot(111);

    print(dFrqArr_GHz, trans_theory)
    ax1.plot(dFrqArr_GHz, trans_theory, 'r', label = 'theory');
    
    #ax1.plot(thermspray_transmission[:,0], thermspray_transmission[:,1], 'b')

    ax1.set_xlim([np.min(dFrqArr_GHz), np.max(dFrqArr_GHz)]);

    #ax1.set_ylim([0.0, 1.1]);

    ax1.set_xlabel("Frequency (GHz)", fontsize = 16);

    ax1.set_ylabel("Transmission", fontsize=16);

    #ax1.set_title("Alumina with Silicon Nitride", fontsize = 20);

    fig1.show();
    fig1.savefig('./test.png')
    #import ipdb;ipdb.set_trace()



    print("My program took", time.time() - start_time, "to run")

    

    # read a text data file

#    txt = "ENTER> Do you want to read an external data file (y/n)?"
#
#    bReadExternalFile = myInput(txt, ['y'])[0] != 'n'
#
#    if bReadExternalFile:
#
#       import Tkinter, tkFileDialog;
#
#
#
#       initDIr = '.'; # '~/data':  default data directory
#
#       inFileName = tkFileDialog.askopenfilename(initialdir=initDir,
#
#                                                 title='Open a text file:',
#
#                                                 filetypes=[('dataFile','.txt')]);
#
#       data = readData ( inFileName );
#
#

    #os.chdir("/Users/objeonog/Documents/Code/Python/Analysis/Transmission")    

    #pdb.set_trace() 


