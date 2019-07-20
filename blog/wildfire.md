# Wildfire History

## Data Sources

There are multiple sources of California wildfire data. The most complete one is maintained by The California Department of Forestry and Fire Protection (CalFire). They maintain a [database](https://frap.fire.ca.gov/media/2525/fire18_1.zip) of wildfire perimeters starting from 1878. There are a lot of other gis-format files on their [website](https://frap.fire.ca.gov/mapping/gis-data/) (Note: Their website has been updated recently. It is possible that not all the relevant data has direct links on that page.)

Another useful source is maintained by [Geosciences and Environmental Change Science Center](https://www.usgs.gov/centers/gecsc). This database has a few advantages over CalFire: it contains the entire US wildfire history and the perimeters are available by each day of incident (instead of the total area). However, it has significant drawbacks: not all incidents are available and the data is not well organized (the format varies by year).

For our project we used the CalFire database.

## CalFire Database

The detailed description of the database is available [here](https://frap.fire.ca.gov/frap-projects/fire-perimeters/). The database available for [download]((https://frap.fire.ca.gov/media/2525/fire18_1.zip) contains wildfire perimeters from 1878 to 2018. According to metadata, 2019 data will be available in April 2020. We will discuss later how we obtained the most recent wildfire data for model validation.

The complete notebook to process this database is available on project [repo](https://github.com/jayzuniga/w210_Wildfire/blob/master/DataPrep/WildFire_S2_v2.ipynb).

The database contains information 20,508 incidents for the available timeframe. As evidenced by the image below, wildfires have not been appearing uniformally across California.

Insert history image.

## National Weather Service Fire Zones

To deal with uneven coverage of California, we decided to overlay the historical wildfire data with 108 [National Weather Service Fire Zones](https://www.weather.gov/gis/FireZones).

Insert history-fz image.

This overlay helped us split California into 3 zones:

1. 28 zones with **low** occurence of wildfires (white)
2. 51 zones with **medium** occurence of wildfires (green)
3. 26 zones with **high** occurence of wildfires (purple)

Insert history-fz-grp image.

For the details on how we grouped the zones see [this notebook](https://github.com/jayzuniga/w210_Wildfire/blob/master/DataPrep/CA_S2_Conversion_v2.ipynb).

Finally, for our analysis we selected only the last three years of data (this is discussed in the [S2 Cell Geometry post]()).

Insert history-fz-grp-16-18 image.

## Wildfires Frequency and Coverage

Our initial exploratory data analysis showed that the number and size of wildfires in California varied siginificantly on the annual basis (if we focus only on the latest 20 years). But 2017 stood out for the record number of incidents (607), while 2018 stood out for the unusually high average area of incidents (4,650 GIS Acres).

Insert wf-count-area image.

Wildfires of 2017 and 2018 stood out also for another rather unfortunate reason: the record number of incidents caused by power lines.

Insert wf-count-area-pl image.

This trend emphasized the importance of investigating the relationship between wildfires and utility infrastructure. 

## Wildfire Perimeters to S2 Cells

The conversion of wildfire perimeters to S2 Cells is covered in [this notebook](https://github.com/jayzuniga/w210_Wildfire/blob/master/DataPrep/WildFire_S2_v2.ipynb). But a few key steps in the process were:

1. Each incident (row) in the database had a `Polygon` object associated with it containing perimeter coordinates. We extracted these coordinates and converted them into an [S2 Loop object](https://github.com/google/s2geometry/blob/master/src/s2/s2loop.h).
2. Since we decided to use `S2 Cells` of 3 different sizes, each `S2 Loop` was converted into 3 types of cells using [S2 Region Coverer](https://github.com/google/s2geometry/blob/master/src/s2/s2region_coverer.h)
3. Our final dataset was on the `S2 Cell ID` + `Date` level. And it was possible that the same cell had multiple wildfires on the same date. Therefore, we aggregated the data to the `S2 Cell ID` + `Date` level to avoid duplicate keys. 
4. Finally, we merged wildfire history data to our baseline dataset by `S2 Cell ID` + `Date`. As a result, our final dataset contained 3.673 rows with wildfires (out of 11,664,728 total)
