#!/bin/bash
for i in {01..12} ; do
    wget -r --reject "index.html*" --user=$1 --password=$2 https://land.copernicus.vgt.vito.be/PDF/datapool/Vegetation/Properties/FAPAR_300m_V1/2015/$i/ &&
    python ~/w210_Wildfire/sat_process/pickle_sat.py land.copernicus.vgt.vito.be/PDF/datapool/Vegetation/Properties/FAPAR_300m_V1/2015/ ~/sat_pickles/ &&
    find land.copernicus.vgt.vito.be/ -name *.nc -type f -delete
done
