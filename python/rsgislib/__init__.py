#!/usr/bin/env python
"""
This namespace contains rsgislib Python bindings 

Please be aware that the following variables have been 
defined to match enums within RSGISLib.

Data Types for images:

    * TYPE_UNDEFINED = 0
    * TYPE_8INT = 1
    * TYPE_16INT = 2
    * TYPE_32INT = 3
    * TYPE_64INT = 4
    * TYPE_8UINT = 5
    * TYPE_16UINT = 6
    * TYPE_32UINT = 7
    * TYPE_64UINT = 8
    * TYPE_32FLOAT = 9
    * TYPE_64FLOAT = 10

Methods for the Maximum Likelihood Classifier:

    * METHOD_SAMPLES = 0        # as calculated by ML
    * METHOD_AREA = 1           # priors set by the relative area
    * METHOD_EQUAL = 2          # priors all equal
    * METHOD_USERDEFINED = 3    # priors passed in to function
    * METHOD_WEIGHTED = 4       # priors by area but with a weight applied

Shape indexes used with RasterGIS:

    * SHAPE_SHAPENA = 0
    * SHAPE_SHAPEAREA = 1
    * SHAPE_ASYMMETRY = 2
    * SHAPE_BORDERINDEX = 3
    * SHAPE_BORDERLENGTH = 4
    * SHAPE_COMPACTNESS = 5
    * SHAPE_DENSITY = 6
    * SHAPE_ELLIPTICFIT = 7
    * SHAPE_LENGTH = 8
    * SHAPE_LENGTHWIDTH = 9
    * SHAPE_WIDTH = 10
    * SHAPE_MAINDIRECTION = 11
    * SHAPE_RADIUSLARGESTENCLOSEDELLIPSE = 12
    * SHAPE_RADIUSSMALLESTENCLOSEDELLIPSE = 13
    * SHAPE_RECTANGULARFIT = 14
    * SHAPE_ROUNDNESS = 15
    * SHAPE_SHAPEINDEX = 16

Methods of initialising KMEANS:

    * INITCLUSTER_RANDOM = 0
    * INITCLUSTER_DIAGONAL_FULL = 1
    * INITCLUSTER_DIAGONAL_STDDEV = 2
    * INITCLUSTER_DIAGONAL_FULL_ATTACH = 3
    * INITCLUSTER_DIAGONAL_STDDEV_ATTACH = 4
    * INITCLUSTER_KPP = 5
    
    
Methods of calculating distance:

    * DIST_UNDEFINED = 0
    * DIST_EUCLIDEAN = 1
    * DIST_MAHALANOBIS = 2
    * DIST_MANHATTEN = 3
    * DIST_MINKOWSKI = 4
    * DIST_CHEBYSHEV = 5
    * DIST_MUTUALINFO = 6
    
Methods of summerising data:

    * SUMTYPE_UNDEFINED = 0
    * SUMTYPE_MODE = 1
    * SUMTYPE_MEAN = 2
    * SUMTYPE_MEDIAN = 3
    * SUMTYPE_MIN = 4
    * SUMTYPE_MAX = 5
    * SUMTYPE_STDDEV = 6
    * SUMTYPE_COUNT = 7
    * SUMTYPE_RANGE = 8
    * SUMTYPE_SUM = 9
    
Constants specifying how bands should be treated when sharpening (see rsgislib.imageutils)
    * SHARP_RES_IGNORE = 0
    * SHARP_RES_LOW = 1
    * SHARP_RES_HIGH = 2

"""
from __future__ import print_function

import os
import time
import datetime
import math
import sys

import osgeo.osr as osr
import osgeo.ogr as ogr
import osgeo.gdal as gdal

gdal.UseExceptions()

TYPE_UNDEFINED = 0
TYPE_8INT = 1
TYPE_16INT = 2
TYPE_32INT = 3
TYPE_64INT = 4
TYPE_8UINT = 5
TYPE_16UINT = 6
TYPE_32UINT = 7
TYPE_64UINT = 8
TYPE_32FLOAT = 9
TYPE_64FLOAT = 10

DIST_UNDEFINED = 0
DIST_EUCLIDEAN = 1
DIST_MAHALANOBIS = 2
DIST_MANHATTEN = 3
DIST_MINKOWSKI = 4
DIST_CHEBYSHEV = 5
DIST_MUTUALINFO = 6

SUMTYPE_UNDEFINED = 0
SUMTYPE_MODE = 1
SUMTYPE_MEAN = 2
SUMTYPE_MEDIAN = 3
SUMTYPE_MIN = 4
SUMTYPE_MAX = 5
SUMTYPE_STDDEV = 6
SUMTYPE_COUNT = 7
SUMTYPE_RANGE = 8
SUMTYPE_SUM = 9

METHOD_SAMPLES = 0      # as calculated by ML
METHOD_AREA = 1         # priors set by the relative area
METHOD_EQUAL = 2        # priors all equal
METHOD_USERDEFINED = 3  # priors passed in to function
METHOD_WEIGHTED = 4     # priors by area but with a weight applied

SHAPE_SHAPENA = 0
SHAPE_SHAPEAREA = 1
SHAPE_ASYMMETRY = 2
SHAPE_BORDERINDEX = 3
SHAPE_BORDERLENGTH = 4
SHAPE_COMPACTNESS = 5
SHAPE_DENSITY = 6
SHAPE_ELLIPTICFIT = 7
SHAPE_LENGTH = 8
SHAPE_LENGTHWIDTH = 9
SHAPE_WIDTH = 10
SHAPE_MAINDIRECTION = 11
SHAPE_RADIUSLARGESTENCLOSEDELLIPSE = 12
SHAPE_RADIUSSMALLESTENCLOSEDELLIPSE = 13
SHAPE_RECTANGULARFIT = 14
SHAPE_ROUNDNESS = 15
SHAPE_SHAPEINDEX = 16

INITCLUSTER_RANDOM = 0
INITCLUSTER_DIAGONAL_FULL = 1
INITCLUSTER_DIAGONAL_STDDEV = 2
INITCLUSTER_DIAGONAL_FULL_ATTACH = 3
INITCLUSTER_DIAGONAL_STDDEV_ATTACH = 4
INITCLUSTER_KPP = 5

SHARP_RES_IGNORE = 0
SHARP_RES_LOW = 1
SHARP_RES_HIGH = 2


def getRSGISLibVersion():
    """ Calls rsgis-config to get the version number. """

    # Try calling rsgis-config to get minor version number
    try:
        import subprocess
        out = subprocess.Popen('rsgis-config --version',shell=True,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = out.communicate()
        versionStr = stdout.decode()
        versionStr = versionStr.split('\n')[0]
    except Exception:
        versionStr = 'NA'
    return(versionStr)

__version__ = getRSGISLibVersion()

py_sys_version_str = "{}.{}".format(sys.version_info.major, sys.version_info.minor)
py_sys_version_flt = float(py_sys_version_str)


class RSGISPyException(Exception):
    """
    A class representing the RSGIS exception.
    """
    
    def __init__(self, value):
        """
        Init for the RSGISPyException class
        """
        self.value = value
        
    def __str__(self):
        """
        Return a string representation of the exception
        """
        return repr(self.value)


class RSGISGDALErrorHandler(object):
    """
    A class representing a generic GDAL Error Handler which
    can be used to pick up GDAL warnings rather than just
    failure errors.
    """

    def __init__(self):
        """
        Init for RSGISGDALErrorHandler. Class attributes are err_level, err_no and err_msg

        """
        from osgeo import gdal
        self.err_level = gdal.CE_None
        self.err_no = 0
        self.err_msg = ''

    def handler(self, err_level, err_no, err_msg):
        """
        The handler function which is called with the error information.

        :param err_level: The level of the error
        :param err_no: The error number
        :param err_msg: The message (string) associated with the error.

        """
        self.err_level = err_level
        self.err_no = err_no
        self.err_msg = err_msg


class RSGISPyUtils (object):
    """
    A class with useful utilities within RSGISLib.
    """
    
    def getFileExtension(self, gdalformat):
        """
        A function to get the extension for a given file format 
        (NOTE, currently only KEA, GTIFF, HFA, PCI and ENVI are supported).

        :return: string

        """
        ext = ".NA"
        if gdalformat.lower() == "kea":
            ext = ".kea"
        elif gdalformat.lower() == "gtiff":
            ext = ".tif"
        elif gdalformat.lower() == "hfa":
            ext = ".img"
        elif gdalformat.lower() == "envi":
            ext = ".env"
        elif gdalformat.lower() == "pcidsk":
            ext = ".pix"
        else:
            raise RSGISPyException("The extension for the gdalformat specified is unknown.")
        return ext
    
    def getGDALFormatFromExt(self, fileName):
        """
        Get GDAL format, based on filename

        :return: string

        """
        gdalStr = ''
        extension = os.path.splitext(fileName)[-1] 
        if extension == '.env':
            gdalStr = 'ENVI'
        elif extension == '.kea':
            gdalStr = 'KEA'
        elif extension == '.tif' or extension == '.tiff':
            gdalStr = 'GTiff'
        elif extension == '.img':
            gdalStr = 'HFA'
        elif extension == '.pix':
            gdalStr = 'PCIDSK'
        else:
            raise RSGISPyException('Type not recognised')
        
        return gdalStr

    def set_envvars_lzw_gtiff_outs(self, bigtiff=True):
        """
        Set environmental variables such that outputted
        GeoTIFF files are outputted as tiled and compressed.

        :param bigtiff: If True GTIFF files will be outputted
                        in big tiff format.

        """
        if bigtiff:
            os.environ["RSGISLIB_IMG_CRT_OPTS_GTIFF"] = "TILED=YES:COMPRESS=LZW:BIGTIFF=YES"
        else:
            os.environ["RSGISLIB_IMG_CRT_OPTS_GTIFF"] = "TILED=YES:COMPRESS=LZW"

    def get_file_basename(self, filepath, checkvalid=False, n_comps=0):
        """
        Uses os.path module to return file basename (i.e., path and extension removed)

        :param filepath: string for the input file name and path
        :param checkvalid: if True then resulting basename will be checked for punctuation
                           characters (other than underscores) and spaces, punctuation
                           will be either removed and spaces changed to an underscore.
                           (Default = False)
        :param n_comps: if > 0 then the resulting basename will be split using underscores
                        and the return based name will be defined using the n_comps
                        components split by under scores.
        :return: basename for file

        """
        import string
        basename = os.path.splitext(os.path.basename(filepath))[0]
        if checkvalid:
            basename = basename.replace(' ', '_')
            for punct in string.punctuation:
                if (punct != '_') and (punct != '-'):
                    basename = basename.replace(punct, '')
        if n_comps > 0:
            basename_split = basename.split('_')
            if len(basename_split) < n_comps:
                raise RSGISPyException(
                    "The number of components specified is more than the number of components in the basename.")
            out_basename = ""
            for i in range(n_comps):
                if i == 0:
                    out_basename = basename_split[i]
                else:
                    out_basename = out_basename + '_' + basename_split[i]
            basename = out_basename
        return basename

    def get_dir_name(self, in_file):
        """
        A function which returns just the name of the directory of the input file without the rest of the path.

        :param in_file: string for the input file name and path
        :return: directory name
        """
        in_file = os.path.abspath(in_file)
        dir_path = os.path.dirname(in_file)
        dir_name = os.path.basename(dir_path)
        return dir_name

    def getRSGISLibDataTypeFromImg(self, inImg):
        """
        Returns the rsgislib datatype ENUM (e.g., rsgislib.TYPE_8INT) 
        for the inputted raster file

        :return: int

        """
        raster = gdal.Open(inImg, gdal.GA_ReadOnly)
        if raster == None:
            raise RSGISPyException('Could not open raster image: \'' + inImg+ '\'')
        band = raster.GetRasterBand(1)
        if band == None:
            raise RSGISPyException('Could not open raster band 1 in image: \'' + inImg+ '\'')
        gdal_dtype = gdal.GetDataTypeName(band.DataType)
        raster = None
        return self.getRSGISLibDataType(gdal_dtype)
        
    def getGDALDataTypeFromImg(self, inImg):
        """
        Returns the GDAL datatype ENUM (e.g., GDT_Float32) for the inputted raster file.

        :return: ints

        """
        raster = gdal.Open(inImg, gdal.GA_ReadOnly)
        if raster == None:
            raise RSGISPyException('Could not open raster image: \'' + inImg+ '\'')
        band = raster.GetRasterBand(1)
        if band == None:
            raise RSGISPyException('Could not open raster band 1 in image: \'' + inImg+ '\'')
        gdal_dtype = band.DataType
        raster = None
        return gdal_dtype
        
    def getGDALDataTypeNameFromImg(self, inImg):
        """
        Returns the GDAL datatype ENUM (e.g., GDT_Float32) for the inputted raster file.

        :return: int

        """
        raster = gdal.Open(inImg, gdal.GA_ReadOnly)
        if raster == None:
            raise RSGISPyException('Could not open raster image: \'' + inImg+ '\'')
        band = raster.GetRasterBand(1)
        if band == None:
            raise RSGISPyException('Could not open raster band 1 in image: \'' + inImg+ '\'')
        dtypeName = gdal.GetDataTypeName(band.DataType)
        raster = None
        return dtypeName
    
    def deleteFileWithBasename(self, filePath):
        """
        Function to delete all the files which have a path
        and base name defined in the filePath attribute.

        """
        import glob
        baseName = os.path.splitext(filePath)[0]
        fileList = glob.glob(baseName+str('.*'))
        for file in fileList:
            print("Deleting file: " + str(file))
            os.remove(file)
                
    def deleteDIR(self, dirPath):
        """
        A function which will delete a directory, if files and other directories
        are within the path specified they will be recursively deleted as well.
        So be careful you don't delete things within meaning it.

        """
        for root, dirs, files in os.walk(dirPath, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(dirPath)
        print("Deleted " + dirPath)
        
    def renameGDALLayer(self, cFileName, oFileName):
        """
        Rename all the files associated with a GDAL layer.

        :param cFileName: The current name of the GDAL layer.
        :param oFileName: The output name of the GDAL layer.

        """
        layerDS = gdal.Open(cFileName, gdal.GA_ReadOnly)
        gdalDriver = layerDS.GetDriver()
        layerDS = None
        gdalDriver.Rename(oFileName, cFileName)

    def getRSGISLibDataType(self, gdaltype):
        """
        Convert from GDAL data type string to RSGISLib data type int.

        :return: int

        """
        gdaltype = gdaltype.lower()
        if gdaltype == 'int8':
            return TYPE_8INT
        elif gdaltype == 'int16':
            return TYPE_16INT
        elif gdaltype == 'int32':
            return TYPE_32INT
        elif gdaltype == 'int64':
            return TYPE_64INT
        elif gdaltype == 'byte' or gdaltype == 'uint8':
            return TYPE_8UINT
        elif gdaltype == 'uint16':
            return TYPE_16UINT
        elif gdaltype == 'uint32':
            return TYPE_32UINT
        elif gdaltype == 'uint64':
            return TYPE_64UINT
        elif gdaltype == 'float32':
            return TYPE_32FLOAT
        elif gdaltype == 'float64':
            return TYPE_64FLOAT
        else:
            raise RSGISPyException("The data type '" + str(gdaltype) + "' is unknown / not supported.")

    def getGDALDataType(self, rsgislib_datatype):
        """
        Convert from RSGIS data type to GDAL data type int.

        :return: int

        """
        if rsgislib_datatype == TYPE_16INT:
            return gdal.GDT_Int16
        elif rsgislib_datatype == TYPE_32INT:
            return gdal.GDT_Int32
        elif rsgislib_datatype == TYPE_8UINT:
            return gdal.GDT_Byte
        elif rsgislib_datatype == TYPE_16UINT:
            return gdal.GDT_UInt16
        elif rsgislib_datatype == TYPE_32UINT:
            return gdal.GDT_UInt32
        elif rsgislib_datatype == TYPE_32FLOAT:
            return gdal.GDT_Float32
        elif rsgislib_datatype == TYPE_64FLOAT:
            return gdal.GDT_Float64
        else:
            raise RSGISPyException("The data type '" + str(rsgislib_datatype) + "' is unknown / not supported.")

    def getNumpyDataType(self, rsgislib_datatype):
        """
        Convert from RSGISLib data type to numpy datatype

        :param rsgis_datatype:
        :return: numpy datatype
        """
        import numpy
        numpyDT = numpy.float32
        if rsgislib_datatype == TYPE_8INT:
            numpyDT = numpy.int8
        elif rsgislib_datatype == TYPE_16INT:
            numpyDT = numpy.int16
        elif rsgislib_datatype == TYPE_32INT:
            numpyDT = numpy.int32
        elif rsgislib_datatype == TYPE_64INT:
            numpyDT = numpy.int64
        elif rsgislib_datatype == TYPE_8UINT:
            numpyDT = numpy.uint8
        elif rsgislib_datatype == TYPE_16UINT:
            numpyDT = numpy.uint16
        elif rsgislib_datatype == TYPE_32UINT:
            numpyDT = numpy.uint32
        elif rsgislib_datatype == TYPE_64UINT:
            numpyDT = numpy.uint64
        elif rsgislib_datatype == TYPE_32FLOAT:
            numpyDT = numpy.float32
        elif rsgislib_datatype == TYPE_64FLOAT:
            numpyDT = numpy.float64
        else:
            raise Exception('Datatype was not recognised.')
        return numpyDT

    def getNumpyCharCodesDataType(self, rsgislib_datatype):
        """
        Convert from RSGISLib data type to numpy datatype

        :param rsgis_datatype:
        :return: numpy character code datatype
        """
        import numpy
        numpyDT = numpy.dtype(numpy.float32).char
        if rsgislib_datatype == TYPE_8INT:
            numpyDT = numpy.dtype(numpy.int8).char
        elif rsgislib_datatype == TYPE_16INT:
            numpyDT = numpy.dtype(numpy.int16).char
        elif rsgislib_datatype == TYPE_32INT:
            numpyDT = numpy.dtype(numpy.int32).char
        elif rsgislib_datatype == TYPE_64INT:
            numpyDT = numpy.dtype(numpy.int64).char
        elif rsgislib_datatype == TYPE_8UINT:
            numpyDT = numpy.dtype(numpy.uint8).char
        elif rsgislib_datatype == TYPE_16UINT:
            numpyDT = numpy.dtype(numpy.uint16).char
        elif rsgislib_datatype == TYPE_32UINT:
            numpyDT = numpy.dtype(numpy.uint32).char
        elif rsgislib_datatype == TYPE_64UINT:
            numpyDT = numpy.dtype(numpy.uint64).char
        elif rsgislib_datatype == TYPE_32FLOAT:
            numpyDT = numpy.dtype(numpy.float32).char
        elif rsgislib_datatype == TYPE_64FLOAT:
            numpyDT = numpy.dtype(numpy.float64).char
        else:
            raise Exception('Datatype was not recognised.')
        return numpyDT
    
    def getImageRes(self, inImg):
        """
        A function to retrieve the image resolution.

        :return: xRes, yRes

        """
        rasterDS = gdal.Open(inImg, gdal.GA_ReadOnly)
        if rasterDS == None:
            raise RSGISPyException('Could not open raster image: \'' + inImg+ '\'')
        
        geotransform = rasterDS.GetGeoTransform()
        xRes = geotransform[1]
        yRes = geotransform[5]
        if yRes < 0:
            yRes = yRes * -1
        rasterDS = None
        return xRes, yRes
    
    def doImageResMatch(self, img1, img2):
        """
        A function to test whether two images have the same
        image pixel resolution.

        :return: boolean

        """
        img1XRes, img1YRes = self.getImageRes(img1)
        img2XRes, img2YRes = self.getImageRes(img2)

        return ((img1XRes == img2XRes) and (img1YRes == img2YRes))
    
    def getImageSize(self, inImg):
        """
        A function to retrieve the image size in pixels.

        :return: xSize, ySize

        """
        rasterDS = gdal.Open(inImg, gdal.GA_ReadOnly)
        if rasterDS == None:
            raise RSGISPyException('Could not open raster image: \'' + inImg+ '\'')
        
        xSize = rasterDS.RasterXSize
        ySize = rasterDS.RasterYSize
        rasterDS = None
        return xSize, ySize
        
    def getImageBBOX(self, inImg):
        """
        A function to retrieve the bounding box in the spatial 
        coordinates of the image.

        :return: (MinX, MaxX, MinY, MaxY)

        """
        rasterDS = gdal.Open(inImg, gdal.GA_ReadOnly)
        if rasterDS == None:
            raise RSGISPyException('Could not open raster image: \'' + inImg+ '\'')
        
        xSize = rasterDS.RasterXSize
        ySize = rasterDS.RasterYSize
        
        geotransform = rasterDS.GetGeoTransform()
        tlX = geotransform[0]
        tlY = geotransform[3]
        xRes = geotransform[1]
        yRes = geotransform[5]
        if yRes < 0:
            yRes = yRes * -1
        rasterDS = None
        
        brX = tlX + (xRes * xSize)
        brY = tlY - (yRes * ySize)
        
        return [tlX, brX, brY, tlY]
    
    def getImageBBOXInProj(self, inImg, outEPSG):
        """
        A function to retrieve the bounding box in the spatial 
        coordinates of the image.

        :return: (MinX, MaxX, MinY, MaxY)

        """
        inProjWKT = self.getWKTProjFromImage(inImg)
        inSpatRef = osr.SpatialReference()
        inSpatRef.ImportFromWkt(inProjWKT)
        
        outSpatRef = osr.SpatialReference()
        outSpatRef.ImportFromEPSG(int(outEPSG))

        img_bbox = self.getImageBBOX(inImg)
        reproj_img_bbox = self.reprojBBOX(img_bbox, inSpatRef, outSpatRef)
        return reproj_img_bbox
        
    def reprojBBOX(self, bbox, inProjObj, outProjObj):
        """
        A function to reproject a bounding box.

        :param bbox: input bounding box (MinX, MaxX, MinY, MaxY)
        :param inProjObj: an osr.SpatialReference() object representing input projection.
        :param outProjObj: an osr.SpatialReference() object representing output projection.

        :return: (MinX, MaxX, MinY, MaxY)

        """
        tlX = bbox[0]
        tlY = bbox[3]
        trX = bbox[1]
        trY = bbox[3]
        brX = bbox[1]
        brY = bbox[2]
        blX = bbox[0]
        blY = bbox[2]

        out_tlX, out_tlY = self.reprojPoint(inProjObj, outProjObj, tlX, tlY)
        out_trX, out_trY = self.reprojPoint(inProjObj, outProjObj, trX, trY)
        out_brX, out_brY = self.reprojPoint(inProjObj, outProjObj, brX, brY)
        out_blX, out_blY = self.reprojPoint(inProjObj, outProjObj, blX, blY)

        minX = out_tlX
        if out_blX < minX:
            minX = out_blX

        maxX = out_brX
        if out_trX > maxX:
            maxX = out_trX

        minY = out_brY
        if out_blY < minY:
            minY = out_blY

        maxY = out_tlY
        if out_trY > maxY:
            maxY = out_trY

        return [minX, maxX, minY, maxY]

    def reprojBBOX_epsg(self, bbox, inEPSG, outEPSG):
        """
        A function to reproject a bounding box.

        :param bbox: input bounding box (MinX, MaxX, MinY, MaxY)
        :param inEPSG: an EPSG code representing input projection.
        :param outEPSG: an EPSG code representing output projection.
        :return: (MinX, MaxX, MinY, MaxY)

        """
        inProjObj = osr.SpatialReference()
        inProjObj.ImportFromEPSG(int(inEPSG))

        outProjObj = osr.SpatialReference()
        outProjObj.ImportFromEPSG(int(outEPSG))

        out_bbox = self.reprojBBOX(bbox, inProjObj, outProjObj)
        return out_bbox

    def do_bboxes_intersect(self, bbox1, bbox2):
        """
        A function which tests whether two bboxes (MinX, MaxX, MinY, MaxY) intersect.

        :param bbox1: The first bounding box (MinX, MaxX, MinY, MaxY)
        :param bbox2: The second bounding box (MinX, MaxX, MinY, MaxY)
        :return: boolean (True they intersect; False they do not intersect)

        """
        x_min = 0
        x_max = 1
        y_min = 2
        y_max = 3
        intersect = ((bbox1[x_max] > bbox2[x_min]) and (bbox2[x_max] > bbox1[x_min]) and (
                    bbox1[y_max] > bbox2[y_min]) and (bbox2[y_max] > bbox1[y_min]))
        return intersect

    def does_bbox_contain(self, bbox1, bbox2):
        """
        A function which tests whether bbox1 contains bbox2.

        :param bbox1: The first bounding box (MinX, MaxX, MinY, MaxY)
        :param bbox2: The second bounding box (MinX, MaxX, MinY, MaxY)
        :return: boolean (True bbox1 contains bbox2; False bbox1 does not contain bbox2)

        """
        x_min = 0
        x_max = 1
        y_min = 2
        y_max = 3
        contains = ((bbox1[x_min] < bbox2[x_min]) and (bbox1[x_max] > bbox2[x_max]) and (
                    bbox1[y_min] < bbox2[y_min]) and (bbox1[y_max] > bbox2[y_max]))
        return contains

    def calc_bbox_area(self, bbox):
        """
        Calculate the area of the bbox.

        :param bbox: bounding box (MinX, MaxX, MinY, MaxY)
        :return: area in projection of the bbox.

        """
        # width x height
        return (bbox[1] - bbox[0]) * (bbox[3] - bbox[2])

    def bbox_equal(self, bbox1, bbox2):
        """
        A function which tests whether two bboxes (xMin, xMax, yMin, yMax) are equal.

        :param bbox1: is a bbox (xMin, xMax, yMin, yMax)
        :param bbox2: is a bbox (xMin, xMax, yMin, yMax)
        :return: boolean

        """
        bbox_eql = False
        if (bbox1[0] == bbox2[0]) and (bbox1[1] == bbox2[1]) and (bbox1[2] == bbox2[2]) and (bbox1[3] == bbox2[3]):
            bbox_eql = True
        return bbox_eql

    def bbox_intersection(self, bbox1, bbox2):
        """
        A function which calculates the intersection of the two bboxes (xMin, xMax, yMin, yMax).

        :param bbox1: is a bbox (xMin, xMax, yMin, yMax)
        :param bbox2: is a bbox (xMin, xMax, yMin, yMax)
        :return: bbox (xMin, xMax, yMin, yMax)

        """
        if not self.do_bboxes_intersect(bbox1, bbox2):
            raise Exception("Bounding Boxes do not intersect.")

        xMinOverlap = bbox1[0]
        xMaxOverlap = bbox1[1]
        yMinOverlap = bbox1[2]
        yMaxOverlap = bbox1[3]

        if bbox2[0] > xMinOverlap:
            xMinOverlap = bbox2[0]

        if bbox2[1] < xMaxOverlap:
            xMaxOverlap = bbox2[1]

        if bbox2[2] > yMinOverlap:
            yMinOverlap = bbox2[2]

        if bbox2[3] < yMaxOverlap:
            yMaxOverlap = bbox2[3]

        return [xMinOverlap, xMaxOverlap, yMinOverlap, yMaxOverlap]

    def bboxes_intersection(self, bboxes):
        """
        A function to find the intersection between a list of
        bboxes.

        :param bboxes: a list of bboxes [(xMin, xMax, yMin, yMax)]
        :return: bbox (xMin, xMax, yMin, yMax)

        """
        if len(bboxes) == 1:
            return bboxes[0]
        elif len(bboxes) == 2:
            return self.bbox_intersection(bboxes[0], bboxes[1])

        inter_bbox = bboxes[0]
        for bbox in bboxes[1:]:
            inter_bbox = self.bbox_intersection(inter_bbox, bbox)
        return inter_bbox

    def buffer_bbox(self, bbox, buf):
        """
        Buffer the input BBOX by a set amount.

        :param bbox: the bounding box (MinX, MaxX, MinY, MaxY)
        :param buf: the amount of buffer by
        :return: the buffered bbox (MinX, MaxX, MinY, MaxY)

        """
        out_bbox = [0, 0, 0, 0]
        out_bbox[0] = bbox[0] - buf
        out_bbox[1] = bbox[1] + buf
        out_bbox[2] = bbox[2] - buf
        out_bbox[3] = bbox[3] + buf
        return out_bbox

    def find_bbox_union(self, bboxes):
        """
        A function which finds the union of all the bboxes inputted.

        :param bboxes: a list of bboxes [(xMin, xMax, yMin, yMax), (xMin, xMax, yMin, yMax)]
        :return: bbox (xMin, xMax, yMin, yMax)

        """
        if len(bboxes) == 1:
            out_bbox = list(bboxes[0])
        elif len(bboxes) > 1:
            out_bbox = list(bboxes[0])
            for bbox in bboxes:
                if bbox[0] < out_bbox[0]:
                    out_bbox[0] = bbox[0]
                if bbox[1] > out_bbox[1]:
                    out_bbox[1] = bbox[1]
                if bbox[2] < out_bbox[2]:
                    out_bbox[2] = bbox[2]
                if bbox[3] > out_bbox[3]:
                    out_bbox[3] = bbox[3]
        else:
            out_bbox = None
        return out_bbox

    def unwrap_wgs84_bbox(self, bbox):
        """
        A function which unwraps a bbox if it projected in WGS84 and over the 180/-180 boundary.

        :param bbox: the bounding box (MinX, MaxX, MinY, MaxY)
        :return: list of bounding boxes [(MinX, MaxX, MinY, MaxY), (MinX, MaxX, MinY, MaxY)...]

        """
        bboxes = []
        if bbox[1] < bbox[0]:
            bbox1 = [-180.0, bbox[1], bbox[2], bbox[3]]
            bboxes.append(bbox1)
            bbox2 = [bbox[0], 180.0, bbox[2], bbox[3]]
            bboxes.append(bbox2)
        else:
            bboxes.append(bbox)
        return bboxes
        
    def getVecLayerExtent(self, inVec, layerName=None, computeIfExp=True):
        """
        Get the extent of the vector layer.
        
        :param inVec: is a string with the input vector file name and path.
        :param layerName: is the layer for which extent is to be calculated (Default: None)
                          if None assume there is only one layer and that will be read.
        :param computeIfExp: is a boolean which specifies whether the layer extent
                             should be calculated (rather than estimated from header)
                             even if that operation is computationally expensive.
        :return: boundary box is returned (MinX, MaxX, MinY, MaxY)
        
        """
        inDataSource = gdal.OpenEx(inVec, gdal.OF_VECTOR )
        if layerName is not None:
            inLayer = inDataSource.GetLayer(layerName)
        else:
            inLayer = inDataSource.GetLayer()
        extent = inLayer.GetExtent(computeIfExp)
        return extent
        
    def getVecFeatCount(self, inVec, layerName=None, computeCount=True):
        """
        Get a count of the number of features in the vector layers.
        
        :param inVec: is a string with the input vector file name and path.
        :param layerName: is the layer for which extent is to be calculated (Default: None)
                          if None assume there is only one layer and that will be read.
        :param computeCount: is a boolean which specifies whether the layer extent
                             should be calculated (rather than estimated from header)
                             even if that operation is computationally expensive.
        
        :return: nfeats
        
        """
        inDataSource = gdal.OpenEx(inVec, gdal.OF_VECTOR )
        if layerName is not None:
            inLayer = inDataSource.GetLayer(layerName)
        else:
            inLayer = inDataSource.GetLayer()
        nFeats = inLayer.GetFeatureCount(computeCount)
        return nFeats

    def findCommonExtentOnGrid(self, baseExtent, baseGrid, otherExtent, fullContain=True):
        """
        A function which calculates the common extent between two extents but defines output on 
        grid with defined resolutions. Useful for finding common extent on a particular image grid.
        
        :param baseExtent: is a bbox (xMin, xMax, yMin, yMax) providing the base for the grid on which output will be defined.
        :param baseGrid: the size of the (square) grid on which output will be defined.
        :param otherExtent: is a bbox (xMin, xMax, yMin, yMax) to be intersected with the baseExtent.
        :param fullContain: is a boolean. True: moving output onto grid will increase size of bbox (i.e., intersection fully contained)
                                          False: move output onto grid will decrease size of bbox (i.e., bbox fully contained within intesection)
        
        :return: bbox (xMin, xMax, yMin, yMax)

        """
        xMinOverlap = baseExtent[0]
        xMaxOverlap = baseExtent[1]
        yMinOverlap = baseExtent[2]
        yMaxOverlap = baseExtent[3]
        
        if otherExtent[0] > xMinOverlap:
            if fullContain:
                diff = math.floor((otherExtent[0] - xMinOverlap)/baseGrid)*baseGrid
            else:   
                diff = math.ceil((otherExtent[0] - xMinOverlap)/baseGrid)*baseGrid
            xMinOverlap = xMinOverlap + diff
        
        if otherExtent[1] < xMaxOverlap:
            if fullContain:
                diff = math.floor((xMaxOverlap - otherExtent[1])/baseGrid)*baseGrid
            else:
                diff = math.ceil((xMaxOverlap - otherExtent[1])/baseGrid)*baseGrid
            xMaxOverlap = xMaxOverlap - diff
        
        if otherExtent[2] > yMinOverlap:
            if fullContain:
                diff = math.floor(abs(otherExtent[2] - yMinOverlap)/baseGrid)*baseGrid
            else:
                diff = math.ceil(abs(otherExtent[2] - yMinOverlap)/baseGrid)*baseGrid
            yMinOverlap = yMinOverlap + diff
        
        if otherExtent[3] < yMaxOverlap:
            if fullContain:
                diff = math.floor(abs(yMaxOverlap - otherExtent[3])/baseGrid)*baseGrid
            else:
                diff = math.ceil(abs(yMaxOverlap - otherExtent[3])/baseGrid)*baseGrid
            yMaxOverlap = yMaxOverlap - diff
    
        return [xMinOverlap, xMaxOverlap, yMinOverlap, yMaxOverlap]
    
    def findExtentOnGrid(self, baseExtent, baseGrid, fullContain=True):
        """
        A function which calculates the extent but defined on a grid with defined resolution. 
        Useful for finding extent on a particular image grid.
        
        :param baseExtent: is a bbox (xMin, xMax, yMin, yMax) providing the base for the grid on which output will be defined.
        :param baseGrid: the size of the (square) grid on which output will be defined.
        :param fullContain: is a boolean. True: moving output onto grid will increase size of bbox (i.e., intersection fully contained)
                                          False: move output onto grid will decrease size of bbox (i.e., bbox fully contained within intesection)
        
        :return: bbox (xMin, xMax, yMin, yMax)

        """
        xMin = baseExtent[0]
        xMax = baseExtent[1]
        yMin = baseExtent[2]
        yMax = baseExtent[3]
        
        diffX = xMax - xMin
        diffY = abs(yMax - yMin)
        
        nPxlX = 0.0
        nPxlY = 0.0
        if fullContain:
            nPxlX = math.ceil(diffX/baseGrid)
            nPxlY = math.ceil(diffY/baseGrid)
        else:
            nPxlX = math.floor(diffX/baseGrid)
            nPxlY = math.floor(diffY/baseGrid)
        
        xMaxOut = xMin + (nPxlX * baseGrid)
        yMinOut = yMax - (nPxlY * baseGrid)
    
        return [xMin, xMaxOut, yMinOut, yMax]

    def findExtentOnWholeNumGrid(self, baseExtent, baseGrid, fullContain=True, round_vals=None):
        """
        A function which calculates the extent but defined on a grid with defined resolution.
        Useful for finding extent on a particular image grid.

        :param baseExtent: is a bbox (xMin, xMax, yMin, yMax) providing the base for the grid on which output will be defined.
        :param baseGrid: the size of the (square) grid on which output will be defined.
        :param fullContain: is a boolean. True: moving output onto grid will increase size of bbox (i.e., intersection fully contained)
                                          False: move output onto grid will decrease size of bbox (i.e., bbox fully contained within intesection)
        :param round_vals: specify whether outputted values should be rounded. None for no rounding (default) or integer for number of
                           significant figures to round to.

        :return: bbox (xMin, xMax, yMin, yMax)

        """
        xMin = baseExtent[0]
        xMax = baseExtent[1]
        yMin = baseExtent[2]
        yMax = baseExtent[3]

        nPxlXMin = math.floor(xMin / baseGrid)
        nPxlYMin = math.floor(yMin / baseGrid)

        xMinOut = nPxlXMin * baseGrid
        yMinOut = nPxlYMin * baseGrid

        diffX = xMax - xMinOut
        diffY = abs(yMax - yMinOut)

        nPxlX = 0.0
        nPxlY = 0.0
        if fullContain:
            nPxlX = math.ceil(diffX / baseGrid)
            nPxlY = math.ceil(diffY / baseGrid)
        else:
            nPxlX = math.floor(diffX / baseGrid)
            nPxlY = math.floor(diffY / baseGrid)

        xMaxOut = xMinOut + (nPxlX * baseGrid)
        yMaxOut = yMinOut + (nPxlY * baseGrid)

        if round_vals is None:
            out_bbox = [xMinOut, xMaxOut, yMinOut, yMaxOut]
        else:
            out_bbox = [round(xMinOut, round_vals), round(xMaxOut, round_vals), round(yMinOut, round_vals),
                        round(yMaxOut, round_vals)]
        return out_bbox

    def getBBoxGrid(self, bbox, x_size, y_size):
        """
        Create a grid with size x_size, y_size for the area represented by bbox.

        :param bbox: a bounding box within which the grid will be created (xMin, xMax, yMin, yMax)
        :param x_size: Output grid size in X axis (same unit as bbox).
        :param y_size: Output grid size in Y axis (same unit as bbox).

        :return: list of bounding boxes (xMin, xMax, yMin, yMax)

        """
        width = bbox[1] - bbox[0]
        height = bbox[3] - bbox[2]

        n_tiles_x = math.floor(width / x_size)
        n_tiles_y = math.floor(height / y_size)

        if (n_tiles_x > 10000) or (n_tiles_y > 10000):
            print("WARNING: did you mean to product so many tiles (X: {}, Y: {}) "
                  "might want to check your units".format(n_tiles_x, n_tiles_y))

        full_tile_width = n_tiles_x * x_size
        full_tile_height = n_tiles_y * y_size

        x_remain = width - full_tile_width
        if x_remain < 0.000001:
            x_remain = 0.0
        y_remain = height - full_tile_height
        if y_remain < 0.000001:
            y_remain = 0.0

        c_min_y = bbox[2]
        c_max_y = c_min_y + y_size

        bboxs = list()
        for ny in range(n_tiles_y):
            c_min_x = bbox[0]
            c_max_x = c_min_x + x_size
            for nx in range(n_tiles_x):
                bboxs.append([c_min_x, c_max_x, c_min_y, c_max_y])
                c_min_x = c_max_x
                c_max_x = c_max_x + x_size
            if x_remain > 0:
                c_max_x = c_min_x + x_remain
                bboxs.append([c_min_x, c_max_x, c_min_y, c_max_y])
            c_min_y = c_max_y
            c_max_y = c_max_y + y_size
        if y_remain > 0:
            c_max_y = c_min_y + y_remain
            c_min_x = bbox[0]
            c_max_x = c_min_x + x_size
            for nx in range(n_tiles_x):
                bboxs.append([c_min_x, c_max_x, c_min_y, c_max_y])
                c_min_x = c_max_x
                c_max_x = c_max_x + x_size
            if x_remain > 0:
                c_max_x = c_min_x + x_remain
                bboxs.append([c_min_x, c_max_x, c_min_y, c_max_y])

        return bboxs

    def reprojPoint(self, inProjOSRObj, outProjOSRObj, x, y):
        """
        Reproject a point from 'inProjOSRObj' to 'outProjOSRObj' where they are gdal
        osgeo.osr.SpatialReference objects. 
        
        :return: x, y.

        """
        if inProjOSRObj.EPSGTreatsAsLatLong():
            wktPt = 'POINT(%s %s)' % (y, x)
        else:
            wktPt = 'POINT(%s %s)' % (x, y)
        point = ogr.CreateGeometryFromWkt(wktPt)
        point.AssignSpatialReference(inProjOSRObj)
        point.TransformTo(outProjOSRObj)
        if outProjOSRObj.EPSGTreatsAsLatLong():
            outX = point.GetY()
            outY = point.GetX()
        else:
            outX = point.GetX()
            outY = point.GetY()
        return outX, outY

    def getImageBandStats(self, img, band, compute=True):
        """
        A function which calls the GDAL function on the band selected to calculate the pixel stats
        (min, max, mean, standard deviation). 
        
        :param img: input image file path
        :param band: specified image band for which stats are to be calculated (starts at 1).
        :param compute: whether the stats should be calculated (True; Default) or an approximation or pre-calculated stats are OK (False).
        
        :return: stats (min, max, mean, stddev)

        """
        img_ds = gdal.Open(img, gdal.GA_ReadOnly)
        if img_ds is None:
            raise Exception("Could not open image: '{}'".format(img))
        n_bands = img_ds.RasterCount
        
        if band > 0 and band <= n_bands:
            img_band = img_ds.GetRasterBand(band)
            if img_band is None:
                raise Exception("Could not open image band ('{0}') from : '{1}'".format(band, img))
            img_stats = img_band.ComputeStatistics((not compute))
        else:
            raise Exception("Band specified is not within the image: '{}'".format(img))
        return img_stats
    
    
    def getImageBandCount(self, inImg):
        """
        A function to retrieve the number of image bands in an image file.

        :return: nBands

        """
        rasterDS = gdal.Open(inImg, gdal.GA_ReadOnly)
        if rasterDS == None:
            raise RSGISPyException('Could not open raster image: \'' + inImg+ '\'')
        
        nBands = rasterDS.RasterCount
        rasterDS = None
        return nBands
        
    def getImageNoDataValue(self, inImg, band=1):
        """
        A function to retrieve the no data value for the image 
        (from band; default 1).

        :return: number

        """
        rasterDS = gdal.Open(inImg, gdal.GA_ReadOnly)
        if rasterDS == None:
            raise RSGISPyException('Could not open raster image: \'' + inImg+ '\'')
        
        noDataVal = rasterDS.GetRasterBand(band).GetNoDataValue()
        rasterDS = None
        return noDataVal

    def setImageNoDataValue(self, inImg, noDataValue, band=None):
        """
        A function to set the no data value for an image.
        If band is not specified sets value for all bands.

        """
        rasterDS = gdal.Open(inImg, gdal.GA_Update)
        if rasterDS is None:
            raise RSGISPyException('Could not open raster image: \'' + inImg + '\'')

        if band is not None:
            rasterDS.GetRasterBand(band).SetNoDataValue(noDataValue)
        else:
            for b in range(rasterDS.RasterCount):
                rasterDS.GetRasterBand(b+1).SetNoDataValue(noDataValue)

        rasterDS = None
    
    def getImgBandColourInterp(self, inImg, band):
        """
        A function to get the colour interpretation for a specific band.

        :return: is a GDALColorInterp value:
        
        * GCI_Undefined=0, 
        * GCI_GrayIndex=1, 
        * GCI_PaletteIndex=2, 
        * GCI_RedBand=3, 
        * GCI_GreenBand=4, 
        * GCI_BlueBand=5, 
        * GCI_AlphaBand=6, 
        * GCI_HueBand=7, 
        * GCI_SaturationBand=8, 
        * GCI_LightnessBand=9, 
        * GCI_CyanBand=10, 
        * GCI_MagentaBand=11, 
        * GCI_YellowBand=12, 
        * GCI_BlackBand=13, 
        * GCI_YCbCr_YBand=14, 
        * GCI_YCbCr_CbBand=15, 
        * GCI_YCbCr_CrBand=16, 
        * GCI_Max=16 
         
        """
        rasterDS = gdal.Open(inImg, gdal.GA_ReadOnly)
        if rasterDS is None:
            raise RSGISPyException('Could not open raster image: \'' + inImg + '\'')
        clrItrpVal = rasterDS.GetRasterBand(band).GetRasterColorInterpretation()
        rasterDS = None
        return clrItrpVal
        
    def setImgBandColourInterp(self, inImg, band, clrItrpVal):
        """
        A function to set the colour interpretation for a specific band.
        input is a GDALColorInterp value:
        
        * GCI_Undefined=0, 
        * GCI_GrayIndex=1, 
        * GCI_PaletteIndex=2, 
        * GCI_RedBand=3, 
        * GCI_GreenBand=4, 
        * GCI_BlueBand=5, 
        * GCI_AlphaBand=6, 
        * GCI_HueBand=7, 
        * GCI_SaturationBand=8, 
        * GCI_LightnessBand=9, 
        * GCI_CyanBand=10, 
        * GCI_MagentaBand=11, 
        * GCI_YellowBand=12, 
        * GCI_BlackBand=13, 
        * GCI_YCbCr_YBand=14, 
        * GCI_YCbCr_CbBand=15, 
        * GCI_YCbCr_CrBand=16, 
        * GCI_Max=16 
         
        """
        rasterDS = gdal.Open(inImg, gdal.GA_Update)
        if rasterDS is None:
            raise RSGISPyException('Could not open raster image: \'' + inImg + '\'')
        rasterDS.GetRasterBand(band).SetColorInterpretation(clrItrpVal)
        rasterDS = None
    
    def getWKTProjFromImage(self, inImg):
        """
        A function which returns the WKT string representing the projection 
        of the input image.

        :return: string

        """
        rasterDS = gdal.Open(inImg, gdal.GA_ReadOnly)
        if rasterDS == None:
            raise RSGISPyException('Could not open raster image: \'' + inImg+ '\'')
        projStr = rasterDS.GetProjection()
        rasterDS = None
        return projStr
    
    def getImageFiles(self, inImg):
        """
        A function which returns a list of the files associated (e.g., header etc.) 
        with the input image file.

        :return: lists

        """
        imgDS = gdal.Open(inImg)
        fileList = imgDS.GetFileList()
        imgDS = None
        return fileList
    
    def getUTMZone(self, inImg):
        """
        A function which returns a string with the UTM (XXN | XXS) zone of the input image 
        but only if it is projected within the UTM projection/coordinate system.

        :return: string

        """
        rasterDS = gdal.Open(inImg, gdal.GA_ReadOnly)
        if rasterDS == None:
            raise RSGISPyException('Could not open raster image: \'' + inImg+ '\'')
        projStr = rasterDS.GetProjection()
        rasterDS = None
    
        spatRef = osr.SpatialReference()
        spatRef.ImportFromWkt(projStr)
        utmZone = None
        if spatRef.IsProjected():
            projName = spatRef.GetAttrValue('projcs')
            zone = spatRef.GetUTMZone()
            if zone != 0:
                if zone < 0:
                    utmZone = str(zone*(-1))
                    if len(utmZone) == 1:
                        utmZone = '0' + utmZone
                    utmZone = utmZone+'S'
                else:
                    utmZone = str(zone)
                    if len(utmZone) == 1:
                        utmZone = '0' + utmZone
                    utmZone = utmZone+'N'
        return utmZone
    
    def getEPSGCode(self, gdalLayer):
        """
        Using GDAL to return the EPSG code for the input layer.

        :return: EPSG code

        """
        epsgCode = None
        try:
            layerDS = gdal.Open(gdalLayer, gdal.GA_ReadOnly)
            if layerDS == None:
                raise RSGISPyException('Could not open raster image: \'' + gdalLayer+ '\'')
            projStr = layerDS.GetProjection()
            layerDS = None
            
            spatRef = osr.SpatialReference()
            spatRef.ImportFromWkt(projStr)            
            spatRef.AutoIdentifyEPSG()
            epsgCode = spatRef.GetAuthorityCode(None)
            if epsgCode is not None:
                epsgCode = int(epsgCode)
        except Exception:
            epsgCode = None
        return epsgCode
        
    def doGDALLayersHaveSameProj(self, layer1, layer2):
        """
        A function which tests whether two gdal compatiable layers are in the same
        projection/coordinate system. This is done using the GDAL SpatialReference
        function AutoIdentifyEPSG. If the identified EPSG codes are different then 
        False is returned otherwise True.

        :return: boolean

        """
        layer1EPSG = self.getEPSGCode(layer1)
        layer2EPSG = self.getEPSGCode(layer2)
        
        sameEPSG = False
        if layer1EPSG == layer2EPSG:
            sameEPSG = True
        
        return sameEPSG
        
    def getProjWKTFromVec(self, inVec, vecLyr=None):
        """
        A function which gets the WKT projection from the inputted vector file.
        
        :param inVec: is a string with the input vector file name and path.
        :param vecLyr: is a string with the input vector layer name, if None then first layer read. (default: None)
        
        :return: WKT representation of projection

        """
        dataset = gdal.OpenEx(inVec, gdal.OF_VECTOR )
        if dataset is None:
            raise Exception("Could not open file: {}".format(inVec))
        if vecLyr is None:
            layer = dataset.GetLayer()
        else:
            layer = dataset.GetLayer(vecLyr)
        if layer is None:
            raise Exception("Could not open layer within file: {}".format(inVec))
        spatialRef = layer.GetSpatialRef()
        return spatialRef.ExportToWkt()

    def getProjEPSGFromVec(self, inVec, vecLyr=None):
        """
        A function which gets the EPSG projection from the inputted vector file.

        :param inVec: is a string with the input vector file name and path.
        :param vecLyr: is a string with the input vector layer name, if None then first layer read. (default: None)

        :return: EPSG representation of projection

        """
        dataset = gdal.OpenEx(inVec, gdal.OF_VECTOR)
        if dataset is None:
            raise Exception("Could not open file: {}".format(inVec))
        if vecLyr is None:
            layer = dataset.GetLayer()
        else:
            layer = dataset.GetLayer(vecLyr)
        if layer is None:
            raise Exception("Could not open layer within file: {}".format(inVec))
        spatialRef = layer.GetSpatialRef()
        spatialRef.AutoIdentifyEPSG()
        return spatialRef.GetAuthorityCode(None)
        
    def getEPSGCodeFromWKT(self, wktString):
        """
        Using GDAL to return the EPSG code for inputted WKT string.

        :return: the EPSG code.

        """
        epsgCode = None
        try:        
            spatRef = osr.SpatialReference()
            spatRef.ImportFromWkt(wktString)            
            spatRef.AutoIdentifyEPSG()
            epsgCode = spatRef.GetAuthorityCode(None)
        except Exception:
            epsgCode = None
        return epsgCode
        
    def getWKTFromEPSGCode(self, epsgCode):
        """
        Using GDAL to return the WKT string for inputted EPSG Code.
        
        :param epsgCode: integer variable of the epsg code.

        :return: string with WKT representation of the projection.

        """
        wktString = None
        try:        
            spatRef = osr.SpatialReference()
            spatRef.ImportFromEPSG(epsgCode)            
            wktString = spatRef.ExportToWkt()
        except Exception:
            wktString = None
        return wktString

    def get_osr_prj_obj(self, epsg_code):
        """
        A function which returns an OSR SpatialReference object
        for a given EPSG code.

        :param epsg_code: An EPSG code for the projection. Must be an integer.
        :return: osr.SpatialReference object.

        """
        spat_ref = osr.SpatialReference()
        spat_ref.ImportFromEPSG(int(epsg_code))
        return spat_ref
    
    def uidGenerator(self, size=6):
        """
        A function which will generate a 'random' string of the specified length based on the UUID

        :param size: the length of the returned string.
        :return: string of length size.

        """
        import uuid
        randomStr = str(uuid.uuid4())
        randomStr = randomStr.replace("-","")
        return randomStr[0:size]
    
    def isNumber(self, strVal):
        """
        A function which tests whether the input string contains a number of not.

        :return: boolean

        """
        try:
            float(strVal) # for int, long and float
        except ValueError:
            try:
                complex(strVal) # for complex
            except ValueError:
                return False
        return True

    def zero_pad_num_str(self, num_val, str_len=3, round_num=False, round_n_digts=0, integerise=False):
        """
        A function which zero pads a number to make a string

        :param num_val: number value to be processed.
        :param str_len: the number of characters in the output string.
        :param round_num: boolean whether to round the input number value.
        :param round_n_digts: If rounding, the number of digits following decimal points to round to.
        :param integerise: boolean whether to integerise the input number
        :return: string with the padded numeric value.

        """
        if round_num:
            num_val = round(num_val, round_n_digts)
        if integerise:
            num_val = int(num_val)

        num_str = "{}".format(num_val)
        num_str = num_str.zfill(str_len)
        return num_str

    def powerset_iter(self, inset):
        """
        A function which returns an iterator (generator) for all the subsets
        of the inputted set (i.e., the powerset)

        :params inset: the input set for which the powerset will be produced

        """
        if len(inset) <= 1:
            yield inset
            yield []
        else:
            for item in self.powerset_iter(inset[1:]):
                yield [inset[0]] + item
                yield item

    def powerset_lst(self, inset, min_items=0):
        """
        A function which returns a list for all the subsets
        of the inputted set (i.e., the powerset)

        :params inset: the input set for which the powerset will be produced
        :params min_items: Optional parameter specifying the minimum number
                           of items in the output sets. If 0 or below then
                           ignored. Default is 0.

        """
        out_pset = []
        for subset in self.powerset_iter(inset):
            if min_items > 0:
                if len(subset) >= min_items:
                    out_pset.append(subset)
            else:
                out_pset.append(subset)
        return out_pset

    def getEnvironmentVariable(self, var):
        """
        A function to get an environmental variable, if variable is not present returns None.

        :return: value of env var.

        """
        outVar = None
        try:
            outVar = os.environ[var]
        except Exception:
            outVar = None
        return outVar
    
    def numProcessCores(self):
        """
        A functions which returns the number of processing cores available on the machine

        :return: int

        """
        import multiprocessing
        return multiprocessing.cpu_count()
        
    def readTextFileNoNewLines(self, file):
        """
        Read a text file into a single string
        removing new lines.

        :param file: File path to the input file.
        :return: string

        """
        txtStr = ""
        try:
            dataFile = open(file, 'r')
            for line in dataFile:
                txtStr += line.strip()
            dataFile.close()
        except Exception as e:
            raise e
        return txtStr

    def readTextFile2List(self, file):
        """
        Read a text file into a list where each line 
        is an element in the list.

        :param file: File path to the input file.
        :return: list

        """
        outList = []
        try:
            dataFile = open(file, 'r')
            for line in dataFile:
                line = line.strip()
                if line != "":
                    outList.append(line)
            dataFile.close()
        except Exception as e:
            raise e
        return outList

    def writeList2File(self, dataList, outFile):
        """
        Write a list a text file, one line per item.

        :param dataList: List of values to be written to the output file.
        :param out_file: File path to the output file.

        """
        try:
            f = open(outFile, 'w')
            for item in dataList:
               f.write(str(item)+'\n')
            f.flush()
            f.close()
        except Exception as e:
            raise e

    def writeData2File(self, data_val, out_file):
        """
        Write some data (a string or can be converted to a string using str(data_val) to
        an output text file.

        :param data_val: Data to be written to the output file.
        :param out_file: File path to the output file.

        """
        try:
            f = open(out_file, 'w')
            f.write(str(data_val)+'\n')
            f.flush()
            f.close()
        except Exception as e:
            raise e

    def writeDict2JSON(self, data_dict, out_file):
        """
        Write some data to a JSON file. The data would commonly be structured as a dict but could also be a list.

        :param data_dict: The dict (or list) to be written to the output JSON file.
        :param out_file: The file path to the output file.

        """
        import json
        with open(out_file, 'w') as fp:
            json.dump(data_dict, fp, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

    def readJSON2Dict(self, input_file):
        """
        Read a JSON file. Will return a list or dict.

        :param input_file: input JSON file path.

        """
        import json
        with open(input_file) as f:
            data = json.load(f)
        return data

    def findFile(self, dirPath, fileSearch):
        """
        Search for a single file with a path using glob. Therefore, the file 
        path returned is a true path. Within the fileSearch provide the file
        name with '*' as wildcard(s).

        :return: string

        """
        import glob
        files = glob.glob(os.path.join(dirPath, fileSearch))
        if len(files) != 1:
            raise RSGISPyException('Could not find a single file ('+fileSearch+'); found ' + str(len(files)) + ' files.')
        return files[0]

    def findFileNone(self, dirPath, fileSearch):
        """
        Search for a single file with a path using glob. Therefore, the file
        path returned is a true path. Within the fileSearch provide the file
        name with '*' as wildcard(s). Returns None is not found.

        :return: string

        """
        import glob
        import os.path
        files = glob.glob(os.path.join(dirPath, fileSearch))
        if len(files) != 1:
            return None
        return files[0]

    def find_files_ext(self, dir_path, ending):
        """
        Find all the files within a directory structure with a specific file ending.
        The files are return as dictionary using the file name as the dictionary key.
        This means you cannot have files with the same name within the structure.

        :param dir_path: the base directory path within which to search.
        :param ending: the file ending (e.g., .txt, or txt or .kea, kea).
        :return: dict with file name as key

        """
        out_file_dict = dict()
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith(ending):
                    file_found = os.path.join(root, file)
                    if os.path.isfile(file_found):
                        out_file_dict[file] = file_found
        return out_file_dict

    def find_files_mpaths_ext(self, dir_paths, ending):
        """
        Find all the files within a list of input directories and the structure beneath
        with a specific file ending. The files are return as dictionary using the file
        name as the dictionary key. This means you cannot have files with the same name
        within the structure.

        :param dir_path: the base directory path within which to search.
        :param ending: the file ending (e.g., .txt, or txt or .kea, kea).
        :return: dict with file name as key

        """
        out_file_dict = dict()
        for dir_path in dir_paths:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    if file.endswith(ending):
                        file_found = os.path.join(root, file)
                        if os.path.isfile(file_found):
                            out_file_dict[file] = file_found
        return out_file_dict

    def find_first_file(self, dirPath, fileSearch, rtn_except=True):
        """
        Search for a single file with a path using glob. Therefore, the file
        path returned is a true path. Within the fileSearch provide the file
        name with '*' as wildcard(s).
        :param dirPath: The directory within which to search, note that the search will be within
                        sub-directories within the base directory until a file meeting the search
                        criteria are met.
        :param fileSearch: The file search string in the file name and must contain a wild character (i.e., *).
        :param rtn_except: if True then an exception will be raised if no file or multiple files are found (default).
                           If False then None will be returned rather than an exception raised.
        :return: The file found (or None if rtn_except=False)

        """
        import glob
        files = None
        for root, dirs, files in os.walk(dirPath):
            files = glob.glob(os.path.join(root, fileSearch))
            if len(files) > 0:
                break
        out_file = None
        if (files is not None) and (len(files) == 1):
            out_file = files[0]
        elif rtn_except:
            raise Exception("Could not find a single file ({0}) in {1}; "
                            "found {2} files.".format(fileSearch, dirPath, len(files)))
        return out_file

    def get_files_mtime(self, file_lst, dt_before=None, dt_after=None):
        """
        A function which subsets a list of files based on datetime of
        last modification. The function also does a check as to whether
        a file exists, files which don't exist will be ignored.

        :param file_lst: The list of file path - represented as strings.
        :param dt_before: a datetime object with a date/time where files modified before this will be returned
        :param dt_after: a datetime object with a date/time where files modified after this will be returned

        """
        if (dt_before is None) and (dt_after is None):
            raise Exception("You must define at least one of dt_before or dt_after")
        out_file_lst = list()
        for cfile in file_lst:
            if os.path.exists(cfile):
                mod_time_stamp = os.path.getmtime(cfile)
                mod_time = datetime.datetime.fromtimestamp(mod_time_stamp)
                if (dt_before is not None) and (mod_time < dt_before):
                    out_file_lst.append(cfile)
                if (dt_after is not None) and (mod_time > dt_after):
                    out_file_lst.append(cfile)
        return out_file_lst

    def file_is_hidden(self, in_path):
        """
        A function to test whether a file or folder is 'hidden' or not on the
        file system. Should be cross platform between Linux/UNIX and windows.

        :param in_path: input file path to be tested
        :return: boolean (True = hidden)

        """
        in_path = os.path.abspath(in_path)
        if os.name == 'nt':
            import win32api, win32con
            attribute = win32api.GetFileAttributes(in_path)
            return attribute & (win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
        else:
            file_name = os.path.basename(in_path)
            return file_name.startswith('.')

    def get_dir_list(self, input_path, inc_hidden=False):
        """
        Function which get the list of directories within the specified path.

        :param input_path: file path to search within
        :param inc_hidden: boolean specifying whether hidden files should be included (default=False)
        :return: list of directory paths

        """
        out_dir_lst = list()
        dir_listing = os.listdir(input_path)
        for item in dir_listing:
            c_path = os.path.join(input_path, item)
            if os.path.isdir(c_path):
                if not inc_hidden:
                    if not self.file_is_hidden(c_path):
                        out_dir_lst.append(c_path)
                else:
                    out_dir_lst.append(c_path)
        return out_dir_lst

    def createVarList(self, in_vals_lsts, val_dict=None):
        """
        A function which will produce a list of dictionaries with all the combinations 
        of the input variables listed (i.e., the powerset). 
        
        :param in_vals_lsts: dictionary with each value having a list of values.
        :param val_dict: variable used in iterative nature of function which lists
                         the variable for which are still to be looped through. Would
                         normally not be provided by the user as default is None. Be
                         careful if you set as otherwise.

        :returns: list of dictionaries with the same keys are the input but only a
                  single value will be associate with key rather than a list.
                   
        Example::

            seg_vars_ranges = dict()
            seg_vars_ranges['k'] = [5, 10, 20, 30, 40, 50, 60, 80, 100, 120]
            seg_vars_ranges['d'] = [10, 20, 50, 100, 200, 1000, 10000]
            seg_vars_ranges['minsize'] = [5, 10, 20, 50, 100, 200]
            seg_vars = rsgis_utils.createVarList(seg_vars_ranges)
        
        """
        out_vars = []
        if (in_vals_lsts is None) and (val_dict is not None):
            out_val_dict = dict()
            for key in val_dict.keys():
                out_val_dict[key] = val_dict[key]
            out_vars.append(out_val_dict)
        elif in_vals_lsts is not None:
            if len(in_vals_lsts.keys()) > 0:
                key = list(in_vals_lsts.keys())[0]
                vals_arr = in_vals_lsts[key]
                next_vals_lsts = dict()
                for ckey in in_vals_lsts.keys():
                    if ckey != key:
                        next_vals_lsts[ckey] = in_vals_lsts[ckey]
                        
                if len(next_vals_lsts.keys()) == 0:
                    next_vals_lsts = None
                
                if val_dict is None:
                    val_dict = dict()
                
                for val in vals_arr:
                    c_val_dict = dict()
                    for ckey in val_dict.keys():
                        c_val_dict[ckey] = val_dict[ckey]
                    c_val_dict[key] = val
                    c_out_vars = self.createVarList(next_vals_lsts, c_val_dict)
                    out_vars = out_vars+c_out_vars
        return out_vars

    def in_bounds(self, x, lower, upper, upper_strict=False):
        """
        Checks whether a value is within specified bounds.

        :param x: value or array of values to check.
        :param lower: lower bound
        :param upper: upper bound
        :param upper_strict: True is less than upper; False is less than equal to upper

        :return: boolean

        """
        import numpy
        if upper_strict:
            return lower <= numpy.min(x) and numpy.max(x) < upper
        else:
            return lower <= numpy.min(x) and numpy.max(x) <= upper

    def mixed_signs(self, x):
        """
        Check whether a list of numbers has a mix of postive and negative values.

        :param x: list of values.

        :return: boolean

        """
        import numpy
        return numpy.min(x) < 0 and numpy.max(x) >= 0

    def negative(self, x):
        """
        Is the maximum number in the list negative.
        :param x: list of values

        :return: boolean

        """
        import numpy
        return numpy.max(x) < 0

    def isodd(self, number):
        """
        A function which tests whether a number is odd

        :param number: number value to test.
        :return: True = input number is odd; False = input number is even

        """
        if (number % 2) != 0:
            return True
        return False

    def remove_repeated_chars(self, str_val, repeat_char):
        """
        A function which removes repeated characters within a string for the specified character

        :param str_val: The input string.
        :param repeat_char: The character
        :return: string without repeat_char

        """
        if len(repeat_char) != 1:
            raise Exception("The repeat character has multiple characters.")
        out_str = ''
        p = ''
        for c in str_val:
            if c == repeat_char:
                if c != p:
                    out_str += c
            else:
                out_str += c
            p = c
        return out_str

    def check_str(self, str_val, rm_non_ascii=False, rm_dashs=False, rm_spaces=False, rm_punc=False):
        """
        A function which can check a string removing spaces (replaced with underscores),
        remove punctuation and any non ascii characters.

        :param str_val: the input string to be processed.
        :param rm_non_ascii: If True (default False) remove any non-ascii characters from the string
        :param rm_dashs: If True (default False) remove any dashs from the string and replace with underscores.
        :param rm_spaces: If True (default False) remove any spaces from the string.
        :param rm_punc: If True (default False) remove any punctuation (other than '_' or '-') from the string.
        :return: returns a string outputted from the processing.

        """
        import string
        str_val_tmp = str_val.strip()

        if rm_non_ascii:
            str_val_tmp_ascii = ""
            for c in str_val_tmp:
                if (c in string.ascii_letters) or (c in string.punctuation) or (c in string.digits) or (c == ' '):
                    str_val_tmp_ascii += c
            str_val_tmp = str_val_tmp_ascii

        if rm_dashs:
            str_val_tmp = str_val_tmp.replace('-', '_')
            str_val_tmp = self.remove_repeated_chars(str_val_tmp, '_')

        if rm_spaces:
            str_val_tmp = str_val_tmp.replace(' ', '_')
            str_val_tmp = self.remove_repeated_chars(str_val_tmp, '_')

        if rm_punc:
            for punct in string.punctuation:
                if (punct != '_') and (punct != '-'):
                    str_val_tmp = str_val_tmp.replace(punct, '')
            str_val_tmp = self.remove_repeated_chars(str_val_tmp, '_')

        return str_val_tmp

    def get_file_lock(self, input_file, sleep_period=1, wait_iters=120, use_except=False):
        """
        A function which gets a lock on a file.

        The lock file will be a unix hidden file (i.e., starts with a .) and it will have .lok added to the end.
        E.g., for input file hello_world.txt the lock file will be .hello_world.txt.lok. The contents of the lock
        file will be the time and date of creation.

        Using the default parameters (sleep 1 second and wait 120 iterations) if the lock isn't available
        it will be retried every second for 120 seconds (i.e., 2 mins).

        :param input_file: The input file for which the lock will be created.
        :param sleep_period: time in seconds to sleep for, if the lock isn't available. (Default=1 second)
        :param wait_iters: the number of iterations to wait for before giving up. (Default=120)
        :param use_except: Boolean. If True then an exception will be thrown if the lock is not
                           available. If False (default) False will be returned if the lock is
                           not successful.
        :return: boolean. True: lock was successfully gained. False: lock was not gained.

        """
        file_path, file_name = os.path.split(input_file)
        lock_file_name = ".{}.lok".format(file_name)
        lock_file_path = os.path.join(file_path, lock_file_name)

        got_lock = False
        for i in range(wait_iters+1):
            if not os.path.exists(lock_file_path):
                got_lock = True
                break
            time.sleep(sleep_period)

        if got_lock:
            c_datetime = datetime.datetime.now()
            f = open(lock_file_path, 'w')
            f.write('{}\n'.format(c_datetime.isoformat()))
            f.flush()
            f.close()
        elif use_except:
            raise Exception("Lock could not be gained for file: {}".format(input_file))

        return got_lock

    def release_file_lock(self, input_file):
        """
        A function which releases a lock file for the input file.

        :param input_file: The input file for which the lock will be created.

        """
        file_path, file_name = os.path.split(input_file)
        lock_file_name = ".{}.lok".format(file_name)
        lock_file_path = os.path.join(file_path, lock_file_name)
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)

    def clean_file_locks(self, dir_path, timeout=3600):
        """
        A function which cleans up any remaining lock file (i.e., if an application has crashed).
        The timeout time will be compared with the time written within the file.

        :param dir_path: the file path to search for lock files (i.e., ".*.lok")
        :param timeout: the time (in seconds) for the timeout. Default: 3600 (1 hours)

        """
        import glob
        c_dateime = datetime.datetime.now()
        lock_files = glob.glob(os.path.join(dir_path, ".*.lok"))
        for lock_file_path in lock_files:
            create_date_str = self.readTextFileNoNewLines(lock_file_path)
            create_date = datetime.datetime.fromisoformat(create_date_str)
            time_since_create = (c_dateime - create_date).total_seconds()
            if time_since_create > timeout:
                os.remove(lock_file_path)

    def get_days_since(self, year, dayofyear, base_date):
        """
        Calculate the number of days from a base data to a defined year/day.

        :param year: int with year XXXX (e.g., 2020)
        :param dayofyear: int with the day within the year (1-365)
        :param base_date: a datetime
        :return: int (n days)

        """
        if year < base_date.year:
            raise Exception("The year specified is before the base date.")
        date_val = datetime.date(year=int(year), month=1, day=1)
        date_val = date_val + datetime.timedelta(days=int(dayofyear - 1))
        return (date_val - base_date).days

    def get_days_since_date(self, year, month, day, base_date):
        """
        Calculate the number of days from a base data to a defined year/day.

        :param year: int with year XXXX (e.g., 2020)
        :param month: int month in year (1-12) (e.g., 6)
        :param day: int with the day within the month (1-31) (e.g., 20)
        :param base_date: a datetime
        :return: int (n days)

        """
        if year < base_date.year:
            raise Exception("The year specified is before the base date.")
        date_val = datetime.date(year=int(year), month=int(month), day=int(day))
        return (date_val - base_date).days

    def check_gdal_image_file(self, gdal_img, check_bands=True, nbands=0, chk_proj=False, epsg_code=0, read_img=False,
                              n_smp_pxls=10):
        """
        A function which checks a GDAL compatible image file and returns an error message if appropriate.

        :param gdal_img: the file path to the gdal image file.
        :param check_bands: boolean specifying whether individual image bands should be
                            opened and checked (Default: True)
        :param nbands: int specifying the number of expected image bands. Ignored if 0; Default is 0.
        :param chk_proj: boolean specifying whether to check that the projection has been defined.
        :param epsg_code: int for the EPSG code for the projection. Error raised if image is not that projection.
        :param read_img: boolean specifying whether to try reading some image pixel values from the image.
                         This option will read 10 random image pixel values from a randomly selected band.
        :param n_smp_pxls: The number of sample pixels to be read from the image if the read_img option is True.
                           Default is 10.
        :return: boolean (True: file ok; False: Error found), string (error message if required otherwise empty string)

        """
        file_ok = True
        err_str = ''
        if os.path.exists(gdal_img):
            err = RSGISGDALErrorHandler()
            err_handler = err.handler
            gdal.PushErrorHandler(err_handler)
            gdal.UseExceptions()
            try:
                if os.path.splitext(gdal_img)[1].lower() == '.kea':
                    file_ok = self.check_hdf5_file(gdal_img)
                    if not file_ok:
                        err_str = "Error with KEA/HDF5 file."
                if file_ok:
                    raster_ds = gdal.Open(gdal_img, gdal.GA_ReadOnly)
                    if raster_ds is None:
                        file_ok = False
                        err_str = 'GDAL could not open the dataset, returned None.'

                    if file_ok and (nbands > 0):
                        n_img_bands = raster_ds.RasterCount
                        if n_img_bands != nbands:
                            file_ok = False
                            err_str = 'Image should have {} image bands but {} found.'.format(nbands, n_img_bands)

                    if file_ok and check_bands:
                        n_img_bands = raster_ds.RasterCount
                        if n_img_bands < 1:
                            file_ok = False
                            err_str = 'Image says it does not have any image bands.'
                        else:
                            for n in range(n_img_bands):
                                band = n + 1
                                img_band = raster_ds.GetRasterBand(band)
                                if img_band is None:
                                    file_ok = False
                                    err_str = 'GDAL could not open band {} in the dataset, returned None.'.format(band)
                                    break

                    if file_ok and chk_proj:
                        proj_obj = raster_ds.GetProjection()
                        if proj_obj is None:
                            file_ok = False
                            err_str = 'Image projection is None.'
                        elif proj_obj is '':
                            file_ok = False
                            err_str = 'Image projection is empty.'

                        if file_ok and (epsg_code > 0):
                            spat_ref = osr.SpatialReference()
                            spat_ref.ImportFromWkt(proj_obj)
                            spat_ref.AutoIdentifyEPSG()
                            img_epsg_code = spat_ref.GetAuthorityCode(None)
                            if img_epsg_code is None:
                                file_ok = False
                                err_str = 'Image projection returned a None EPSG code.'
                            elif int(img_epsg_code) != int(epsg_code):
                                file_ok = False
                                err_str = 'Image EPSG ({}) does not match that specified ({})'.format(img_epsg_code,
                                                                                                      epsg_code)

                    if file_ok and read_img:
                        import numpy
                        n_img_bands = raster_ds.RasterCount
                        xSize = raster_ds.RasterXSize
                        ySize = raster_ds.RasterYSize

                        if n_img_bands == 1:
                            band = 1
                        else:
                            band = int(numpy.random.randint(1, high=n_img_bands, size=1))

                        img_band = raster_ds.GetRasterBand(band)
                        x_pxls = numpy.random.choice(xSize, n_smp_pxls)
                        y_pxls = numpy.random.choice(ySize, n_smp_pxls)
                        for i in range(n_smp_pxls):
                            img_data = img_band.ReadRaster(xoff=int(x_pxls[i]), yoff=int(y_pxls[i]), xsize=1, ysize=1,
                                                           buf_xsize=1, buf_ysize=1, buf_type=gdal.GDT_Float32)

                    raster_ds = None
            except Exception as e:
                file_ok = False
                err_str = str(e)
            else:
                if err.err_level >= gdal.CE_Warning:
                    file_ok = False
                    err_str = str(err.err_msg)
            finally:
                gdal.PopErrorHandler()
        else:
            file_ok = False
            err_str = 'File does not exist.'
        return file_ok, err_str

    def check_gdal_vector_file(self, gdal_vec):
        """
        A function which checks a GDAL compatible vector file and returns an error message if appropriate.

        :param gdal_vec: the file path to the gdal vector file.
        :return: boolean (True: file OK; False: Error found), string (error message if required otherwise empty string)

        """
        file_ok = True
        err_str = ''
        if os.path.exists(gdal_vec):
            err = RSGISGDALErrorHandler()
            err_handler = err.handler
            gdal.PushErrorHandler(err_handler)
            gdal.UseExceptions()

            try:
                vec_ds = gdal.OpenEx(gdal_vec, gdal.OF_VECTOR)
                if vec_ds is None:
                    file_ok = False
                    err_str = 'GDAL could not open the data source, returned None.'
                else:
                    for lyr_idx in range(vec_ds.GetLayerCount()):
                        vec_lyr = vec_ds.GetLayerByIndex(lyr_idx)
                        if vec_lyr is None:
                            file_ok = False
                            err_str = 'GDAL could not open all the vector layers.'
                            break
                vec_ds = None
            except Exception as e:
                file_ok = False
                err_str = str(e)
            else:
                if err.err_level >= gdal.CE_Warning:
                    file_ok = False
                    err_str = str(err.err_msg)
            finally:
                gdal.PopErrorHandler()
        else:
            file_ok = False
            err_str = 'File does not exist.'
        return file_ok, err_str

    def check_hdf5_file(self, input_file):
        """
        A function which checks whether a HDF5 file is valid.
        :param input_file: the file path to the input file.
        :return: a boolean - True file is valid. False file is not valid.

        """
        import h5py

        def _check_h5_var(h5_obj):
            lcl_ok = True
            try:
                if isinstance(h5_obj, h5py.Dataset):
                    lcl_ok = True
                elif isinstance(h5_obj, h5py.Group):
                    for var in h5_obj.keys():
                        lcl_ok = _check_h5_var(h5_obj[var])
                        if not lcl_ok:
                            break
            except RuntimeError:
                lcl_ok = False
            return lcl_ok

        glb_ok = True
        if not os.path.exists(input_file):
            glb_ok = False
        else:
            fH5 = h5py.File(input_file, 'r')
            if fH5 is None:
                glb_ok = False
            else:
                for var in fH5.keys():
                    glb_ok = _check_h5_var(fH5[var])
                    if not glb_ok:
                        break
        return glb_ok


class RSGISTime (object):
    """ Class to calculate run time for a function, format and print out (similar to for XML interface).

        Need to call start before running function and end immediately after.
        Example::

            t = RSGISTime()
            t.start()
            rsgislib.segmentation.clump(kMeansFileZonesNoSgls, initClumpsFile, gdalformat, False, 0) 
            t.end()
        
        Note, this is only designed to provide some general feedback, for benchmarking the timeit module
        is better suited.

    """

    def __init__(self):
        self.startTime = time.time()
        self.endTime = time.time()

    def start(self, printStartTime=False):
        """
        Start timer, optionally printing start time

        :param printStartTime: A boolean specifiying whether the start time should be printed to console.

        """
        self.startTime = time.time()
        if printStartTime:
            print(time.strftime('Start Time: %H:%M:%S, %a %b %m %Y.'))

    def end(self, reportDiff=True, preceedStr="", postStr=""):
        """ 
        End timer and optionally print difference.
        If preceedStr or postStr have a value then they will be used instead
        of the generic wording around the time. 
        
        preceedStr + time + postStr

        :param reportDiff: A boolean specifiying whether time difference should be printed to console.
        :param preceedStr: A string which is printed ahead of time difference
        :param postStr: A string which is printed after the time difference

        """
        self.endTime = time.time()
        if reportDiff:
            self.calcDiff(preceedStr, postStr)

    def calcDiff(self, preceedStr="", postStr=""):
        """
        Calculate time difference, format and print.
        :param preceedStr: A string which is printed ahead of time difference
        :param postStr: A string which is printed after the time difference

        """
        timeDiff = self.endTime - self.startTime
        
        useCustomMss = False
        if (len(preceedStr) > 0) or (len(postStr) > 0):
            useCustomMss = True
        
        if timeDiff <= 1:
            if useCustomMss:
                outStr = preceedStr + str("in less than a second") + postStr
                print(outStr)
            else:
                print("Algorithm Completed in less than a second.")
        else:
            timeObj = datetime.datetime.utcfromtimestamp(timeDiff)
            timeDiffStr = timeObj.strftime('%H:%M:%S')
            if useCustomMss:
                print(preceedStr + timeDiffStr + postStr)
            else:
                print('Algorithm Completed in %s.'%(timeDiffStr))
        
class TQDMProgressBar(object):
    """
    Uses TQDM TermProgress to print a progress bar to the terminal
    """
    def __init__(self):
        self.lprogress = 0

    def setTotalSteps(self,steps):
        import tqdm
        self.pbar = tqdm.tqdm(total=steps)
        self.lprogress = 0

    def setProgress(self, progress):
        step = progress - self.lprogress
        self.pbar.update(step)
        self.lprogress = progress

    def reset(self):
        self.pbar.close()
        import tqdm
        self.pbar = tqdm.tqdm(total=100)
        self.lprogress = 0

    def setLabelText(self,text):
        sys.stdout.write('\n%s\n' % text)

    def wasCancelled(self):
        return False

    def displayException(self,trace):
        sys.stdout.write(trace)

    def displayWarning(self,text):
        sys.stdout.write("Warning: %s\n" % text)

    def displayError(self,text):
        sys.stdout.write("Error: %s\n" % text)

    def displayInfo(self,text):
        sys.stdout.write("Info: %s\n" % text)
