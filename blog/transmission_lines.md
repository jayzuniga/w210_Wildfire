# Transmission Lines

The California Energy Commission's GIS [data hub](https://cecgis-caenergy.opendata.arcgis.com/) provides California energy related geospatial data, including [transmission lines](https://cecgis-caenergy.opendata.arcgis.com/datasets/california-electric-transmission-line). Unlike other data sources, this dataset required minimal processing since it was available in a user-friendly format. A few key steps in the process were:

1. Each transmission line (row) in the database had a `Linestring` object associated with it containing coordinates of closely positioned points. We extracted these coordinates and converted them into an [S2 PolyLine object](https://github.com/google/s2geometry/blob/master/src/s2/s2polyline.h).
2. Since we decided to use `S2 Cells` of 3 different sizes, each `S2 PolyLine` was converted into 3 types of cells using [S2 Region Coverer](https://github.com/google/s2geometry/blob/master/src/s2/s2region_coverer.h).
3. It was common for the same cell to contain multiple transmission lines. Also, we used three different cell levels: 9/10/11.  To address that, we used a few different aggregation methods to roll up the dataset to the `S2 Cell ID` level.  We counted the number of unique transmission lines per cell.  We also looked at the more detailed level 16 S2 Cells that contain transmission lines, then looked at what  percent of these more detailed cells existed within the parent S2 Cells.  This served as a proxy for the percentage of S2 Cells covered by transmission lines. As a result 4,188 cells contained transmission lines (out of 10,643). 
4. Finally, we merged Transmission Lines data to our baseline dataset by `S2 Cell ID`. 

The conversion of Transmission Lines Shapefile into S2 Cells is covered in [this notebook](https://github.com/jayzuniga/w210_Wildfire/blob/master/DataPrep/Transmission_Lines.ipynb).

As the image below demonstrates, there is no clear pattern between the location of Transmission Lines and Wildfire incidents. However, our model would help disentangle multiple factors and allocate the fair share of impact to the utility infrastructure.

![Transmission-Lines](https://github.com/jayzuniga/w210_Wildfire/blob/master/blog/images/tl.png?raw=true)
