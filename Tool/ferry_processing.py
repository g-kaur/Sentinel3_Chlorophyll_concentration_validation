# BC Ferries algae concentration data is downloaded from ONC website on monthly basis which is
# segregated into multiple csv files due to excessive amount of data in one file. This python sript 
# cleans and merges relevant records into one dataframe

import pandas as pd
import numpy as np
import os
import glob

def get_args():
    parser = argparse.ArgumentParser(description="This script takes the arguments from user",formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--month",'-m', type=str,required=True,choices=['01','02','03','04','05','06','07','08','09','10','11','12'], help="Months (type a desired month number in the range [01,12]")
    parser.add_argument("--year",'-y', type=int, required=True, help="Type the desired year")
    return parser.parse_args()


def clean_daily_ferry_data(year,month):

    '''
    Parameters:
        year (str): year interested to validate
        month (str): month interested to validate
    
    Return:
        df (pandas dataframe): aggregated data into one dataframe for the whole month

    '''
    
    # Cleaning and reading the files
    df = pd.DataFrame(columns=['Date','Time','Latitude','Longitude','chl'])
    del_row = list(np.arange(50)) # The first 50 lines were containing unnecessary metadata 
    del_row.append(51)
    count = 0
    for fn in sorted(glob.glob("/spectral/gagan26/Ferry_ONC/{}/{}/*.csv".format(startyear,startmonth))):
        data = pd.read_csv(fn,skiprows = del_row) # remove unnecessary metadata
        data.drop(data.columns[[2,4,6,7,8,9,10,11,12]],axis = 1, inplace = True) # Redundant columns
        count = count +1
        
        # Renaming columns for simplicity
        data.columns = ['date_time','chl','Latitude','Longitude']

        # Split Date/Time in different columns and organizing columns
        data['Date'] = [x.split('T')[0] for x in data['date_time']]
        data['Time'] = [x.split('T')[1].split('.')[0] for x in data['date_time']]
        data = data[['Date','Time','Latitude','Longitude','chl']]
        data = data.dropna()
        date_list = data.Date.unique()
        
        for date in date_list:
            day = str(date[8:])
            date_df = data[data.Date == date]
                       
            filepath = "/spectral/gagan26/Processed_ferry_to_csv/{}/{}/{}/clean_ferry_data_{}-{}-{}.csv".format(startyear,startmonth,day,startyear,startmonth,day)
            dirpath = "../Processed_ferry_to_csv/{}/{}/{}".format(startyear,startmonth,day)
            if not os.path.isdir("../Processed_ferry_to_csv/{}/{}/{}".format(startyear,startmonth,day)):
                os.mkdir(dirpath)
            if not os.path.isfile(filepath):
                print("created file path : "+filepath)
                date_df.to_csv(filepath)
                
            else:
                print("updated : "+filepath)
                date_df.to_csv(filepath,mode = 'a',header = False)
                
    return


args = get_args()
month = args.month
year = str(args.year) 

clean_daily_ferry_data(year,month)
    
