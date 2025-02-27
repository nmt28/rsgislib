#!/usr/bin/env python
############################################################################
#  leastcostpath.py
#
#  Copyright 2017 RSGISLib.
#
#  RSGISLib: 'The remote sensing and GIS Software Library'
#
#  RSGISLib is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  RSGISLib is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with RSGISLib.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Purpose:  Calculate the least cost path across a raster.
#
# Author: Pete Bunting
# Email: petebunting@mac.com
# Date: 17/08/2017
# Version: 1.0
#
# History:
# Version 1.0 - Created.
#
############################################################################

from osgeo import gdal
from osgeo import osr
import numpy


def _coord2pixelOffset(rasterfn, x, y):
    raster = gdal.Open(rasterfn)
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    xOffset = int((x - originX) / pixelWidth)
    yOffset = int((y - originY) / pixelHeight)
    return xOffset, yOffset


def _createPath(CostSurfaceImg, costSurfaceArray, startCoord, stopCoord):
    import skimage.graph

    # coordinates to array index
    startCoordX = startCoord[0]
    startCoordY = startCoord[1]
    startIndexX, startIndexY = _coord2pixelOffset(
        CostSurfaceImg, startCoordX, startCoordY
    )

    stopCoordX = stopCoord[0]
    stopCoordY = stopCoord[1]
    stopIndexX, stopIndexY = _coord2pixelOffset(CostSurfaceImg, stopCoordX, stopCoordY)

    # create path
    indices, weight = skimage.graph.route_through_array(
        costSurfaceArray,
        (startIndexY, startIndexX),
        (stopIndexY, stopIndexX),
        geometric=True,
        fully_connected=True,
    )
    indices = numpy.array(indices).T
    path = numpy.zeros_like(costSurfaceArray)
    path[indices[0], indices[1]] = 1
    return path


def _array2raster(newRasterfn, rasterfn, array, outFormat):
    raster = gdal.Open(rasterfn)
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    cols = array.shape[1]
    rows = array.shape[0]

    driver = gdal.GetDriverByName(outFormat)
    outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Byte)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()
    outRaster = None
    raster = None


def perform_least_cost_path_calc(
    cost_surface_img: str,
    output_img: str,
    start_coord: list,
    stop_coord: list,
    gdalformat: str = "KEA",
    cost_img_band: int = 1,
):
    """
    Calculates least cost path for a raster surface from start coord to stop coord:

    Version of code from:
    https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html#create-least-cost-path

    :param cost_surface_img: Input image to calculate cost path from
    :param output_img: Output image
    :param start_coord: Start coordinate (e.g., (263155.9, 291809.1))
    :param stop_coord: End coordinate (e.g., (263000.1, 292263.7))
    :param gdalformat: GDAL format (default=KEA)
    :param cost_img_band: Band in input image to use for cost analysis (default=1)

    """
    # Read gdal raster as array.
    gdalRasterDS = gdal.Open(cost_surface_img)
    costSurfaceArray = gdalRasterDS.GetRasterBand(cost_img_band).ReadAsArray()

    # Creates path array
    pathArray = _createPath(cost_surface_img, costSurfaceArray, start_coord, stop_coord)

    # Converts path array to raster
    _array2raster(output_img, cost_surface_img, pathArray, gdalformat)
