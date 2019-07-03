"""
sat2_S2.py

Script for converting pickle files of California satellite FAPAR data into csv, aggregated by S2 cells.

Usage

python sat2_S2.py <input_dir> <output_dir>

Example

python sat2_S2.py '/home/scott/sat_pickles/' '/home/scott/sat_aggs/' 2014

"""
import datetime as dt  # Python standard library datetime  module
import numpy as np
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

import google.cloud.bigquery
import pandas_gbq
import pandas as pd
import shapefile as shp
import descartes
from shapely.geometry import Polygon, mapping, Point

import time

# Define slightly customized aggregation functions

def myMedian(x):
    return(pd.DataFrame.median(x, skipna=True))

def myMean(x):
    return(np.ma.mean(x))

def myStd(x):
    return(np.ma.std(x))


print ('Number of arguments:', len(sys.argv), 'arguments.')
print ('Argument List:', str(sys.argv))
   
data_dir = sys.argv[1]
output_dir = sys.argv[2]
year = sys.argv[3]

startTotalTime = time.time()
print(f"Loading initial files")

picklefiles = {}

# Courtesy Yulia
ca_s2_df = gpd.read_file("/home/scott/w210_Wildfire/DataPrep/Data/Processed/CA_S2Cells/CA_S2Cells.shp")

for dirpath, dirnames, filenames in os.walk(data_dir):
    for filename in [f for f in filenames if f.endswith(".pkl")]:
        picklefiles[filename] = (os.path.join(dirpath, filename)) 

dates = []


"""
for filename, fullpath in picklefiles.items():
    if filename.startswith('Lat'):
            dateStart = filename.find(str(year))
            date = filename[dateStart:dateStart+8]
            with open(fullpath, 'rb') as f:
                lat = pickle.load(f)
            lats[date] = lat


"""

lats ={}
for filename, fullpath in picklefiles.items():
    if filename.startswith('Lat'):
            dateStart = filename.find(str(year))
            if dateStart!= -1: #file includes date of interest
                date = filename[dateStart:dateStart+8]
                with open(fullpath, 'rb') as f:
                    lat = pickle.load(f)
                lats[date] = lat

lons ={}
for filename, fullpath in picklefiles.items():
    if filename.startswith('Lon'):
        dateStart = filename.find(str(year))
        if dateStart!= -1: #file includes date of interest
            date = filename[dateStart:dateStart+8]
            with open(fullpath, 'rb') as f:
                lon = pickle.load(f)
            lons[date] = lon


fapars ={}
for filename, fullpath in picklefiles.items():
    if filename.startswith('FAPAR'):
        dateStart = filename.find(str(year))
        if dateStart!= -1: #file includes date of interest
            date = filename[dateStart:dateStart+8]
            dates.append(date)
            with open(fullpath, 'rb') as f:
                fapar = pickle.load(f)
            fapars[date] = fapar

        
# NOTE I had a typo in pickle_sat.py in creating the grid of longitudes in the initial processing.
# Further, the FAPAR file gives lat (N-S) then lon (E-W)
# so its shape is 3500 x 3750  (lat by lon)
#
#
# The FAPAR file ranges from lons[18500:22250] 
# while the lon file ranges from [18500:22500], 
# difference of 250 in the second dimension
# Filtered to a coarse crop containing California:
# California is between West 125 (-125 lon) and 114 (-114 lon), and 32 N and 42 N (32 and 42 lat)
#        ca_W = lons[18500]
#        ca_E = lons[22250]
#        ca_N = lats[12750]
#        ca_S = lats[16250]
#        latsCa= lats[12750:16250]
#        lonsCa = lons[18500:22500]
#        faparCa = fapar[12750:16250,18500:22250]

for date in sorted(dates):
    
    start = time.time()
    print(f"Working on {date}")
    latArray = lats[date]
    lonArray = lons[date]
    fapar = fapars[date]
    mask = fapars[date].mask

    latLonLookupList = []

    print(f"Building S2 cell ids")
    for idxLat, lat in enumerate(latArray):
        for idxLon, lon in enumerate(lonArray[0:-250]):  #kluge to fix a typo where the lonArray should be 3750 pixels but I kept 4000 earlier
            latlng = s2.S2LatLng_FromDegrees(lat, lon)
            cell = s2.S2CellId(latlng)
            cell9 = cell.parent(9)
            cell10 = cell.parent(10)
            cell11 = cell.parent(11)
            latLonLookupList.append((idxLat, lat, idxLon, lon, fapar[idxLat, idxLon], fapar.mask[idxLat, idxLon], 9, cell9.ToToken()))
            latLonLookupList.append((idxLat, lat, idxLon, lon, fapar[idxLat, idxLon], fapar.mask[idxLat, idxLon], 10, cell10.ToToken()))
            latLonLookupList.append((idxLat, lat, idxLon, lon, fapar[idxLat, idxLon], fapar.mask[idxLat, idxLon], 11, cell11.ToToken()))

    latLonLookupDF = pd.DataFrame(latLonLookupList, columns= ['latIdx', 'lat', 'lonIdx', 'lon', 'faparVal', 'faparMask', 'S2Level', 'S2_Cells_I'])

    latLonLookupDF['mergeKey'] = latLonLookupDF.S2_Cells_I.astype(str)
    ca_s2_df['mergeKey'] = ca_s2_df.S2_Cells_I.astype(str)
    print(f"Merging")
    merged = ca_s2_df.merge(latLonLookupDF, how='inner', on= 'mergeKey', left_index = True)
    faparMerged = merged[['mergeKey', 'latIdx', 'lat', 'lonIdx', 'lon', 'faparVal', 'faparMask']]
    print(f"Aggregating")
    agged = faparMerged.groupby('mergeKey').agg(['min', 'max', myMean, myMedian, myStd, 'size', 'count', 'nunique'])
    agged2 = agged.copy()
    agged2.columns = ['_'.join(col).strip() for col in agged2.columns.values]
    fullPath = output_dir + date + '_agg.csv'
    print(f"Saving")
    agged2.to_csv(fullPath)
    print(f"Plotting")
    agged3 = ca_s2_df.merge(agged2, on = 'mergeKey')
    fig = agged3.plot(column = 'faparVal_myMean')
    plt.savefig(output_dir + str(date) + '.png')
    end = time.time()
    print(f"Total time is {end - start}")
    
endTotalTime = time.time()

print(f"Total time is {endTotalTime - startTotalTime}")
