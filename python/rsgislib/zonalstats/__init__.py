#!/usr/bin/env python
"""
The zonal stats module provides functions to perform pixel-in-polygon or point-in-pixel analysis. 

For undertaking a pixel-in-polygon analysis you need to consider the size of the polygons with
respect to the size of the pixels being intersected. 

Where the pixels are small with respect to the polygons so there is at least one pixel within the polygon
then the best function to use is:

* rsgislib.zonalstats.calcZonalBandStats

If the pixels are large with respect to the polygons then use the following function which intersects
the polygon centroid.

* rsgislib.zonalstats.calcZonalPolyPtsBandStats

If the pixel size in between and/or polygons are varied in size such that it is not certain that all 
polygons will contain a pixel then the following function will first attempt to intersect the polygon 
with the pixels and if there is not a pixel within the polygon then the centriod is used.

* rsgislib.zonalstats.calcZonalBandStatsTestPolyPts

Alternatively, the other functions are slower to execute but have more options with respect to the
method of intersection. The options for intersection are:

* METHOD_POLYCONTAINSPIXEL = 0           # Polygon completely contains pixel
* METHOD_POLYCONTAINSPIXELCENTER = 1     # Pixel center is within the polygon
* METHOD_POLYOVERLAPSPIXEL = 2           # Polygon overlaps the pixel
* METHOD_POLYOVERLAPSORCONTAINSPIXEL = 3 # Polygon overlaps or contains the pixel
* METHOD_PIXELCONTAINSPOLY = 4           # Pixel contains the polygon
* METHOD_PIXELCONTAINSPOLYCENTER = 5     # Polygon center is within pixel
* METHOD_ADAPTIVE = 6                    # The method is chosen based on relative areas of pixel and polygon.
* METHOD_ENVELOPE = 7                    # All pixels in polygon envelope chosen
* METHOD_PIXELAREAINPOLY = 8             # Percent of pixel area that is within the polygon
* METHOD_POLYAREAINPIXEL = 9             # Percent of polygon area that is within pixel

"""
from __future__ import print_function

# import the C++ extension into this level
from ._zonalstats import *

import osgeo.gdal as gdal
import osgeo.ogr as ogr
import osgeo.osr as osr
import numpy
import math
import sys
import tqdm

METHOD_POLYCONTAINSPIXEL = 0           # Polygon completely contains pixel
METHOD_POLYCONTAINSPIXELCENTER = 1     # Pixel center is within the polygon
METHOD_POLYOVERLAPSPIXEL = 2           # Polygon overlaps the pixel
METHOD_POLYOVERLAPSORCONTAINSPIXEL = 3 # Polygon overlaps or contains the pixel
METHOD_PIXELCONTAINSPOLY = 4           # Pixel contains the polygon
METHOD_PIXELCONTAINSPOLYCENTER = 5     # Polygon center is within pixel
METHOD_ADAPTIVE = 6                    # The method is chosen based on relative areas of pixel and polygon.
METHOD_ENVELOPE = 7                    # All pixels in polygon envelope chosen
METHOD_PIXELAREAINPOLY = 8             # Percent of pixel area that is within the polygon
METHOD_POLYAREAINPIXEL = 9             # Percent of polygon area that is within pixel

class ZonalAttributes:
    """ Object, specifying which stats should be calculated and minimum / maximum thresholds. 
This is passed to the pixelStats2SHP and pixelStats2TXT functions. """
    def __init__(self, minThreshold=None, maxThreshold=None, calcCount=False,
                 calcMin=False, calcMax=False, calcMean=False, calcStdDev=False,
                 calcMode=False, calcSum=False):
        self.minThreshold = minThreshold
        self.maxThreshold = maxThreshold
        self.calcCount = calcCount
        self.calcMin = calcMin
        self.calcMax = calcMax
        self.calcMean = calcMean
        self.calcStdDev = calcStdDev 
        self.calcMode = calcMode
        self.calcSum = calcSum
        

class ZonalBandAttributes:
    """ Object, specifying which band, the band name and stats should be calculated and minimum / maximum thresholds. 
This is passed to the polyPixelStatsVecLyr function. """
    def __init__(self, band=0, basename="band", minThres=None, maxThres=None,
                 calcCount=False, calcMin=False, calcMax=False, calcMean=False,
                 calcStdDev=False, calcMode=False, calcMedian=False, calcSum=False):
        self.band = band
        self.basename = basename
        self.minThres = minThres
        self.maxThres = maxThres
        self.calcCount = calcCount
        self.calcMin = calcMin
        self.calcMax = calcMax
        self.calcMean = calcMean
        self.calcStdDev = calcStdDev 
        self.calcMode = calcMode
        self.calcMedian = calcMedian
        self.calcSum = calcSum

def calcZonalBandStatsFile(vecfile, veclyrname, valsimg, imgbandidx, minthres, maxthres, out_no_data_val,
                           minfield=None, maxfield=None, meanfield=None, stddevfield=None, sumfield=None,
                           countfield=None, modefield=None, medianfield=None, vec_def_epsg=None):
    """
A function which calculates zonal statistics for a particular image band. 
If you know that the pixels in the values image are small with respect to 
the polygons then use this function.

:param vecfile: input vector file
:param veclyrname: input vector layer within the input file which specifies the features and where the
                   output stats will be written.
:param valsimg: the values image
:param imgbandidx: the index (starting at 1) of the image band for which the stats will be calculated.
                   If defined the no data value of the band will be ignored.
:param minthres: a lower threshold for values which will be included in the stats calculation.
:param maxthres: a upper threshold for values which will be included in the stats calculation.
:param out_no_data_val: output no data value if no valid pixels are within the polygon.
:param minfield: the name of the field for the min value (None or not specified to be ignored).
:param maxfield: the name of the field for the max value (None or not specified to be ignored).
:param meanfield: the name of the field for the mean value (None or not specified to be ignored).
:param stddevfield: the name of the field for the standard deviation value (None or not specified to be ignored).
:param sumfield: the name of the field for the sum value (None or not specified to be ignored).
:param countfield: the name of the field for the count (of number of pixels) value
                   (None or not specified to be ignored).
:param modefield: the name of the field for the mode value (None or not specified to be ignored).
:param medianfield: the name of the field for the median value (None or not specified to be ignored).
:param vec_def_epsg: an EPSG code can be specified for the vector layer is the projection is not well defined
                     within the inputted vector layer.

"""
    gdal.UseExceptions()
    
    try:    
        vecDS = gdal.OpenEx(vecfile, gdal.OF_VECTOR|gdal.OF_UPDATE )
        if vecDS is None:
            raise Exception("Could not open '{}'".format(vecfile)) 
    
        veclyr = vecDS.GetLayerByName(veclyrname)
        if veclyr is None:
            raise Exception("Could not open layer '{}'".format(veclyrname))

        calcZonalBandStats(veclyr, valsimg, imgbandidx, minthres, maxthres, out_no_data_val,
                           minfield, maxfield, meanfield, stddevfield, sumfield, countfield,
                           modefield, medianfield, vec_def_epsg)
            
        vecDS = None
    except Exception as e:
        print("Error Vector File: {}".format(vecfile), file=sys.stderr)
        print("Error Vector Layer: {}".format(veclyrname), file=sys.stderr)
        print("Error Image File: {}".format(valsimg), file=sys.stderr)
        raise e


def calcZonalBandStats(veclyr, valsimg, imgbandidx, minthres, maxthres, out_no_data_val,
                       minfield=None, maxfield=None, meanfield=None, stddevfield=None,
                       sumfield=None, countfield=None, modefield=None, medianfield=None,
                       vec_def_epsg=None):
    """
A function which calculates zonal statistics for a particular image band. 
If you know that the pixels in the values image are small with respect to 
the polygons then use this function.

:param veclyr: OGR vector layer object containing the geometries being processed and to which
               the stats will be written.
:param valsimg: the values image
:param imgbandidx: the index (starting at 1) of the image band for which the stats will be calculated.
                   If defined the no data value of the band will be ignored.
:param minthres: a lower threshold for values which will be included in the stats calculation.
:param maxthres: a upper threshold for values which will be included in the stats calculation.
:param out_no_data_val: output no data value if no valid pixels are within the polygon.
:param minfield: the name of the field for the min value (None or not specified to be ignored).
:param maxfield: the name of the field for the max value (None or not specified to be ignored).
:param meanfield: the name of the field for the mean value (None or not specified to be ignored).
:param stddevfield: the name of the field for the standard deviation value (None or not specified to be ignored).
:param sumfield: the name of the field for the sum value (None or not specified to be ignored).
:param countfield: the name of the field for the count (of number of pixels) value
                   (None or not specified to be ignored).
:param modefield: the name of the field for the mode value (None or not specified to be ignored).
:param medianfield: the name of the field for the median value (None or not specified to be ignored).
:param vec_def_epsg: an EPSG code can be specified for the vector layer is the projection is not well defined
                     within the inputted vector layer.

"""
    if modefield is not None:
        import scipy.stats.mstats
    gdal.UseExceptions()
    
    try:
        if veclyr is None:
            raise Exception("The inputted vector layer was None")

        if (minfield is None) and (maxfield is None) and (meanfield is None) and (stddevfield is None) and (
            sumfield is None) and (countfield is None) and (modefield is None) and (medianfield is None):
            raise Exception("At least one field needs to be specified for there is to an output.")
    
        imgDS = gdal.OpenEx(valsimg, gdal.GA_ReadOnly)
        if imgDS is None:
            raise Exception("Could not open '{}'".format(valsimg))
        imgband = imgDS.GetRasterBand(imgbandidx)
        if imgband is None:
            raise Exception("Could not find image band '{}'".format(imgbandidx))
        imgGeoTrans = imgDS.GetGeoTransform()
        img_wkt_str = imgDS.GetProjection()
        img_spatial_ref = osr.SpatialReference()
        img_spatial_ref.ImportFromWkt(img_wkt_str)
        img_spatial_ref.AutoIdentifyEPSG()
        epsg_img_spatial = img_spatial_ref.GetAuthorityCode(None)
        
        pixel_width = imgGeoTrans[1]
        pixel_height = imgGeoTrans[5]
        
        imgSizeX = imgDS.RasterXSize
        imgSizeY = imgDS.RasterYSize
    
        imgNoDataVal = imgband.GetNoDataValue()

        if vec_def_epsg is None:
            veclyr_spatial_ref = veclyr.GetSpatialRef()
            if veclyr_spatial_ref is None:
                raise Exception("Could not retrieve a projection object from the vector layer - "
                                "projection might not be be defined.")
            epsg_vec_spatial = veclyr_spatial_ref.GetAuthorityCode(None)
        else:
            epsg_vec_spatial = vec_def_epsg
            veclyr_spatial_ref = osr.SpatialReference()
            veclyr_spatial_ref.ImportFromEPSG(int(vec_def_epsg))

        if epsg_vec_spatial != epsg_img_spatial:
            imgDS = None
            vecDS = None
            raise Exception("Inputted raster and vector layers have different projections: ('{0}' '{1}') ".format(
                'Vector Layer Provided', valsimg))
        
        veclyrDefn = veclyr.GetLayerDefn()
        
        outFieldAtts = [minfield, maxfield, meanfield, stddevfield, sumfield, countfield, modefield, medianfield]
        for outattname in outFieldAtts:
            if outattname is not None:
                found = False
                for i in range(veclyrDefn.GetFieldCount()):
                    if veclyrDefn.GetFieldDefn(i).GetName().lower() == outattname.lower():
                        found = True
                        break
                if not found:
                    veclyr.CreateField(ogr.FieldDefn(outattname.lower(), ogr.OFTReal))
        
        fieldAttIdxs = dict()
        for outattname in outFieldAtts:
            if outattname is not None:
                fieldAttIdxs[outattname] = veclyr.FindFieldIndex(outattname.lower(), True)
        
        vec_mem_drv = ogr.GetDriverByName('Memory')
        img_mem_drv = gdal.GetDriverByName('MEM')
    
        # Iterate through features.
        openTransaction = False
        transactionStep = 20000
        nextTransaction = transactionStep
        nFeats = veclyr.GetFeatureCount(True)
        pbar = tqdm.tqdm(total=nFeats)
        counter = 0
        veclyr.ResetReading()
        feat = veclyr.GetNextFeature()
        while feat is not None:
            if not openTransaction:
                veclyr.StartTransaction()
                openTransaction = True
                
            if feat is not None:
                feat_geom = feat.geometry()
                if feat_geom is not None:
                    feat_bbox = feat_geom.GetEnvelope()
                    havepxls = True
                    
                    x1Sp = float(feat_bbox[0] - imgGeoTrans[0])
                    x2Sp = float(feat_bbox[1] - imgGeoTrans[0])
                    y1Sp = float(feat_bbox[3] - imgGeoTrans[3])
                    y2Sp = float(feat_bbox[2] - imgGeoTrans[3])
                                        
                    if x1Sp == 0.0:
                        x1 = 0
                    else:
                        x1 = int(x1Sp / pixel_width) - 1
                        
                    if x2Sp == 0.0:
                        x2 = 0
                    else:
                        x2 = int(x2Sp / pixel_width) + 1
                        
                    if y1Sp == 0.0:
                        y1 = 0
                    else:
                        y1 = int(y1Sp / pixel_height) - 1
                        
                    if y2Sp == 0.0:
                        y2 = 0
                    else:
                        y2 = int(y2Sp / pixel_height) + 1
                                        
                    if x1 < 0:
                        x1 = 0
                    elif x1 >= imgSizeX:
                        x1 = imgSizeX-1
                        
                    if x2 < 0:
                        x2 = 0
                    elif x2 >= imgSizeX:
                        x2 = imgSizeX-1
                        
                    if y1 < 0:
                        y1 = 0
                    elif y1 >= imgSizeY:
                        y1 = imgSizeY-1
                    
                    if y2 < 0:
                        y2 = 0
                    elif y2 >= imgSizeY:
                        y2 = imgSizeY-1
                                        
                    xsize = x2 - x1
                    ysize = y2 - y1
                    
                    if (xsize == 0) or (ysize == 0):
                        havepxls = False
                    
                    # Define the image ROI for the feature
                    src_offset = (x1, y1, xsize, ysize)

                    if havepxls:
                        # Read the band array.
                        src_array = imgband.ReadAsArray(*src_offset)
                    else:
                        src_array = None
                    
                    if (src_array is not None) and havepxls:
                
                        # calculate new geotransform of the feature subset
                        subGeoTrans = ((imgGeoTrans[0] + (src_offset[0] * imgGeoTrans[1])), imgGeoTrans[1], 0.0,
                                       (imgGeoTrans[3] + (src_offset[1] * imgGeoTrans[5])), 0.0, imgGeoTrans[5])
                
                        # Create a temporary vector layer in memory
                        vec_mem_ds = vec_mem_drv.CreateDataSource('out')
                        vec_mem_lyr = vec_mem_ds.CreateLayer('poly', veclyr_spatial_ref, ogr.wkbPolygon)
                        vec_mem_lyr.CreateFeature(feat.Clone())
                
                        # Rasterize the feature.
                        img_tmp_ds = img_mem_drv.Create('', src_offset[2], src_offset[3], 1, gdal.GDT_Byte)
                        img_tmp_ds.SetGeoTransform(subGeoTrans)
                        img_tmp_ds.SetProjection(img_wkt_str)
                        gdal.RasterizeLayer(img_tmp_ds, [1], vec_mem_lyr, burn_values=[1])
                        rv_array = img_tmp_ds.ReadAsArray()
                
                        # Mask the data vals array to feature.
                        mask_arr = numpy.ones_like(src_array, dtype=numpy.uint8)
                        if imgNoDataVal is not None:
                            mask_arr[src_array == imgNoDataVal] = 0
                            mask_arr[rv_array == 0] = 0
                            mask_arr[src_array < minthres] = 0
                            mask_arr[src_array > maxthres] = 0
                        else:
                            mask_arr[rv_array == 0] = 0
                            mask_arr[src_array < minthres] = 0
                            mask_arr[src_array > maxthres] = 0
                        mask_arr = mask_arr.flatten()
                        src_array_flat = src_array.flatten()
                        src_array_flat = src_array_flat[mask_arr==1]

                        if src_array_flat.shape[0] > 0:
                            if minfield is not None:
                                min_val = float(src_array_flat.min())
                                feat.SetField(fieldAttIdxs[minfield], min_val)
                            if maxfield is not None:
                                max_val = float(src_array_flat.max())
                                feat.SetField(fieldAttIdxs[maxfield], max_val)
                            if meanfield is not None:
                                mean_val = float(src_array_flat.mean())
                                feat.SetField(fieldAttIdxs[meanfield], mean_val)
                            if stddevfield is not None:
                                stddev_val = float(src_array_flat.std())
                                feat.SetField(fieldAttIdxs[stddevfield], stddev_val)
                            if sumfield is not None:
                                sum_val = float(src_array_flat.sum())
                                feat.SetField(fieldAttIdxs[sumfield], sum_val)
                            if countfield is not None:
                                count_val = float(src_array_flat.shape[0])
                                feat.SetField(fieldAttIdxs[countfield], count_val)
                            if modefield is not None:
                                mode_val, mode_count = scipy.stats.mstats.mode(src_array_flat)
                                mode_val = float(mode_val)
                                feat.SetField(fieldAttIdxs[modefield], mode_val)
                            if medianfield is not None:
                                median_val = float(numpy.ma.median(src_array_flat))
                                feat.SetField(fieldAttIdxs[medianfield], median_val)
                        else:
                            if minfield is not None:
                                feat.SetField(fieldAttIdxs[minfield], out_no_data_val)
                            if maxfield is not None:
                                feat.SetField(fieldAttIdxs[maxfield], out_no_data_val)
                            if meanfield is not None:
                                feat.SetField(fieldAttIdxs[meanfield], out_no_data_val)
                            if stddevfield is not None:
                                feat.SetField(fieldAttIdxs[stddevfield], out_no_data_val)
                            if sumfield is not None:
                                feat.SetField(fieldAttIdxs[sumfield], out_no_data_val)
                            if countfield is not None:
                                feat.SetField(fieldAttIdxs[countfield], out_no_data_val)
                            if modefield is not None:
                                feat.SetField(fieldAttIdxs[modefield], out_no_data_val)
                            if medianfield is not None:
                                feat.SetField(fieldAttIdxs[medianfield], out_no_data_val)
                        # Write the updated feature to the vector layer.
                        veclyr.SetFeature(feat)
            
                        vec_mem_ds = None
                        img_tmp_ds = None
            
            if (counter == nextTransaction) and openTransaction:
                veclyr.CommitTransaction()
                openTransaction = False
                nextTransaction = nextTransaction + transactionStep
            
            feat = veclyr.GetNextFeature()
            counter = counter + 1
            pbar.update(counter)
        if openTransaction:
            veclyr.CommitTransaction()
            openTransaction = False
        pbar.close()

        imgDS = None
    except Exception as e:
        print("Error Image File: {}".format(valsimg), file=sys.stderr)
        raise e


def calcZonalPolyPtsBandStatsFile(vecfile, veclyrname, valsimg, imgbandidx, outfield, vec_def_epsg=None):
    """
A funtion which extracts zonal stats for a polygon using the polygon centroid.
This is useful when you are intesecting a low resolution image with respect to
the polygon resolution.

:param vecfile: input vector file
:param veclyrname: input vector layer within the input file which specifies the features and
                   where the output stats will be written.
:param valsimg: the values image
:param imgbandidx: the index (starting at 1) of the image band for which the stats will be calculated.
                   If defined the no data value of the band will be ignored.
:param outfield: output field name within the vector layer.
:param vec_def_epsg: an EPSG code can be specified for the vector layer is the projection is not well defined
                     within the inputted vector layer.

"""
    gdal.UseExceptions()
    try:    
        vecDS = gdal.OpenEx(vecfile, gdal.OF_VECTOR|gdal.OF_UPDATE )
        if vecDS is None:
            raise Exception("Could not open '{}'".format(vecfile)) 
    
        veclyr = vecDS.GetLayerByName(veclyrname)
        if veclyr is None:
            raise Exception("Could not open layer '{}'".format(veclyrname))

        calcZonalPolyPtsBandStats(veclyr, valsimg, imgbandidx, outfield, vec_def_epsg)
            
        vecDS = None
    except Exception as e:
        print("Error Vector File: {}".format(vecfile), file=sys.stderr)
        print("Error Vector Layer: {}".format(veclyrname), file=sys.stderr)
        print("Error Image File: {}".format(valsimg), file=sys.stderr)
        raise e


def calcZonalPolyPtsBandStats(veclyr, valsimg, imgbandidx, outfield, vec_def_epsg=None):
    """
A funtion which extracts zonal stats for a polygon using the polygon centroid.
This is useful when you are intesecting a low resolution image with respect to
the polygon resolution.

:param veclyr: OGR vector layer object containing the geometries being processed and to
               which the stats will be written.
:param valsimg: the values image
:param imgbandidx: the index (starting at 1) of the image band for which the stats will be calculated.
                   If defined the no data value of the band will be ignored.
:param outfield: output field name within the vector layer.
:param vec_def_epsg: an EPSG code can be specified for the vector layer is the projection is not well defined
                     within the inputted vector layer.

"""
    gdal.UseExceptions()
    try:
        if veclyr is None:
            raise Exception("The inputted vector layer was None")
    
        imgDS = gdal.OpenEx(valsimg, gdal.GA_ReadOnly)
        if imgDS is None:
            raise Exception("Could not open '{}'".format(valsimg))
        imgband = imgDS.GetRasterBand(imgbandidx)
        if imgband is None:
            raise Exception("Could not find image band '{}'".format(imgbandidx))
        imgGeoTrans = imgDS.GetGeoTransform()
        img_wkt_str = imgDS.GetProjection()
        img_spatial_ref = osr.SpatialReference()
        img_spatial_ref.ImportFromWkt(img_wkt_str)
        epsg_img_spatial = img_spatial_ref.GetAuthorityCode(None)
        
        pixel_width = imgGeoTrans[1]
        pixel_height = imgGeoTrans[5]
        
        imgSizeX = imgDS.RasterXSize
        imgSizeY = imgDS.RasterYSize

        if vec_def_epsg is None:
            veclyr_spatial_ref = veclyr.GetSpatialRef()
            if veclyr_spatial_ref is None:
                raise Exception("Could not retrieve a projection object from the vector layer - "
                                "projection not might be be defined.")
            epsg_vec_spatial = veclyr_spatial_ref.GetAuthorityCode(None)
        else:
            epsg_vec_spatial = vec_def_epsg

        if epsg_vec_spatial != epsg_img_spatial:
            imgDS = None
            vecDS = None
            raise Exception("Inputted raster and vector layers have different projections: ('{0}' '{1}') ".format(
                'Vector Layer Provided', valsimg))
        
        veclyrDefn = veclyr.GetLayerDefn()
        
        found = False
        for i in range(veclyrDefn.GetFieldCount()):
            if veclyrDefn.GetFieldDefn(i).GetName().lower() == outfield.lower():
                found = True
                break
        if not found:
            veclyr.CreateField(ogr.FieldDefn(outfield.lower(), ogr.OFTReal))
        
        outfieldidx = veclyr.FindFieldIndex(outfield.lower(), True)
    
        vec_mem_drv = ogr.GetDriverByName('Memory')
        img_mem_drv = gdal.GetDriverByName('MEM')
        
        # Iterate through features.
        openTransaction = False
        transactionStep = 20000
        nextTransaction = transactionStep
        nFeats = veclyr.GetFeatureCount(True)
        pbar = tqdm.tqdm(total=nFeats)
        counter = 0
        veclyr.ResetReading()
        feat = veclyr.GetNextFeature()
        while feat is not None:
            if not openTransaction:
                veclyr.StartTransaction()
                openTransaction = True
            
            if feat is not None:
                feat_geom = feat.geometry()
                if feat_geom is not None:
                    feat_bbox = feat_geom.GetEnvelope()
                    havepxls = True
                    
                    x1Sp = float(feat_bbox[0] - imgGeoTrans[0])
                    x2Sp = float(feat_bbox[1] - imgGeoTrans[0])
                    y1Sp = float(feat_bbox[3] - imgGeoTrans[3])
                    y2Sp = float(feat_bbox[2] - imgGeoTrans[3])
                                        
                    if x1Sp == 0.0:
                        x1 = 0
                    else:
                        x1 = int(x1Sp / pixel_width) - 1
                        
                    if x2Sp == 0.0:
                        x2 = 0
                    else:
                        x2 = int(x2Sp / pixel_width) + 1
                        
                    if y1Sp == 0.0:
                        y1 = 0
                    else:
                        y1 = int(y1Sp / pixel_height) - 1
                        
                    if y2Sp == 0.0:
                        y2 = 0
                    else:
                        y2 = int(y2Sp / pixel_height) + 1
                                        
                    if x1 < 0:
                        x1 = 0
                    elif x1 >= imgSizeX:
                        x1 = imgSizeX-1
                        
                    if x2 < 0:
                        x2 = 0
                    elif x2 >= imgSizeX:
                        x2 = imgSizeX-1
                        
                    if y1 < 0:
                        y1 = 0
                    elif y1 >= imgSizeY:
                        y1 = imgSizeY-1
                    
                    if y2 < 0:
                        y2 = 0
                    elif y2 >= imgSizeY:
                        y2 = imgSizeY-1
                                        
                    xsize = x2 - x1
                    ysize = y2 - y1
                    
                    if (xsize == 0) or (ysize == 0):
                        havepxls = False
                    
                    # Define the image ROI for the feature
                    src_offset = (x1, y1, xsize, ysize)

                    if havepxls:
                        # Read the band array.
                        src_array = imgband.ReadAsArray(*src_offset)
                    else:
                        src_array = None
                    
                    if (src_array is not None) and havepxls:
                        subTLX = (imgGeoTrans[0] + (src_offset[0] * imgGeoTrans[1]))
                        subTLY = (imgGeoTrans[3] + (src_offset[1] * imgGeoTrans[5]))
                        resX = imgGeoTrans[1]
                        resY = imgGeoTrans[5]
                                    
                        ptx,pty,ptz = feat.GetGeometryRef().Centroid().GetPoint()
                        
                        xOff = math.floor((ptx - subTLX) / resX)
                        yOff = math.floor((pty - subTLY) / resY)
                        
                        if xOff < 0:
                            xOff = 0
                        if xOff >= xsize:
                            xOff = xsize - 1
                            
                        if yOff < 0:
                            yOff = 0
                        if yOff >= ysize:
                            yOff = ysize - 1
                
                        out_val = float(src_array[yOff, xOff])
                        feat.SetField(outfieldidx, out_val)
            
                        veclyr.SetFeature(feat)
            
                        vec_mem_ds = None
                        img_tmp_ds = None
            
            if (counter == nextTransaction) and openTransaction:
                veclyr.CommitTransaction()
                openTransaction = False
                nextTransaction = nextTransaction + transactionStep
            
            feat = veclyr.GetNextFeature()
            counter = counter + 1
            pbar.update(counter)
    
        if openTransaction:
            veclyr.CommitTransaction()
            openTransaction = False
        pbar.close()

        imgDS = None
    except Exception as e:
        print("Error Image File: {}".format(valsimg), file=sys.stderr)
        raise e


def calcZonalBandStatsTestPolyPtsFile(vecfile, veclyrname, valsimg, imgbandidx, minthres, maxthres, out_no_data_val,
                                      percentile=None, percentilefield=None, minfield=None, maxfield=None, meanfield=None,
                                      stddevfield=None, sumfield=None, countfield=None, modefield=None, medianfield=None,
                                      vec_def_epsg=None):
    """
A function which calculates zonal statistics for a particular image band. If unsure then use this function. 
This function tests whether 1 or more pixels has been found within the polygon and if not then the centroid 
use used to find a value for the polygon.

If you are unsure as to whether the pixels are small enough to be contained within all the polygons then 
use this function.

:param vecfile: input vector file
:param veclyrname: input vector layer within the input file which specifies the features and where the
                   output stats will be written.
:param valsimg: the values image
:param imgbandidx: the index (starting at 1) of the image band for which the stats will be calculated.
                   If defined the no data value of the band will be ignored.
:param minthres: a lower threshold for values which will be included in the stats calculation.
:param maxthres: a upper threshold for values which will be included in the stats calculation.
:param out_no_data_val: output no data value if no valid pixels are within the polygon.
:param percentile: the percentile value to calculate.
:param percentilefield: the name of the field for the percentile value (None or not specified to be ignored).
:param minfield: the name of the field for the min value (None or not specified to be ignored).
:param maxfield: the name of the field for the max value (None or not specified to be ignored).
:param meanfield: the name of the field for the mean value (None or not specified to be ignored).
:param stddevfield: the name of the field for the standard deviation value (None or not specified to be ignored).
:param sumfield: the name of the field for the sum value (None or not specified to be ignored).
:param countfield: the name of the field for the count (of number of pixels) value
                   (None or not specified to be ignored).
:param modefield: the name of the field for the mode value (None or not specified to be ignored).
:param medianfield: the name of the field for the median value (None or not specified to be ignored).
:param vec_def_epsg: an EPSG code can be specified for the vector layer is the projection is not well defined
                     within the inputted vector layer.

"""
    gdal.UseExceptions()
    
    try:    
        vecDS = gdal.OpenEx(vecfile, gdal.OF_VECTOR|gdal.OF_UPDATE )
        if vecDS is None:
            raise Exception("Could not open '{}'".format(vecfile)) 
    
        veclyr = vecDS.GetLayerByName(veclyrname)
        if veclyr is None:
            raise Exception("Could not open layer '{}'".format(veclyrname))

        calcZonalBandStatsTestPolyPts(veclyr, valsimg, imgbandidx, minthres, maxthres, out_no_data_val, percentile,
                                      percentilefield, minfield, maxfield, meanfield, stddevfield, sumfield,
                                      countfield, modefield, medianfield, vec_def_epsg)
    
        vecDS = None
    except Exception as e:
        print("Error Vector File: {}".format(vecfile), file=sys.stderr)
        print("Error Vector Layer: {}".format(veclyrname), file=sys.stderr)
        print("Error Image File: {}".format(valsimg), file=sys.stderr)
        raise e


def calcZonalBandStatsTestPolyPts(veclyr, valsimg, imgbandidx, minthres, maxthres, out_no_data_val,
                                  percentile=None, percentilefield=None, minfield=None, maxfield=None,
                                  meanfield=None, stddevfield=None, sumfield=None, countfield=None,
                                  modefield=None, medianfield=None, vec_def_epsg=None):
    """
A function which calculates zonal statistics for a particular image band. If unsure then use this function. 
This function tests whether 1 or more pixels has been found within the polygon and if not then the centroid 
use used to find a value for the polygon.

If you are unsure as to whether the pixels are small enough to be contained within all the polygons then 
use this function.

:param veclyr: OGR vector layer object containing the geometries being processed and to which the stats will be written.
:param valsimg: the values image
:param imgbandidx: the index (starting at 1) of the image band for which the stats will be calculated.
                   If defined the no data value of the band will be ignored.
:param minthres: a lower threshold (inclusive) for values which will be included in the stats calculation.
:param maxthres: a upper threshold (inclusive) for values which will be included in the stats calculation.
:param out_no_data_val: output no data value if no valid pixels are within the polygon.
:param percentile: the percentile value to calculate.
:param percentilefield: the name of the field for the percentile value (None or not specified to be ignored).
:param minfield: the name of the field for the min value (None or not specified to be ignored).
:param maxfield: the name of the field for the max value (None or not specified to be ignored).
:param meanfield: the name of the field for the mean value (None or not specified to be ignored).
:param stddevfield: the name of the field for the standard deviation value (None or not specified to be ignored).
:param sumfield: the name of the field for the sum value (None or not specified to be ignored).
:param countfield: the name of the field for the count (of number of pixels) value
                   (None or not specified to be ignored).
:param modefield: the name of the field for the mode value (None or not specified to be ignored).
:param medianfield: the name of the field for the median value (None or not specified to be ignored).
:param vec_def_epsg: an EPSG code can be specified for the vector layer is the projection is not well defined
                     within the inputted vector layer.

"""
    if modefield is not None:
        import scipy.stats.mstats
    gdal.UseExceptions()
    
    try:
        if veclyr is None:
            raise Exception("The inputted vector layer was None")

        if (minfield is None) and (maxfield is None) and (meanfield is None) and (stddevfield is None) and (
            sumfield is None) and (countfield is None) and (modefield is None) and (medianfield is None) and (percentilefield is None):
            raise Exception("At least one field needs to be specified for there is to an output.")
    
        imgDS = gdal.OpenEx(valsimg, gdal.GA_ReadOnly)
        if imgDS is None:
            raise Exception("Could not open '{}'".format(valsimg))
        imgband = imgDS.GetRasterBand(imgbandidx)
        if imgband is None:
            raise Exception("Could not find image band '{}'".format(imgbandidx))
        imgGeoTrans = imgDS.GetGeoTransform()
        img_wkt_str = imgDS.GetProjection()
        img_spatial_ref = osr.SpatialReference()
        img_spatial_ref.ImportFromWkt(img_wkt_str)
        epsg_img_spatial = img_spatial_ref.GetAuthorityCode(None)
        
        pixel_width = imgGeoTrans[1]
        pixel_height = imgGeoTrans[5]
        
        imgSizeX = imgDS.RasterXSize
        imgSizeY = imgDS.RasterYSize
            
        imgNoDataVal = imgband.GetNoDataValue()

        if vec_def_epsg is None:
            veclyr_spatial_ref = veclyr.GetSpatialRef()
            if veclyr_spatial_ref is None:
                raise Exception("Could not retrieve a projection object from the vector layer - projection might be be defined.")
            epsg_vec_spatial = veclyr_spatial_ref.GetAuthorityCode(None)
        else:
            epsg_vec_spatial = vec_def_epsg
            veclyr_spatial_ref = osr.SpatialReference()
            veclyr_spatial_ref.ImportFromEPSG(int(vec_def_epsg))

        if epsg_vec_spatial != epsg_img_spatial:
            imgDS = None
            vecDS = None
            raise Exception("Inputted raster and vector layers have different projections: ('{0}' '{1}') ".format(
                'Vector Layer Provided', valsimg))
        
        veclyrDefn = veclyr.GetLayerDefn()
        
        outFieldAtts = [minfield, maxfield, meanfield, stddevfield, sumfield, countfield, modefield, medianfield, percentilefield]
        for outattname in outFieldAtts:
            if outattname is not None:
                found = False
                for i in range(veclyrDefn.GetFieldCount()):
                    if veclyrDefn.GetFieldDefn(i).GetName().lower() == outattname.lower():
                        found = True
                        break
                if not found:
                    veclyr.CreateField(ogr.FieldDefn(outattname.lower(), ogr.OFTReal))
        
        fieldAttIdxs = dict()
        for outattname in outFieldAtts:
            if outattname is not None:
                fieldAttIdxs[outattname] = veclyr.FindFieldIndex(outattname.lower(), True)
        
        vec_mem_drv = ogr.GetDriverByName('Memory')
        img_mem_drv = gdal.GetDriverByName('MEM')
    
        # Iterate through features.
        openTransaction = False
        transactionStep = 20000
        nextTransaction = transactionStep
        nFeats = veclyr.GetFeatureCount(True)
        pbar = tqdm.tqdm(total=nFeats)
        counter = 0
        veclyr.ResetReading()
        feat = veclyr.GetNextFeature()
        while feat is not None:
            if not openTransaction:
                veclyr.StartTransaction()
                openTransaction = True
            
            if feat is not None:
                feat_geom = feat.geometry()
                if feat_geom is not None:
                    feat_bbox = feat_geom.GetEnvelope()
                    
                    havepxls = True
                    
                    x1Sp = float(feat_bbox[0] - imgGeoTrans[0])
                    x2Sp = float(feat_bbox[1] - imgGeoTrans[0])
                    y1Sp = float(feat_bbox[3] - imgGeoTrans[3])
                    y2Sp = float(feat_bbox[2] - imgGeoTrans[3])
                                        
                    if x1Sp == 0.0:
                        x1 = 0
                    else:
                        x1 = int(x1Sp / pixel_width) - 1
                        
                    if x2Sp == 0.0:
                        x2 = 0
                    else:
                        x2 = int(x2Sp / pixel_width) + 1
                        
                    if y1Sp == 0.0:
                        y1 = 0
                    else:
                        y1 = int(y1Sp / pixel_height) - 1
                        
                    if y2Sp == 0.0:
                        y2 = 0
                    else:
                        y2 = int(y2Sp / pixel_height) + 1
                                        
                    if x1 < 0:
                        x1 = 0
                    elif x1 >= imgSizeX:
                        x1 = imgSizeX-1
                        
                    if x2 < 0:
                        x2 = 0
                    elif x2 >= imgSizeX:
                        x2 = imgSizeX-1
                        
                    if y1 < 0:
                        y1 = 0
                    elif y1 >= imgSizeY:
                        y1 = imgSizeY-1
                    
                    if y2 < 0:
                        y2 = 0
                    elif y2 >= imgSizeY:
                        y2 = imgSizeY-1
                                        
                    xsize = x2 - x1
                    ysize = y2 - y1
                    
                    if (xsize == 0) or (ysize == 0):
                        havepxls = False
                    
                    # Define the image ROI for the feature
                    src_offset = (x1, y1, xsize, ysize)

                    if havepxls:
                        # Read the band array.
                        src_array = imgband.ReadAsArray(*src_offset)
                    else:
                        src_array = None
                    
                    if (src_array is not None) and havepxls:
                
                        # calculate new geotransform of the feature subset
                        subGeoTrans = ((imgGeoTrans[0] + (src_offset[0] * imgGeoTrans[1])), imgGeoTrans[1], 0.0,
                                       (imgGeoTrans[3] + (src_offset[1] * imgGeoTrans[5])), 0.0, imgGeoTrans[5])
                
                        # Create a temporary vector layer in memory
                        vec_mem_ds = vec_mem_drv.CreateDataSource('out')
                        vec_mem_lyr = vec_mem_ds.CreateLayer('poly', veclyr_spatial_ref, ogr.wkbPolygon)
                        vec_mem_lyr.CreateFeature(feat.Clone())
                
                        # Rasterize the feature.
                        img_tmp_ds = img_mem_drv.Create('', src_offset[2], src_offset[3], 1, gdal.GDT_Byte)
                        img_tmp_ds.SetGeoTransform(subGeoTrans)
                        img_tmp_ds.SetProjection(img_wkt_str)
                        gdal.RasterizeLayer(img_tmp_ds, [1], vec_mem_lyr, burn_values=[1])
                        rv_array = img_tmp_ds.ReadAsArray()
                
                        # Mask the data vals array to feature
                        mask_arr = numpy.ones_like(src_array, dtype=numpy.uint8)
                        if imgNoDataVal is not None:
                            mask_arr[src_array == imgNoDataVal] = 0
                            mask_arr[rv_array == 0] = 0
                            mask_arr[src_array < minthres] = 0
                            mask_arr[src_array > maxthres] = 0
                        else:
                            mask_arr[rv_array == 0] = 0
                            mask_arr[src_array < minthres] = 0
                            mask_arr[src_array > maxthres] = 0
                        mask_arr = mask_arr.flatten()
                        src_array_flat = src_array.flatten()
                        src_array_flat = src_array_flat[mask_arr == 1]

                        if src_array_flat.shape[0] > 0:
                            if minfield is not None:
                                min_val = float(src_array_flat.min())
                                feat.SetField(fieldAttIdxs[minfield], min_val)
                            if maxfield is not None:
                                max_val = float(src_array_flat.max())
                                feat.SetField(fieldAttIdxs[maxfield], max_val)
                            if meanfield is not None:
                                mean_val = float(src_array_flat.mean())
                                feat.SetField(fieldAttIdxs[meanfield], mean_val)
                            if stddevfield is not None:
                                stddev_val = float(src_array_flat.std())
                                feat.SetField(fieldAttIdxs[stddevfield], stddev_val)
                            if sumfield is not None:
                                sum_val = float(src_array_flat.sum())
                                feat.SetField(fieldAttIdxs[sumfield], sum_val)
                            if countfield is not None:
                                count_val = float(src_array_flat.shape[0])
                                feat.SetField(fieldAttIdxs[countfield], count_val)
                            if modefield is not None:
                                mode_val, mode_count = scipy.stats.mstats.mode(src_array_flat)
                                mode_val = float(mode_val)
                                feat.SetField(fieldAttIdxs[modefield], mode_val)
                            if medianfield is not None:
                                median_val = float(numpy.ma.median(src_array_flat))
                                feat.SetField(fieldAttIdxs[medianfield], median_val)
                            if percentilefield is not None:
                                perc_val = float(numpy.percentile(numpy.ma.compressed(src_array_flat), float(percentile)))
                                feat.SetField(fieldAttIdxs[percentilefield], perc_val)
                                
                        else:
                            subTLX = (imgGeoTrans[0] + (src_offset[0] * imgGeoTrans[1]))
                            subTLY = (imgGeoTrans[3] + (src_offset[1] * imgGeoTrans[5]))
                            resX = imgGeoTrans[1]
                            resY = imgGeoTrans[5]
                                        
                            ptx,pty,ptz = feat.GetGeometryRef().Centroid().GetPoint()
                            
                            xOff = math.floor((ptx - subTLX) / resX)
                            yOff = math.floor((pty - subTLY) / resY)
                            
                            if xOff < 0:
                                xOff = 0
                            if xOff >= xsize:
                                xOff = xsize - 1
                                
                            if yOff < 0:
                                yOff = 0
                            if yOff >= ysize:
                                yOff = ysize - 1

                            out_val = float(src_array[yOff, xOff])
                            invalid_val = False
                            if imgNoDataVal is not None:
                                if out_val == imgNoDataVal:
                                    invalid_val = True
                            if out_val < minthres:
                                invalid_val = True
                            if out_val > maxthres:
                                invalid_val = True

                            if invalid_val:
                                if minfield is not None:
                                    feat.SetField(fieldAttIdxs[minfield], out_no_data_val)
                                if maxfield is not None:
                                    feat.SetField(fieldAttIdxs[maxfield], out_no_data_val)
                                if meanfield is not None:
                                    feat.SetField(fieldAttIdxs[meanfield], out_no_data_val)
                                if stddevfield is not None:
                                    feat.SetField(fieldAttIdxs[stddevfield], out_no_data_val)
                                if sumfield is not None:
                                    feat.SetField(fieldAttIdxs[sumfield], out_no_data_val)
                                if countfield is not None:
                                    feat.SetField(fieldAttIdxs[countfield], 0.0)
                                if modefield is not None:
                                    feat.SetField(fieldAttIdxs[modefield], out_no_data_val)
                                if medianfield is not None:
                                    feat.SetField(fieldAttIdxs[medianfield], out_no_data_val)
                                if percentilefield is not None:
                                    feat.SetField(fieldAttIdxs[percentilefield], perc_val)
                            else:
                                if minfield is not None:
                                    feat.SetField(fieldAttIdxs[minfield], out_val)
                                if maxfield is not None:
                                    feat.SetField(fieldAttIdxs[maxfield], out_val)
                                if meanfield is not None:
                                    feat.SetField(fieldAttIdxs[meanfield], out_val)
                                if stddevfield is not None:
                                    feat.SetField(fieldAttIdxs[stddevfield], 0.0)
                                if sumfield is not None:
                                    feat.SetField(fieldAttIdxs[sumfield], out_val)
                                if countfield is not None:
                                    feat.SetField(fieldAttIdxs[countfield], 1.0)
                                if modefield is not None:
                                    feat.SetField(fieldAttIdxs[modefield], out_val)
                                if medianfield is not None:
                                    feat.SetField(fieldAttIdxs[medianfield], out_val)
                                if percentilefield is not None:
                                    feat.SetField(fieldAttIdxs[percentilefield], perc_val)
                            
                        # Write the updated feature to the vector layer.
                        veclyr.SetFeature(feat)
            
                        vec_mem_ds = None
                        img_tmp_ds = None            
            
            if (counter == nextTransaction) and openTransaction:
                veclyr.CommitTransaction()
                openTransaction = False
                nextTransaction = nextTransaction + transactionStep
            
            feat = veclyr.GetNextFeature()
            counter = counter + 1
            pbar.update(counter)
        if openTransaction:
            veclyr.CommitTransaction()
            openTransaction = False
        pbar.close()
    
        imgDS = None
    except Exception as e:
        print("Error Image File: {}".format(valsimg), file=sys.stderr)
        raise e


def extPointBandValuesFile(vecfile, veclyrname, valsimg, imgbandidx, minthres, maxthres, out_no_data_val, outfield,
                           reproj_vec=False, vec_def_epsg=None):
    """
A function which extracts point values for an input vector file for a particular image band.

:param vecfile: input vector file
:param veclyrname: input vector layer within the input file which specifies the features and where the
                   output stats will be written.
:param valsimg: the values image
:param imgbandidx: the index (starting at 1) of the image band for which the stats will be calculated.
                   If defined the no data value of the band will be ignored.
:param minthres: a lower threshold for values which will be included in the stats calculation.
:param maxthres: a upper threshold for values which will be included in the stats calculation.
:param out_no_data_val: output no data value if no valid pixels are within the polygon.
:param outfield: the name of the field in the vector layer where the pixel values will be written.
:param reproj_vec: boolean to specify whether the vector layer should be reprojected on the fly during processing
                   if the projections are different. Default: False to ensure it is the users intention.
:param vec_def_epsg: an EPSG code can be specified for the vector layer is the projection is not well defined
                     within the inputted vector layer.

"""
    gdal.UseExceptions()

    try:
        vecDS = gdal.OpenEx(vecfile, gdal.OF_VECTOR | gdal.OF_UPDATE)
        if vecDS is None:
            raise Exception("Could not open '{}'".format(vecfile))

        veclyr = vecDS.GetLayerByName(veclyrname)
        if veclyr is None:
            raise Exception("Could not open layer '{}'".format(veclyrname))

        extPointBandValues(veclyr, valsimg, imgbandidx, minthres, maxthres, out_no_data_val, outfield, reproj_vec, vec_def_epsg)

        vecDS = None
    except Exception as e:
        print("Error Vector File: {}".format(vecfile), file=sys.stderr)
        print("Error Vector Layer: {}".format(veclyrname), file=sys.stderr)
        print("Error Image File: {}".format(valsimg), file=sys.stderr)
        raise e


def extPointBandValues(veclyr, valsimg, imgbandidx, minthres, maxthres, out_no_data_val, outfield, reproj_vec=False,
                       vec_def_epsg=None):
    """
A function which extracts point values for an input vector file for a particular image band.

:param veclyr: OGR vector layer object containing the geometries being processed and to which
               the stats will be written.
:param valsimg: the values image
:param imgbandidx: the index (starting at 1) of the image band for which the stats will be calculated.
                   If defined the no data value of the band will be ignored.
:param minthres: a lower threshold for values which will be included in the stats calculation.
:param maxthres: a upper threshold for values which will be included in the stats calculation.
:param out_no_data_val: output no data value if no valid pixels are within the polygon.
:param outfield: the name of the field in the vector layer where the pixel values will be written.
:param reproj_vec: boolean to specify whether the vector layer should be reprojected on the fly during processing
                   if the projections are different. Default: False to ensure it is the users intention.
:param vec_def_epsg: an EPSG code can be specified for the vector layer is the projection is not well defined
                     within the inputted vector layer.

"""
    gdal.UseExceptions()
    import rsgislib.tools.geometrytools
    try:
        if veclyr is None:
            raise Exception("The inputted vector layer was None")

        if outfield is None:
            raise Exception("Output field specified as none, a name needs to be given.")
        elif outfield == '':
            raise Exception("Output field specified as an empty string, a name needs to be given.")

        veclyrDefn = veclyr.GetLayerDefn()
        lyr_geom_type = ogr.GeometryTypeToName(veclyrDefn.GetGeomType())
        if lyr_geom_type.lower() != 'point':
            raise Exception("The layer geometry type must be point.")

        imgDS = gdal.OpenEx(valsimg, gdal.GA_ReadOnly)
        if imgDS is None:
            raise Exception("Could not open '{}'".format(valsimg))
        imgband = imgDS.GetRasterBand(imgbandidx)
        if imgband is None:
            raise Exception("Could not find image band '{}'".format(imgbandidx))
        imgGeoTrans = imgDS.GetGeoTransform()
        img_wkt_str = imgDS.GetProjection()
        img_spatial_ref = osr.SpatialReference()
        img_spatial_ref.ImportFromWkt(img_wkt_str)
        img_spatial_ref.AutoIdentifyEPSG()
        epsg_img_spatial = img_spatial_ref.GetAuthorityCode(None)

        pixel_width = imgGeoTrans[1]
        pixel_height = imgGeoTrans[5]

        imgSizeX = imgDS.RasterXSize
        imgSizeY = imgDS.RasterYSize

        imgNoDataVal = imgband.GetNoDataValue()
        out_no_data_val = float(out_no_data_val)

        if vec_def_epsg is None:
            veclyr_spatial_ref = veclyr.GetSpatialRef()
            if veclyr_spatial_ref is None:
                raise Exception("Could not retrieve a projection object from the vector layer - projection might be be defined.")
            epsg_vec_spatial = veclyr_spatial_ref.GetAuthorityCode(None)
        else:
            epsg_vec_spatial = vec_def_epsg
            veclyr_spatial_ref = osr.SpatialReference()
            veclyr_spatial_ref.ImportFromEPSG(int(vec_def_epsg))
        pt_reprj = False
        if epsg_vec_spatial != epsg_img_spatial:
            if reproj_vec:
                pt_reprj = True
            else:
                raise Exception("Input vector and image datasets are in different projections (EPSG:{} / EPSG:{})."
                                 "You can select option to reproject.".format(epsg_vec_spatial, epsg_img_spatial))

        found = False
        for i in range(veclyrDefn.GetFieldCount()):
            if veclyrDefn.GetFieldDefn(i).GetName().lower() == outfield.lower():
                found = True
                break
        if not found:
            veclyr.CreateField(ogr.FieldDefn(outfield.lower(), ogr.OFTReal))

        out_field_idx = veclyr.FindFieldIndex(outfield.lower(), True)

        # Iterate through features.
        openTransaction = False
        transactionStep = 20000
        nextTransaction = transactionStep
        nFeats = veclyr.GetFeatureCount(True)
        pbar = tqdm.tqdm(total=nFeats)
        counter = 0
        veclyr.ResetReading()
        feat = veclyr.GetNextFeature()
        while feat is not None:
            if not openTransaction:
                veclyr.StartTransaction()
                openTransaction = True

            if feat is not None:
                feat_geom = feat.geometry()
                if feat_geom is not None:
                    pt_in_img = True
                    x_pt = feat_geom.GetX()
                    y_pt = feat_geom.GetY()

                    if pt_reprj:
                        if veclyr_spatial_ref.EPSGTreatsAsLatLong():
                            x_pt, y_pt = rsgislib.tools.geometrytools.reprojPoint(veclyr_spatial_ref, img_spatial_ref, y_pt, x_pt)
                        else:
                            x_pt, y_pt = rsgislib.tools.geometrytools.reprojPoint(veclyr_spatial_ref, img_spatial_ref, x_pt, y_pt)

                    x_pt_off = float(x_pt - imgGeoTrans[0])
                    y_pt_off = float(y_pt - imgGeoTrans[3])

                    if x_pt_off == 0.0:
                        x_pxl = 0
                    else:
                        x_pxl = int(x_pt_off / pixel_width) - 1

                    if y_pt_off == 0.0:
                        y_pxl = 0
                    else:
                        y_pxl = int(y_pt_off / pixel_height) - 1

                    if x_pxl < 0:
                        pt_in_img = False
                    elif x_pxl >= imgSizeX:
                        pt_in_img = False

                    if y_pxl < 0:
                        pt_in_img = False
                    elif y_pxl >= imgSizeY:
                        pt_in_img = False

                    if pt_in_img:
                        src_offset = (x_pxl, y_pxl, 1, 1)
                        src_array = imgband.ReadAsArray(*src_offset)
                        pxl_val = src_array[0][0]
                        out_val = float(pxl_val)
                        if pxl_val == imgNoDataVal:
                            out_val = out_no_data_val
                        elif pxl_val < minthres:
                            out_val = out_no_data_val
                        elif pxl_val > maxthres:
                            out_val = out_no_data_val

                        feat.SetField(out_field_idx, out_val)
                    else:
                        feat.SetField(out_field_idx, out_no_data_val)

                    veclyr.SetFeature(feat)

            if (counter == nextTransaction) and openTransaction:
                veclyr.CommitTransaction()
                openTransaction = False
                nextTransaction = nextTransaction + transactionStep

            feat = veclyr.GetNextFeature()
            counter = counter + 1
            pbar.update(1)
        pbar.close()

        if openTransaction:
            veclyr.CommitTransaction()
            openTransaction = False

        imgDS = None

    except Exception as e:
        print("Error Image File: {}".format(valsimg), file=sys.stderr)
        raise e


