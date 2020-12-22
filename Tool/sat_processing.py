## This python scripts cleans the chlorophyll-concentration dataset obtained from Sentinel-3
## satellite. 
# 
## The dataset was originally present in the form of complicated masked arrays.
## The following python code simplifies the format of reperesentation of the data by transforming
## the format to dataframe where each record of the dataframe contains chlorophyll concentration 
## estimations at respective geographic locations and time of capture of the record.
#
## The code logic is designed in such a way that the satellite data points which are in close 
## proximity to the specific BC ferry route, are only chosen while the rest are not taken into 
## consideration


import numpy as np
import glob
import pandas as pd
import xarray as xr
import os 
import time
import argparse

### To pass the run time variables of start and end months and year


def get_args():
    parser = argparse.ArgumentParser(description="This script takes the arguments from user",formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--month",'-m', type=str,required=True,choices=['01','02','03','04','05','06','07','08','09','10','11','12'], help="Months (type a desired month number in the range [01,12]")
    parser.add_argument("--year",'-y', type=int, required=True, help="Type the desired year")
    return parser.parse_args()

def satellite_data_cleaning(startyear,startmonth):
    
    '''

    Parameters:
        startyear (str) : year for which satellite-dataset cleaning is required
        startmonth (str) : month for which satellite-dataset cleaning is required

    Return:
        None

    '''

    count = 0
    log_file = open("Logs/logs_nc_{}/{}.txt".format(startmonth,startyear),'a')

    for folder in sorted(glob.glob("/spectral/OLCI/{}/{}/*".format(startyear,startmonth))):
        day_df = pd.DataFrame(columns = ['date','starttime','endtime','latitude','longitude','logchl'])
        count = 0
        original_data_size = 0
        log_file.write("\n")
        for file_name in sorted(glob.glob("{}/polymer/S3A*".format(folder))):
            count = count +1 
            
            ds=xr.open_dataset(file_name,mask_and_scale=False)
            dataframe = ds.to_dataframe()
            dataframe.reset_index(inplace=True) ## resets the index from matrix format to continuous values
            df = dataframe[["latitude","longitude","logchl"]]
            original_data_size = original_data_size + df.shape[0]
            fn = file_name.split("____")[1].split("_",2)[:2]
            
            ### Fetching date, start_time, end_time from the nomenclature of Sentinel satellite netcdf file  
            ### in order to find the duration of image captured by pushbroom sensors present on satellite    
            date = fn[0].split("T")[0]    
            start_time = fn[0].split("T")[1]
            end_time = str(int(fn[1].split("T")[1])-1)
            date = '{}-{}-{}'.format(date[:4],date[4:6],date[6:])
            start_time = '{}:{}:{}'.format(start_time[:2],start_time[2:4],start_time[4:])
            end_time = '{}:{}:{}'.format(end_time[:2],end_time[2:4],end_time[4:])

            
            
            log_file.write(("Processing files from {}\n".format(date)))
            log_file.write("\tReading file number {} from {}\n".format(count,date))
            log_file.write("\tNumber of data points in file {} before filtering: {}\n".format(count,df.shape[0]))
            

            df.insert(0,'date',date)
            df.insert(1,'starttime',start_time)
            df.insert(2, 'endtime',end_time)
            

            ### The values has to be compared/validated with the data collected from BC Ferries which 
            ### follows a particular path bounded by a particular range of  coordinates.
            ### Therefore, its mandatory to filter out the unnecessary coordinates present in Netcdf file 
            ### Latitude Range : 48.690000 <-> 49.000000 North 
            ### Longitude Range : -123.400000 <-> -123.100000 East

            lat_start = 48.690000
            lat_end = 49.000000
            lon_start = -123.400000
            lon_end = -123.100000
            logchl = 100 # setting threshold
            
            day0_df = df[(((df["latitude"]>=lat_start) & (df["latitude"]<=lat_end)) & ((df["longitude"]>=lon_start) & (df["longitude"]<=lon_end)) & (df["logchl"]<=logchl))]
            if day0_df.shape[0]!=0:
                log_file.write("\tNumber of data points in file {} after filtering : {}\n".format(count,day0_df.shape[0]))
                day_df = day_df.append(day0_df,ignore_index=True)
            else:
                log_file.write("\tNumber of data points in file {} after filtering : '0' as the pushbroom sensor doesnot traverses the desired geographical area\n".format(count))
            
            
            
        final_data_size = day_df.shape[0]
        log_file.write("Total data points from {} before filtering : {}\n".format(date,original_data_size))
        log_file.write("Total data points from {} after filtering : {}\n".format(date,final_data_size))
        if day_df.shape[0]!=0:

            day_df['logchl'] = np.power(10,day_df.logchl)
            day_df.columns = ['date','starttime','endtime','latitude','longitude','chl']
            day_df = day_df[(day_df['chl']<50)]
            day = str(date[8:])
            if not os.path.isdir("../Processed_nc_to_csv/{}/{}/{}".format(startyear,startmonth,day)):
                os.mkdir("../Processed_nc_to_csv/{}/{}/{}".format(startyear,startmonth,day))
            day_df.to_csv("/spectral/gagan26/Processed_nc_to_csv/{}/{}/{}/filtered_nc_{}-{}-{}.csv".format(startyear,startmonth,day,startyear,startmonth,day))
            log_file.write("Processing completed for {}-{}-{}\n".format(startyear,startmonth,day))
    log_file.close()
    return None

args = get_args()
month = args.month
year = str(args.year)

satellite_data_cleaning(year, month)





    




