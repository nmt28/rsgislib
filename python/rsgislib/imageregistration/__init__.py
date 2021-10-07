#!/usr/bin/env python
"""
The image registration module contains algorithms for generating tie points matching two image and warping images based on tie points.

There are two algorithms are available for registration: basic, and singlelayer. The single layer algorithm is a simplified version of the algorithm proposed in:

Bunting, P.J., Labrosse, F. & Lucas, R.M., 2010. A multi-resolution area-based technique for automatic multi-modal image registration. Image and Vision Computing, 28(8), pp.1203-1219.


Image distance metrics:

    * METRIC_EUCLIDEAN = 1
    * METRIC_SQDIFF = 2
    * METRIC_MANHATTEN = 3
    * METRIC_CORELATION = 4


GCP Output Types:

    * TYPE_ENVI_IMG2IMG = 1
    * TYPE_ENVI_IMG2MAP = 2
    * TYPE_RSGIS_IMG2MAP = 3
    * TYPE_RSGIS_MAPOFFS = 4


"""

# import the C++ extension into this level
from ._imageregistration import *

import rsgislib

METRIC_EUCLIDEAN = 1
METRIC_SQDIFF = 2
METRIC_MANHATTEN = 3
METRIC_CORELATION = 4

TYPE_ENVI_IMG2IMG = 1
TYPE_ENVI_IMG2MAP = 2
TYPE_RSGIS_IMG2MAP = 3
TYPE_RSGIS_MAPOFFS = 4



def warp_with_gcps_with_gdal(inRefImg, inProcessImg, outImg, gdalformat, interpMethod, useTPS=False, usePoly=True, polyOrder=3, useMutliThread=False):
    """
A utility function to warp an image file (inProcessImg) using GCPs defined within the image header - this is the same as using the 
gdalwarp utility. However, the output image will have the same pixel grid and dimensions as the input reference image (inRefImg).

Where:

:param inRefImg: is the input reference image to which the processing image is to resampled to.
:param inProcessImg: is the image which is to be resampled.
:param outImg: is the output image file.
:param gdalformat: is the gdal format for the output image.
:param interpMethod: is the interpolation method used to resample the image [bilinear, lanczos, cubicspline, nearestneighbour, cubic, average, mode]
:param useTPS: is a boolean specifying that the thin plated splines method of warping should be used (i.e., rubbersheet); Default False.
:param usePoly: is a boolean specifying that a polynomial method of warpping is used; Default True
:param polyOrder: is the order of the polynomial used to represent the transformation (1, 2 or 3). Only used if usePoly=True
:param useMutliThread: is a boolean specifying whether multiple processing cores should be used for the warping.

"""
    import rsgislib.imageutils
    from osgeo import gdal
     
    if not rsgislib.imageutils.has_gcps(inProcessImg):
        raise Exception("Input process image does not have GCPs within it's header - this is required.")

    numBands = rsgislib.imageutils.get_image_band_count(inProcessImg)
    noDataVal = rsgislib.imageutils.getImageNoDataValue(inProcessImg)
    datatype = rsgislib.imageutils.get_rsgislib_datatype_from_img(inProcessImg)
    
    interpolationMethod = gdal.GRA_NearestNeighbour
    if interpMethod == 'bilinear':
        interpolationMethod = gdal.GRA_Bilinear 
    elif interpMethod == 'lanczos':
        interpolationMethod = gdal.GRA_Lanczos 
    elif interpMethod == 'cubicspline':
        interpolationMethod = gdal.GRA_CubicSpline 
    elif interpMethod == 'nearestneighbour':
        interpolationMethod = gdal.GRA_NearestNeighbour 
    elif interpMethod == 'cubic':
        interpolationMethod = gdal.GRA_Cubic
    elif interpMethod == 'average':
        interpolationMethod = gdal.GRA_Average
    elif interpMethod == 'mode':
        interpolationMethod = gdal.GRA_Mode
    else:
        raise Exception("Interpolation method was not recognised or known.")
    
    rsgislib.imageutils.create_copy_img(inRefImg, outImg, numBands, 0, gdalformat, datatype)

    inFile = gdal.Open(inProcessImg, gdal.GA_ReadOnly)
    outFile = gdal.Open(outImg, gdal.GA_Update)

    try:
        import tqdm
        pbar = tqdm.tqdm(total=100)
        callback = lambda *args, **kw: pbar.update()
    except:
        callback = gdal.TermProgress

    wrpOpts = None
    if useTPS:
        wrpOpts = gdal.WarpOptions(resampleAlg=interpolationMethod, srcNodata=noDataVal, dstNodata=noDataVal, multithread=useMutliThread, tps=useTPS, callback=callback)
    elif usePoly:
        wrpOpts = gdal.WarpOptions(resampleAlg=interpolationMethod, srcNodata=noDataVal, dstNodata=noDataVal, multithread=useMutliThread, polynomialOrder=polyOrder, callback=callback)
    else:
        warpOptions = None    
    
    gdal.Warp(outFile, inFile, options=wrpOpts)
        
    inFile = None
    outFile = None



