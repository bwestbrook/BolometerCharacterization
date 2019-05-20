import matplotlib
matplotlib.use('TkAgg')
import pylab as pl
from DFT import *
from scipy import signal
from scipy.signal import find_peaks_cwt
import scipy.optimize
import numpy as np
import matplotlib.colors as colors
import matplotlib.ticker as ticker
import pickle
from matplotlib import cm
from scipy import optimize
from scipy import math
from scipy.signal import argrelextrema
from math import exp, expm1
from scipy.fftpack import rfft, irfft, fftfreq
import numpy.polynomial.polynomial as poly
#pl.rc('text',usetex = True)
#pl.rc('font',family = 'serif')
pl.rcParams.update({'font.size':10})

kB = 1.38e-23 # Boltzmann constant in J/K
GHz = 1e9
pW = 1e-12
mK = 1e-3
kOhm = 1e3
c = 299792458 # speed of light in m/s
mm = 1e-3

r2d = 180./pl.pi # radian to degree
d2r = 1./r2d # degree to radian
inch2mm = 25.4 # 1 inch in mm

zFP2flange = 137.#+12.7 # distance from focal plane to window flange (mm)

fnAtm = 'ExternalSpectra/ATM_PWV0p5mm_APEX.txt'


def extract_raw_data(fn,colNames):
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
			llist[i].append(float(lineSplit[i]))
	for i in range(len(colNames)):
		d[colNames[i]] = pl.array(llist[i])
	f.close()
	return d



def extract_raw_beam(fn):
	'''
	Extract beam-map data from a LabVIEW output file fn and
	return a Python dictionary with entries x, y, amp and std.

	Positions are in motor steps (usually 100000 per inch). Amplitudes
	are in arbitrary units.
	'''
	colNames = ['y','x','amp','std']
	return extract_raw_data(fn,colNames)



def transformPlotParam(plotParam,defaultPlotParam):
	'''
	Set a plot parameter to its default value if it is given as None.
	'''
	if plotParam == None:
		return defaultPlotParam
	else:
		return plotParam

def make_figure_multiple(dList,xEntry,yEntry,labelList = None,\
							 xLabel = None,yLabel = None,\
							 outputFn = None,linewidthList = None,\
							 linestyleList = None,xMin = None,\
							 xMax = None,\
							 ylimTup = None,xNorm = None,yNorm = None, intNorm = False,\
							 markerList = None,title = None,legLoc = 'best', savepng = False,\
							 minovermax = False, fit = False, partialfit = False, trunc = 0):
	'''
	Make a figure from multiple data dictionaries. Specify the dictionary
	keywords for the x values (xEntry) and y values (yEntry). Other
	plot parameters will be set to default values if given as None. Plot
	parameters given as lists correspond elementwise to the dictionary list
	dList. The x and y values can be normalized with xNorm and yNorm, 
	respectively.
	'''
	labelList = transformPlotParam(labelList,len(dList)*[None])
	xLabel = transformPlotParam(xLabel,xEntry)
	yLabel = transformPlotParam(yLabel,yEntry)
	linewidthList = transformPlotParam(linewidthList,len(dList)*[1])
	linestyleList = transformPlotParam(linestyleList,len(dList)*['-'])
	xNorm = transformPlotParam(xNorm,1.)
	yNorm = transformPlotParam(yNorm,1.)
	markerList = transformPlotParam(markerList,len(dList)*[None])
	title = transformPlotParam(title,'')

	pl.figure(figsize = (10,6))
	for i in range(len(dList)):
		d = dList[i]
		if intNorm:
			Norm = sum([])
		pl.plot(xNorm*d[xEntry],yNorm*d[yEntry],label = labelList[i],\
					linewidth = linewidthList[i],\
					linestyle = linestyleList[i],marker = markerList[i])
	
	if fit:
		def test_func(x, a, b, c, d):
			return a * np.sin( b * x + c) + d
		if partialfit:
			x2 = dList[0]['pos']
			y2 = dList[0]['amp']
			x2del = x2[0:trunc]
			y2del = y2[0:trunc]
			#print(x2)
			params, params_covariance = optimize.curve_fit(test_func, x2del, y2del, p0 = [8., 1/10000., 3.14, 4])
			print(params)
		else:
			params, params_covariance = optimize.curve_fit(test_func, dList[0]['pos'], dList[0]['amp'], p0 = [8., 1/10000., 3.14, 4], bounds = (0,60000.))
			print(params)
		if minovermax:
			mmin = np.amin(test_func(dList[0]['pos'], params[0],params[1],params[2],params[3]))
			mmax = np.amax(test_func(dList[0]['pos'], params[0],params[1],params[2],params[3]))
			print(mmin,mmax)
			#crosspol = np.amin(dList[0]['amp'])/np.nanmax(dList[0]['amp'])
			crosspol = mmin/mmax
			print(crosspol)
			llabel = "90 GHz - 5 mm - No AR, crosspol = %s" % round(100*crosspol,2) + "%"
			print(llabel)
		pl.plot(dList[0]['pos'], test_func(dList[0]['pos'], params[0],params[1],params[2],params[3]), label = llabel)
		print(test_func)

	

	pl.grid()
	pl.legend(loc = legLoc)
	pl.xlabel(xLabel)
	pl.ylabel(yLabel)
	pl.xlim(xmin = xMin,xmax = xMax)
	pl.ylim(ylimTup)
	pl.title(title)
	#pl.grid(False)
	#pl.xticks(np.arange(0,250,10))
	#pl.xticks([0,50,98,100,150,200,250])
	if savepng:
		pl.savefig("%s.png" % (title))
	if outputFn == None:
		pl.show()
	else:
		pl.savefig(outputFn,bbox_inches = 'tight')




def make_meshgrid(d,forContour = False):
	nx = 0
	ny = 0
	x0 = d['x'][0]
	y0 = d['y'][0]
	xTemp = d['x'][nx]
	yTemp = d['y'][ny]
	while xTemp == x0:
		nx += 1
		xTemp = d['x'][nx]
	while yTemp == y0:
		ny += 1
		yTemp = d['y'][ny]
	dx = pl.absolute(xTemp - x0)
	dy = pl.absolute(yTemp - y0)
	xMin = min(d['x'])
	xMax = max(d['x'])
	yMin = min(d['y'])
	yMax = max(d['y'])
	# For pcolor, define meshgrid with one extra row/col relative to amp
	# matrix; otherwise, last row/col won't be plotted. For contour, leave out.
	if forContour:
		X,Y = pl.meshgrid(pl.arange(xMin,xMax + dx,dx),\
									 pl.arange(yMin,yMax + dy,dy))
		dX = 0. # no offset needed for contour
		dY = 0.
		nRows,nCols = pl.shape(X)
	else:
		X,Y = pl.meshgrid(pl.arange(xMin,xMax + 2.*dx,dx),\
						  pl.arange(yMin,yMax + 2.*dy,dy))
		dX = dx/2. # offset for pcolor to center pixels on (x,y)
		dY = dy/2.
		nRows,nCols = pl.shape(X)
		nRows -= 1
		nCols -= 1
	A = pl.zeros((nRows,nCols))
	# for each (i,j), check that this point is in the data.
	# Only modify amp matrix if it exists.
	for i in range(nRows):
		for j in range(nCols):
			x = X[i,j]
			y = Y[i,j]
			for k in range(len(d['amp'])):
				if d['x'][k] == x and d['y'][k] == y:
					A[i,j] = d['amp'][k]    
	return X-dX,Y-dY,A

def convertBeam2dB(A,dBref,dBMin = -20.):
	nRows,nCols = pl.shape(A)
	AdB = pl.zeros(pl.shape(A))
	for i in range(nRows):
		for j in range(nCols):
			if A[i,j] <= 0.:
				AdB[i,j] = dBMin
			else:
				AdB[i,j] = 10.*pl.log10(A[i,j]/dBref)
	return AdB

def make_figure_beam(dColor,dContour = None,title = None,\
						 xLabel = '',yLabel = '',contourLabel = None,\
						 cLabel = '',xTicks = None,xTickLabels = None,\
						 yTicks = None,yTickLabels = None,dBref = None,\
						 dBMin = -20.,linMin = 0.,outputFn = None,xlimTup = None,\
						 ylimTup = None, savepng = False):
	X,Y,A = make_meshgrid(dColor)

	fig,ax = pl.subplots()
	ax.set_aspect('equal')

	if dBref == None:
		#pl.pcolor(X,Y,A,vmin = linMin, cmap = cm.jet)
		pl.pcolor(X,Y,A, cmap = cm.jet)
	else:
		pl.pcolor(X,Y,convertBeam2dB(A,dBref,dBMin = dBMin),vmin = dBMin, cmap = cm.jet)
	c = pl.colorbar()

	if dContour != None:
		Xc,Yc,Ac = make_meshgrid(dContour,forContour = True)
		if dBref == None:
			beamContour = pl.contour(Xc,Yc,Ac,colors = 'k')
		else:
			beamContour = pl.contour(Xc,Yc,\
									 convertBeam2dB(Ac,dBref,dBMin = dBMin),\
									 colors = 'k')
		pl.clabel(beamContour,inline = 1,colors = 'k',fontsize = 10,\
					  fmt = '$%.1f$')
		beamContour.collections[0].set_label(contourLabel)

	c.set_label(cLabel)
	pl.xlabel(xLabel)
	pl.ylabel(yLabel)
	if title != None:
		pl.title(title)
	pl.legend(loc = 'lower right')

	if xTicks != None:
		ax.set_xticks(xTicks)
		if xTickLabels != None:
			ax.set_xticklabels(xTickLabels)
	if yTicks != None:
		ax.set_yticks(yTicks)
		if yTickLabels != None:
			ax.set_yticklabels(yTickLabels)
	
	if xlimTup != None:
		pl.xlim(xlimTup)
	if ylimTup != None:
		pl.ylim(ylimTup)

	if outputFn != None:
		pl.savefig(outputFn,bbox_inches = 'tight')
	else:
		pl.show(block=False)
	if savepng:
		pl.savefig("%s.png" % (title))



def make_figure_beam_raw(fn,title = None,showContour = False,dB = False,\
							 dBMin = -20.,outputFn = None, PwrNorm = False, savepng = False):
	d = extract_raw_beam(fn)
	pwrtot = sum(d['amp'])
	print(pwrtot)
	if PwrNorm:
		d['amp'] = d['amp']/pwrtot 
	magMax = max(d['amp'])
	if showContour:
		dContour = d
	else:
		dContour = None
	if dB:
		dBref = magMax
		cLabel = r'Power (dB)'
	else:
		dBref = None
		cLabel = r'Power (arbitrary units)'
	make_figure_beam(d,dContour = dContour,title = title,\
						 xLabel = r'$x$ (motor steps)',\
						 yLabel = r'$y$ (motor steps)',\
						 cLabel = cLabel,dBref = dBref,dBMin = dBMin,\
						 outputFn = outputFn, savepng = savepng)







def make_figure_beam_raw_multiple(fnList,titleList,showContour = False,dB = False,\
							 dBMin = -20.,outputFn = None, BMNorm = False, CustomNorm = False, CN = [], savepng = False):
	for i in range(len(fnList)):
		d = extract_raw_beam(fnList[i])
		pwrtot = sum(d['amp'])
		if BMNorm:
			d['amp'] = d['amp']/pwrtot
		if CustomNorm:
			print[CN[i]]
			d['amp'] = CN[i]*d['amp']
		magMax = max(d['amp'])
		if showContour:
			dContour = d
		else:
			dContour = None
		if dB:
			dBref = magMax
			cLabel = r'Power (dB)'
		else:
			dBref = None
			cLabel = r'Power (arbitrary units)'
		make_figure_beam(d,dContour = dContour,title = titleList[i],\
							 xLabel = r'$x$ (motor steps)',\
							 yLabel = r'$y$ (motor steps)',\
							 cLabel = cLabel,dBref = dBref,dBMin = dBMin,\
							 outputFn = outputFn, savepng = savepng)


def beam_model(xy,nu,z,x0,y0,phi0,w0x,w0y,I0):
	'''
	xy: list of tuples of the form (x,y)
	nu: frequency (GHz)
	z: distance from antenna to beam-mapper plane (mm)
	x0,y0: beam center (mm)
	phi0: rotation of beam w.r.t. xy coordinates
	w0x: beam waist along x-axis (mm)
	w0y: beam waist along y-axis (mm)
	I0: peak amplitude
	'''
	x = pl.zeros(len(xy))
	y = pl.zeros(len(xy))
	for i in range(len(xy)):
		x[i] = xy[i][0]
		y[i] = xy[i][1]
	xp = pl.cos(phi0)*(x-x0) + pl.sin(phi0)*(y-y0)
	yp = -pl.sin(phi0)*(x-x0) + pl.cos(phi0)*(y-y0)
	s = pl.sqrt(xp**2 + yp**2)
	
	cosTheta = pl.sqrt(1./(1.+(s/z)**2))
	sinTheta = pl.sqrt(((s/z)**2)/(1.+(s/z)**2))
	cosPhi = xp/s
	sinPhi = yp/s

	sigmaX = w0x/pl.sqrt(2.)
	sigmaY = w0y/pl.sqrt(2.)
	
	wl = (c/mm)/(nu*GHz) # wavelength in mm
	k = 2.*pl.pi/wl

	return I0*(cosTheta**3)*pl.exp(-(k*sigmaX*sinTheta*cosPhi)**2)*\
		pl.exp(-(k*sigmaY*sinTheta*sinPhi)**2)

def create_beam_model(nu,deltaZ):
	'''
	nu: central frequency (GHz)
	deltaZ: distance from window flange to beam-mapper aperture (inches)
	'''
	z = zFP2flange + inch2mm*deltaZ

	def model_func(xy,x0,y0,phi0,w0x,w0y,I0):
		return beam_model(xy,nu,z,x0,y0,phi0,w0x,w0y,I0)
	return model_func

def make_points_list(d,stepsPerInch = 100000.):
	'''
	Return a list of tuples of the form (x,y) corresponding to the locations
	of beam-map data samples in the order they were taken.

	d: dictionary containing beam-map data
	stepsPerInch: motor steps per inch; typically 100000
	'''
	xy = []
	for i in range(len(d['x'])):
		xy.append((inch2mm*d['x'][i]/stepsPerInch,\
					   inch2mm*d['y'][i]/stepsPerInch))
	return xy

def get_ellipticity(popt):
	w0x = popt[3]
	w0y = popt[4]
	return pl.absolute( (1./w0x - 1./w0y)/(1./w0x + 1./w0y) )
	
def fit_beam(d,nu,deltaZ,stepsPerInch = 100000.):
	'''
	d: dictionary containing beam-map data
	nu: central frequency (GHz)
	deltaZ: distance from window flange to beam-mapper aperture (inches)
	stepsPerInch: motor steps per inch; typically 100000
	'''
	xy = make_points_list(d,stepsPerInch = stepsPerInch)
	mag = d['amp']

	model_func = create_beam_model(nu,deltaZ)

	p0 = [1e-3,1e-3,pl.pi/4.,6.,6.,1.]

	lowerBounds = [-pl.inf,-pl.inf,0.,0.,0.,0.]
	upperBounds = [pl.inf,pl.inf,2.*pl.pi,pl.inf,pl.inf,pl.inf]
	popt,pcov = scipy.optimize.curve_fit(model_func,xy,mag,p0 = p0,\
										 bounds = (lowerBounds,upperBounds))
	perr = pl.sqrt(pl.diag(pcov))

	print '\n*** Fit beam model ***\n%s' % (d['filename'])
	print 'Central frequency = %.1f GHz' % (nu)
	print 'Window flange to source = %.2f\"' % (deltaZ)
	print '\tx0 = %.1f +- %.1f mm' % (popt[0],perr[0])
	print '\ty0 = %.1f +- %.1f mm' % (popt[1],perr[1])
	print '\tphi0 = %.1f +- %.1f deg.' % (popt[2]*r2d,perr[2]*r2d)
	print '\tw0x = %.1f +- %.1f mm' % (popt[3],perr[3])
	print '\tw0y = %.1f +- %.1f mm' % (popt[4],perr[4])
	print '\tI0 = %.3e +- %.3e' % (popt[5],perr[5])
	
	e = get_ellipticity(popt)
	print 'Ellipticity = %.1f%%' % (e*100.)

	return popt,pcov

def get_popt_beam(d,nu,deltaZ,stepsPerInch = 100000.):
	popt,pcov = fit_beam(d,nu,deltaZ,stepsPerInch = stepsPerInch)
	return popt

def make_dFit_beam(d,popt,nu,deltaZ,smooth = True,stepsPerInch = 100000.):
	'''
	smooth: For the fitted beam, use finer pixel spacing than the data. 
		When False, uses same pixel spacing as data.
	'''
	model_func = create_beam_model(nu,deltaZ)
	dFit = {}
	if smooth:
		xMin = min(d['x'])
		xMax = max(d['x'])
		yMin = min(d['y'])
		yMax = max(d['y'])
		dx = (xMax - xMin)/50.
		dy = (yMax - yMin)/50.
		Xfit,Yfit = pl.meshgrid(pl.arange(xMin,xMax + dx,dx),\
									pl.arange(yMin,yMax + dy,dy))
		nRows,nCols = pl.shape(Xfit)
		dFit['x'] = pl.zeros(nRows*nCols)
		dFit['y'] = pl.zeros(nRows*nCols)
		for i in range(nRows):
			for j in range(nCols):
				dFit['x'][i*nCols + j] = Xfit[i,j]
				dFit['y'][i*nCols + j] = Yfit[i,j]
	else:
		dFit['x'] = d['x']
		dFit['y'] = d['y']
	xyFit = make_points_list(dFit,stepsPerInch = stepsPerInch)
	dFit['amp'] = model_func(xyFit,*popt)    
	return dFit

def make_beam_cuts(d,popt,nu,deltaZ,stepsPerInch = 100000.):
	X,Y,A = make_meshgrid(d,forContour = True) # don't want extra x,y entries
	X *= inch2mm/stepsPerInch # convert X from steps to mm
	Y *= inch2mm/stepsPerInch # conver Y from steps to mm
	
	# find row and col of (x0,y0)
	nRows,nCols = pl.shape(X)
	x0,y0 = popt[0],popt[1]
	def dist(i,j):
		return pl.sqrt((X[i,j]-x0)**2 + (Y[i,j]-y0)**2)
	i0,j0 = 0,0
	r = dist(i0,j0)
	for i in range(nRows):
		for j in range(nCols):
			if dist(i,j) < r:
				r = dist(i,j)
				i0,j0 = i,j
	
	z = deltaZ*inch2mm + zFP2flange

	dData = {}
	dData[0] = {}
	dData[0]['theta'] = r2d*pl.arctan((X[i0,:]-x0)/z)
	dData[0]['amp'] = A[i0,:]
	dData[90] = {}
	dData[90]['theta'] = r2d*pl.arctan((Y[:,j0]-y0)/z)
	dData[90]['amp'] = A[:,j0]

	# make beam cuts for best-fit model
	model_func = create_beam_model(nu,deltaZ)
	xMin = min(X[0,:])
	xMax = max(X[0,:])
	yMin = min(Y[:,0])
	yMax = max(Y[:,0])
	dx = (xMax - xMin)/1e3
	dy = (yMax - yMin)/1e3
	xFit = pl.arange(xMin,xMax + dx,dx)
	yFit = pl.arange(yMin,yMax + dy,dy)
	dFit = {}
	x0data = X[i0,j0] # closest x grid coordinate to x0
	y0data = Y[i0,j0] # closest y grid coordinate to y0
	
	# 0-deg. fit
	xy0 = []
	thetaFit0 = []
	for i in range(len(xFit)):
		xTemp = xFit[i]
		xy0.append((xTemp,y0))
		thetaFit0.append(r2d*pl.arctan((xTemp-x0)/z))
	dFit[0] = {}
	dFit[0]['amp'] = model_func(xy0,*popt)
	dFit[0]['theta'] = thetaFit0

	# 90-deg. fit
	xy90 = []
	thetaFit90 = []
	for i in range(len(yFit)):
		yTemp = yFit[i]
		xy90.append((x0,yTemp))
		thetaFit90.append(r2d*pl.arctan((yTemp-y0)/z))
	dFit[90] = {}
	dFit[90]['amp'] = model_func(xy90,*popt)
	dFit[90]['theta'] = thetaFit90

	# only include 45-deg. cuts if x and y spacing are the same
	if (pl.absolute(X[0,0] - X[0,1]) - pl.absolute(Y[0,0] - Y[1,0]))/pl.absolute(X[0,0] - X[0,1]) <= 1e-9:
		# find starting row/col for 45-deg. cut
		i,j = i0,j0
		while i > 0 and j > 0:
			i -= 1
			j -= 1
		theta45 = []
		A45 = []
		while i < nRows - 1 and j < nCols - 1:
			theta45.append(r2d*pl.sign(X[i,j]-x0)*\
					 pl.arctan(pl.sqrt((X[i,j]-x0)**2 + (Y[i,j]-y0)**2)/z))
			A45.append(A[i,j])
			i += 1
			j += 1
		dData[45] = {}
		dData[45]['theta'] = pl.array(theta45)
		dData[45]['amp'] = pl.array(A45)

		# find starting row/col for 135-deg. cut
		i,j = i0,j0
		while i < nRows - 1 and j > 0:
			i += 1
			j -= 1
		theta135 = []
		A135 = []
		while i > 0 and j < nCols - 1:
			theta135.append(r2d*pl.sign(X[i,j]-x0)*\
					  pl.arctan(pl.sqrt((X[i,j]-x0)**2 + (Y[i,j]-y0)**2)/z))
			A135.append(A[i,j])
			i -= 1
			j += 1
		dData[135] = {}
		dData[135]['theta'] = pl.array(theta135)
		dData[135]['amp'] = pl.array(A135)
	
		# 45-deg. fit
		xyFit45 = []
		thetaFit45 = []
		for i in range(len(xFit)):
			xTemp = xFit[i]
			yTemp = xTemp - x0 + y0
			if xTemp <= xMax and xTemp >= xMin and yTemp <= yMax and \
					yTemp >= yMin:
				xyFit45.append((xTemp,yTemp))
				thetaFit45.append(r2d*pl.sign(xTemp-x0)*\
						 pl.arctan(pl.sqrt((xTemp-x0)**2 + (yTemp-y0)**2)/z))
		dFit[45] = {}
		dFit[45]['theta'] = thetaFit45
		dFit[45]['amp'] = model_func(xyFit45,*popt)
		
		# 135-deg. fit
		xyFit135 = []
		thetaFit135 = []
		for i in range(len(xFit)):
			xTemp = xFit[i]
			yTemp = -(xTemp-x0) + y0
			if xTemp <= xMax and xTemp >= xMin and yTemp <= yMax and \
					yTemp >= yMin:
				xyFit135.append((xTemp,yTemp))
				thetaFit135.append(r2d*pl.sign(xTemp-x0)*\
						 pl.arctan(pl.sqrt((xTemp-x0)**2 + (yTemp-y0)**2)/z))
		dFit[135] = {}
		dFit[135]['theta'] = thetaFit135
		dFit[135]['amp'] = model_func(xyFit135,*popt)
		
		return dData,dFit

def plot_beam_cuts(d,popt,nu,deltaZ,title = None,stepsPerInch = 100000.,plotFit = True,\
					   dB = False,dBMin = -20.,thetaDegMax = 30.,outputFn = None):
	dData,dFit = make_beam_cuts(d,popt,nu,deltaZ,stepsPerInch = stepsPerInch)
	
	pl.figure(figsize = (10,6))

	colorList = ['b','g','r','c']
	i = 0
	def transform(amp):
		if dB:
			return 10.*pl.log10(amp)
		else:
			return amp
	for cut in dData:
		if plotFit:
			pl.plot(dFit[cut]['theta'],transform(dFit[cut]['amp']),\
						color = colorList[i])
		pl.plot(dData[cut]['theta'],transform(dData[cut]['amp']),\
					color = colorList[i],linestyle = 'none',marker = 'o',\
					label = r'$%i^\circ$' % cut)
		i += 1
	pl.grid()
	pl.xlabel(r'Polar angle from beam center ($^\circ$)')
	if plotFit:
		s1 = 'normalized to fit peak'
	else:
		s1 = 'arbitrary units'
	if dB:
		yLabel = r'Power (dB, %s)' % (s1)
		pl.ylim(ymin = dBMin)
	else:
		yLabel = r'Power (%s)' % (s1)
		pl.ylim(ymin = 0.)
	pl.ylabel(yLabel)
	pl.legend(loc = 'best')
	pl.xlim(-thetaDegMax,thetaDegMax)
	if title != None:
		pl.title(title)
	if outputFn != None:
		pl.savefig(outputFn)
	else:
		pl.show()
	pickle.dump(dData, open("cuts_5p3mm_90.pkl", "wb"))
	pickle.dump(dFit, open("fits_5p3mm_90.pkl", "wb"))	
	print("asdfasdfqetn")


def make_figure_beam_fit(fn,nu,title = None, deltaZ = 4.41,stepsPerInch = 100000.,\
							 thetaDegTick = 10.,dB = False,dBMin = -20.,\
							 plotFit_beamCut = True,thetaDegMax = 25.,\
							 outputFnBeam = None,outputFnRes = None,\
							 outputFnCuts = None,plotContour = True,\
							 xlimTup = None,ylimTup = None):
	'''
	d: dictionary containing beam-map data
	nu: central frequency (GHz)
	deltaZ: distance from window flange to beam-mapper aperture (inches)
	stepsPerInch: motor steps per inch; typically 100000
	'''
	d = extract_raw_beam(fn)
	popt = get_popt_beam(d,nu,deltaZ,stepsPerInch = stepsPerInch)
	I0 = popt[5]
	d['amp'] /= I0 # peak normalize
	popt[5] = 1. # maintain peak normalization in subsequent calls to the fit
	
	if plotContour:
		dFitSmooth = make_dFit_beam(d,popt,nu,deltaZ,stepsPerInch = stepsPerInch)
	else:
		dFitSmooth = None

	e = get_ellipticity(popt)

	# create angular axis ticks and labels
	x0,y0 = popt[0],popt[1]
	x0s = stepsPerInch*x0/inch2mm
	y0s = stepsPerInch*y0/inch2mm
	xMin = min(d['x'])
	xMax = max(d['x'])
	yMin = min(d['y'])
	yMax = max(d['y'])
	z = stepsPerInch*deltaZ + stepsPerInch*zFP2flange/inch2mm
	thetaMinX = pl.arctan((xMin-x0s)/z)
	thetaMaxX = pl.arctan((xMax-x0s)/z)
	thetaMinY = pl.arctan((yMin-y0s)/z)
	thetaMaxY = pl.arctan((yMax-y0s)/z)
	thetaTick = thetaDegTick*d2r
	iMinX = int(thetaMinX/thetaTick)
	iMaxX = int(thetaMaxX/thetaTick)
	iMinY = int(thetaMinY/thetaTick)
	iMaxY = int(thetaMaxY/thetaTick)
	xTicks = []
	xTickLabels = []

	for i in range(iMinX,iMaxX + 1):
		xTicks.append(z*pl.tan(i*thetaTick) + x0s)
		xTickLabels.append(r'$%i^\circ$' % (i*thetaDegTick))
	yTicks = []
	yTickLabels = []
	for i in range(iMinY,iMaxY + 1):
		yTicks.append(z*pl.tan(i*thetaTick) + y0s)
		yTickLabels.append(r'$%i^\circ$' % (i*thetaDegTick))

	if plotContour:
		s2 = 'normalized to peak of fit'
	else:
		s2 = 'arbitrary units'

	if dB:
		dBref = 1.
		cLabel = r'Power (dB, %s)' % (s2)
	else: 
		dBref = None
		cLabel = r'Power (%s)' % (s2)


	make_figure_beam(d,dContour = dFitSmooth,\
						 title = title, contourLabel = r'$\epsilon = %.1f\%%$' % (e*100.),\
						 cLabel = cLabel,xTicks = xTicks,\
						 xTickLabels = xTickLabels,yTicks = yTicks,\
						 yTickLabels = yTickLabels,\
						 xLabel = r'Polar angle',\
						 yLabel = r'Polar angle',\
						 dBref = dBref,dBMin = dBMin,outputFn = outputFnBeam,\
						 xlimTup = xlimTup,ylimTup = ylimTup )

	dRes = {}
	dRes['x'] = d['x']
	dRes['y'] = d['y']
	dFitDiscrete = make_dFit_beam(d,popt,nu,deltaZ,\
									  stepsPerInch = stepsPerInch,\
									  smooth = False)
	dRes['amp'] = dFitDiscrete['amp'] - d['amp']
	
	make_figure_beam(dRes,\
					 title =  title, cLabel = r'Residual (fit - data, relative to fit peak)',\
					 xTicks = xTicks,xTickLabels = xTickLabels,\
					 yTicks = yTicks,yTickLabels = yTickLabels,\
					 xLabel = r'Polar angle from beam center',\
					 yLabel = r'Polar angle from beam center',linMin = None,\
					 outputFn = outputFnRes,xlimTup = xlimTup,ylimTup = ylimTup)
	
	plot_beam_cuts(d,popt,nu,deltaZ, title = title, stepsPerInch = stepsPerInch,\
					   plotFit = plotFit_beamCut,dB = dB,dBMin = dBMin,\
					   thetaDegMax = thetaDegMax,outputFn = outputFnCuts)
	
	return d,popt
