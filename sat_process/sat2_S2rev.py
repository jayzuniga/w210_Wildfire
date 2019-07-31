"""
sat2_S2.py

Script for converting pickle files of California satellite FAPAR data into csv, aggregated by S2 cells.

Usage

python sat2_S2.py <input_dir> <output_dir>

Example

python sat2_S2.py '/home/scott/sat_pickles/' '/home/scott/sat_aggs/' 2016

"""
import datetime as dt  # Python standard library datetime  module
import numpy as np
import matplotlib.pyplot as plt
#from mpl_toolkits.basemap import Basemap, addcyclic, shiftgrid

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

# Define  customized aggregation functions
# https://stackoverflow.com/questions/10951341/pandas-dataframe-aggregate-function-using-multiple-columns

def myMean(group):
    fV = group['faparVal']
    m = group['faparMask']
    y = np.ma.MaskedArray(data=fV, mask=m)
    return np.ma.mean(y)

def myMedian(group):
    fV = group['faparVal']
    m = group['faparMask']
    try:
        outVal = np.median(fV.loc[m==False])  # np.ma.median doesn't work correctly
    except:
        return np.ma.masked
    return outVal
    
def myStd(group):
    fV = group['faparVal']
    m = group['faparMask']
    try:
        outVal = np.std(fV.loc[m==False])   # np.ma.std doesn't work correctly
    except:
        outVal = np.ma.masked
    
    if np.isnan(outVal):
        outVal = np.ma.masked
    return outVal

def myMin(group):
    fV = group['faparVal']
    m = group['faparMask']
    try:
        outVal = np.min(fV.loc[m==False])   # np.ma.std doesn't work correctly
    except:
        outVal = np.ma.masked
    
    if np.isnan(outVal):
        outVal = np.ma.masked
    return outVal

def myMax(group):
    fV = group['faparVal']
    m = group['faparMask']
    try:
        outVal = np.max(fV.loc[m==False])   # np.ma.std doesn't work correctly
    except:
        outVal = np.ma.masked
    
    if np.isnan(outVal):
        outVal = np.ma.masked
    return outVal




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

for date in sorted(dates, reverse = True):
    
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

    # Get S2 cells df for merging
    latLonLookupDF = pd.DataFrame(latLonLookupList, columns= ['latIdx', 'lat', 'lonIdx', 'lon', 'faparVal', 'faparMask', 'S2Level', 'S2_Cells_I'])
    latLonLookupDF['mergeKey'] = latLonLookupDF.S2_Cells_I.astype(str)
    ca_s2_df['mergeKey'] = ca_s2_df.S2_Cells_I.astype(str)
    
    # Perform merge to desired S2 cell levels
    merged = ca_s2_df.merge(latLonLookupDF, how='inner', on= 'mergeKey', left_index = True)

    # Subset to desired columns
    faparMerged = merged[['mergeKey', 'lat', 'lon', 'faparVal', 'faparMask']]
    # Perform aggregations
    grouped = faparMerged.groupby('mergeKey')
    # Aggregate for standard functions
    groupedOut = grouped.agg(['min', 'max', 'mean', 'median', 'std', 'size', 'count', 'nunique'])

    # Apply the custom aggregation functions that depend on multiple columns (due to masking)
    groupedOut2 = pd.DataFrame()
    groupedOut2['mergeKey'] = grouped.indices
    groupedOut2['faparVal_myMean'] = grouped.apply(myMean)
    groupedOut2['faparVal_myMedian'] = grouped.apply(myMedian)
    groupedOut2['faparVal_myStd'] = grouped.apply(myStd)
    groupedOut2['faparVal_min'] = grouped.apply(myMin)
    groupedOut2['faparVal_max'] = grouped.apply(myMax)
    
    #TODO use the custom min and max
    # Get  the standard agregations for columns that also have custom aggregations
    aggedFapar = faparMerged[['faparVal', 'mergeKey']].groupby('mergeKey').agg(['size', 'count', 'nunique'])
    agged2 = groupedOut.copy()
    # Merge the standard columns for masked and unmasked column types
    agged2 = agged2.merge(aggedFapar, on = 'mergeKey')
    # Flatten the index
    agged2.columns = ['_'.join(col).strip() for col in agged2.columns.values]
    # Merge with the custom columns
    agged3 = agged2.merge(groupedOut2, on='mergeKey')
    dateFormatted = date[0:4] + '-' + date[4:6] + '-' + date[6:]
    agged3['date'] = dateFormatted
    
    #Save it
    fullPath = output_dir + date + '_agg.csv'
    print(f"Saving")
    agged3.to_csv(fullPath)
    
    # Make a plot of the mean
    print(f"Plotting")
    plotDf = ca_s2_df.merge(agged3, on = 'mergeKey')
    plotDf['faparVal_myMean'] = plotDf['faparVal_myMean'].astype('float64')
    ax = plotDf.plot(column = 'faparVal_myMean', label = 'Mean FAPAR', legend = True)
    plt.title('Mean FAPAR')
    plt.savefig(output_dir + str(date) + '.png')
    end = time.time()
    print(f"Total time is {end - start}")
    
endTotalTime = time.time()

print(f"Total time is {endTotalTime - startTotalTime}")
