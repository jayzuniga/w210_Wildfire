"""
pickle_sat.py

Functions for filtering worldwide satellite FAPAR data into California only and saving to pickle files.

Usage

python process_sat.py <input_dir> <output_dir>

Example

python pickle_sat.py '/home/scott/land.copernicus.vgt.vito.be/' '/home/scott/sat_pickles/'

Uses code by Chris Slocum

"""

import datetime as dt  # Python standard library datetime  module
import numpy as np
import netCDF4  # http://code.google.com/p/netcdf4-python/
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap, addcyclic, shiftgrid

import s2_py as s2
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, mapping

import os
import sys
import pickle


'''
NAME
    NetCDF with Python
PURPOSE
    To demonstrate how to read and write data with NetCDF files using
    a NetCDF file from the NCEP/NCAR Reanalysis.
    Plotting using Matplotlib and Basemap is also shown.
PROGRAMMER(S)
    Chris Slocum
REVISION HISTORY
    20140320 -- Initial version created and posted online
    20140722 -- Added basic error handling to ncdump
                Thanks to K.-Michael Aye for highlighting the issue
REFERENCES
    netcdf4-python -- http://code.google.com/p/netcdf4-python/
    NCEP/NCAR Reanalysis -- Kalnay et al. 1996
        http://dx.doi.org/10.1175/1520-0477(1996)077<0437:TNYRP>2.0.CO;2
'''


def ncdump(nc_fid, verb=True):
    '''
    ncdump outputs dimensions, variables and their attribute information.
    The information is similar to that of NCAR's ncdump utility.
    ncdump requires a valid instance of Dataset.

    Parameters
    ----------
    nc_fid : netCDF4.Dataset
        A netCDF4 dateset object
    verb : Boolean
        whether or not nc_attrs, nc_dims, and nc_vars are printed

    Returns
    -------
    nc_attrs : list
        A Python list of the NetCDF file global attributes
    nc_dims : list
        A Python list of the NetCDF file dimensions
    nc_vars : list
        A Python list of the NetCDF file variables
    '''
    def print_ncattr(key):
        """
        Prints the NetCDF file attributes for a given key

        Parameters
        ----------
        key : unicode
            a valid netCDF4.Dataset.variables key
        """
        try:
            print( "\t\ttype:", repr(nc_fid.variables[key].dtype))
            for ncattr in nc_fid.variables[key].ncattrs():
                print( '\t\t%s:' % ncattr,\
                      repr(nc_fid.variables[key].getncattr(ncattr)))
        except KeyError:
            print( "\t\tWARNING: %s does not contain variable attributes" % key)

    # NetCDF global attributes
    nc_attrs = nc_fid.ncattrs()
    if verb:
        print( "NetCDF Global Attributes:")
        for nc_attr in nc_attrs:
            print( '\t%s:' % nc_attr, repr(nc_fid.getncattr(nc_attr)))
    nc_dims = [dim for dim in nc_fid.dimensions]  # list of nc dimensions
    # Dimension shape information.
    if verb:
        print( "NetCDF dimension information:")
        for dim in nc_dims:
            print( "\tName:", dim) 
            print( "\t\tsize:", len(nc_fid.dimensions[dim]))
            print_ncattr(dim)
    # Variable information.
    nc_vars = [var for var in nc_fid.variables]  # list of nc variables
    if verb:
        print( "NetCDF variable information:")
        for var in nc_vars:
            if var not in nc_dims:
                print( '\tName:', var)
                print( "\t\tdimensions:", nc_fid.variables[var].dimensions)
                print( "\t\tsize:", nc_fid.variables[var].size)
                print_ncattr(var)
    return nc_attrs, nc_dims, nc_vars


def pickleSatFile(filename, fullpath, savedir):
    """Load a netcdf formatted .nc satellite file containing FAPAR data.
    Save pickle files of the FAPAR data and the latitude and longitude listings.
        
    Args:
        filename (str): The full path to the netcdf file, as string.
        param2 (str): The full path to the save directory.

    Returns:
        bool: The return value. True for success, False otherwise.

    """
    
    try:
        #Load data from file
        nc_fid = netCDF4.Dataset(fullpath, 'r')  # Dataset is the class behavior to open the file
                                 # and create an instance of the ncCDF4 class
        #nc_attrs, nc_dims, nc_vars = ncdump(nc_fid)
            # Extract data from NetCDF file
        lats = nc_fid.variables['lat'][:]  # extract/copy the data
        lons = nc_fid.variables['lon'][:]
        fapar = nc_fid.variables['FAPAR']  # shape is ???, 

        # Filter to a coarse grid containing California:
        # California is between West 125 (-125 lon) and 114 (-114 lon), and 32 N and 42 N (32 and 42 lat)
        ca_W = lons[18500]
        ca_E = lons[22250]
        ca_N = lats[12750]
        ca_S = lats[16250]
        latsCa= lats[12750:16250]
        lonsCa = lons[18500:22500]
        faparCa = fapar[12750:16250,18500:22250]
        faparFile = os.path.join(savedir, filename[6:-3] + '.pkl').replace('GLOBE', 'Calif')

        # Create pickle files
        latFile = os.path.join(savedir, filename[6:-3] + '.pkl').replace('GLOBE', 'Calif').replace('FAPAR', 'Lat')
        lonFile = os.path.join(savedir, filename[6:-3] + '.pkl').replace('GLOBE', 'Calif').replace('FAPAR', 'Lon')

        print('Pickling' + faparFile)
        with open(faparFile, 'wb+') as f:
            pickle.dump(faparCa, f)

        print('Pickling' + latFile)
        with open(latFile, 'wb+') as f:
            pickle.dump(latsCa, f)

        print('Pickling' + lonFile)
        with open(lonFile, 'wb+') as f:
            pickle.dump(lonsCa, f)
    
        return True

    except Exception as e:
        print(e)
        return False
    
print ('Number of arguments:', len(sys.argv), 'arguments.')
print ('Argument List:', str(sys.argv))
    
data_dir = sys.argv[1]
output_dir = sys.argv[2]

satfiles = {}

for dirpath, dirnames, filenames in os.walk(data_dir):
    for filename in [f for f in filenames if f.endswith(".nc")]:
        satfiles[filename] = os.path.join(dirpath, filename)
        print('Processing' + str(filename))
        pickleSatFile(filename, satfiles[filename], output_dir)