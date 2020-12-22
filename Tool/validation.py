## This python script fetches the cleaned BC ferry-dataset (refer Ferry_processing.py) 
## and cleaned Sentinel3 satellite-dataset (refer Sat_processing.py) and compares/validates 
## the chlorophyll concentration estimates from the two datasets. 

## To validate the dataset, it is first required to filter the data points for optimal solution

## Ferry data points are filtered such that the data points which are recorded within the time-window
## of the satellite data points, are only considered

## Satellite data points are filtered according to the geographical location of the filtered ferry 
## data points such that the area covered by the filtered satellite data points can overlap with
## the geographical area covered by the previously filtered ferry data points

## This python script also involves code to visualize the implementation of the algorithm geographically 

import pandas as pd
import numpy as np
import math
import os
import datetime
from geopy import distance
import matplotlib.pyplot as plt
import folium
from folium import plugins
from folium.plugins import HeatMap
from folium.plugins import BoatMarker
pd.options.mode.chained_assignment = None

def get_args():

    parser = argparse.ArgumentParser(description="This script takes the arguments from user",formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--month",'-m', type=str,required=True,choices=['01','02','03','04','05','06','07','08','09','10','11','12'], help="Months (type a desired month number in the range [01,12]")
    parser.add_argument("--year",'-y', type=int, required=True, help="Type the desired year")
    parser.add_argument("radius_factor", 'rf',typr=int, required=True, choices=[1,2,3,4], help="value of parameter to increase or decrease radius")
    return parser.parse_args()


def write_log(content):
    '''
    Parameters
        content (str) : Content to log

    Return 
        None

    '''
    fpath = "Logs/ExecutionLogs.txt"
    file=open(fpath,'a')
    file.write(content+"\n")
    file.close()
    print(content)
    return None


def read_and_filter(satellite,ferry,radius):
    '''
    Parameters 
        satellite (str): csv file path of cleaned satellite data of the respective date
        ferry (str) : csv file path for cleaned ferry data of the respective date
        radius (int) : parameter to increase or decrease radius around the ferry location
    
    Returns
        sat_filtered : filtered satellite dataframe
        ferry_filtered : filtered ferry dataframe
        mid-lat (int) : mean latitude value
        mid-lon (int) : mean longitude value
        radius_range (int) : range of the radius around imaginary circle 
    
    '''
    sat_df = pd.read_csv(satellite)
    ferry_df = pd.read_csv(ferry)
    sat_df = sat_df.drop(['Unnamed: 0'],axis =1)
    ferry_df = ferry_df.drop(['Unnamed: 0'],axis =1)

    # Filtering relevant ferry points in the 3 minute window in which push broom sensor scanned the area
    start_time = pd.unique(pd.Series(sat_df.starttime))
    end_time = pd.unique(pd.Series(sat_df.endtime))
    mask = (ferry_df['Time'] >= start_time[0]) &(ferry_df['Time'] <= end_time[0])
    ferry_filtered = ferry_df.loc[mask]
    ferry_filtered['chl'] = np.float64((ferry_filtered['chl']))
    ferry_filtered = ferry_filtered.reset_index(drop = True)
    # chl_column = ferry_filtered["chl"]
    # max_ferry_chla = chl_column.max()
    if len(ferry_filtered)==0:
        return None,None,0,0,0
    first_lat = ferry_filtered.loc[0,'Latitude']
    first_lon = ferry_filtered.loc[0,'Longitude']
    last_lat = ferry_filtered.loc[len(ferry_filtered)-1,'Latitude']
    last_lon = ferry_filtered.loc[len(ferry_filtered)-1,'Longitude']
    mid_lat = np.median(ferry_filtered['Latitude'].astype('float'))
    mid_lon = np.median(ferry_filtered['Longitude'].astype('float'))
    distance_traversed = distance.distance((first_lat, first_lon),(last_lat, last_lon)).km
    
    sat_df['sat_kms'] = sat_df.apply((lambda row: distance.distance((row['latitude'], row['longitude']),
            (mid_lat,mid_lon)).km),axis=1)
    sat_df = sat_df.sort_values(by = ['sat_kms'])
    if distance_traversed < 1.0:
        write_log("Ferry is standing still at one of the terminal and has not moved")
        distance_traversed = 2.0
    radius_range = radius*(distance_traversed/2.0)
    mask_kms = sat_df['sat_kms']<=radius*(distance_traversed/2.0)
    sat_filtered = sat_df.loc[mask_kms].reset_index(drop = True)

    # mask_chl = sat_filtered['chl']<= max_ferry_chla
    # sat_filtered = sat_filtered.loc[mask_chl].reset_index(drop=True)
    # sat_filtered.drop_duplicates(inplace = True)
    # if len(sat_filtered)==0:
        # return None, None,0,0,0
    return sat_filtered,ferry_filtered,mid_lat,mid_lon,radius_range

def undersampling(sat_filtered,ferry_filtered):
    '''
    
    Parameters :
        sat_filtered : filtered satellite dataframe
        ferry_filtered : filtered ferry dataframe
    
    Return :
        avg_corr (int) : average correlation between the selected ferry data points and satellite data points
    
    '''
    avg_corr_ = []
    # print(len(sat_filtered),len(ferry_filtered))
    for num in range(1,11):
        
        ferry_sample = ferry_filtered.sample(len(sat_filtered),random_state=num)
    #     write_log(ferry_sample.info())
    #     write_log("random_state {}".format(num))
        X = (sat_filtered['chl'])
        Y = (ferry_sample['chl'])
        corr = X.corr(Y)
        
        if not math.isnan(corr) :
            avg_corr_.append(corr)
            
    return avg_corr_

def oversampling(sat_filtered,ferry_filtered):
    '''

    Parameters :
        sat_filtered : filtered satellite dataframe
        ferry_filtered : filtered ferry dataframe
    
    Return :
        avg_corr (float) : average correlation between the selected ferry data points and satellite data points
    
    '''

    avg_corr = []
    for num in range(200):
        # print(len(sat_filtered),num)
        sat_sample = sat_filtered.sample(len(ferry_filtered),random_state=num,replace=True)
    #     write_log("random_state {}".format(num))
        print(sat_sample.shape)
        X = (sat_sample['chl'])
        Y = (ferry_filtered['chl'])
        corr = X.corr(Y)
        avg_corr.append(corr)
        
    return avg_corr,sat_sample


def heatmap(sat_filtered,ferry_filtered,lat,lon,corr,map_ferry,boat_color):

    '''

    Parameters :
        sat_filtered : filtered satellite dataframe
        ferry_filtered : filtered ferry dataframe
        lat (float) : latitude value
        lon (float) : longitude value
        corr (float) : average correlation between the selected ferry data points and satellite data points
        map_ferry (object) : contains information for visualization of the data points on the map
        boat_color (list of strings) : colors for the boat markers 
    
    Return:
        map_ferry (object) : representation of the data points on the map


    '''

    
    ## Plotting heat map using folium
    if map_ferry == None:
       map_ferry = folium.Map(location=[lat,lon],zoom_start=10)
    
    if corr <= 0:
        color = 'red'
        ps = 'No correlation at all'
    elif corr > 0 and corr <= 0.3:
        color = 'coral'
        ps = 'Very weak correlation'
    elif corr > 0.3 and corr <= 0.5:
        color = 'gold'
        ps = 'Weak correlation'
    elif corr > 0.5 and corr <= 0.7:
        color = 'yellow'
        ps = 'Strong correlation'
    else:
        color = 'greenyellow'
        ps = 'Very strong correlation'
    BoatMarker(
        location=[lat,lon],
        popup = (sat_filtered.iloc[0]['date'],ps,"Correlation = {}".format(corr)),
        heading=40,
        wind_heading=46,
        wind_speed=25,
        color=boat_color).add_to(map_ferry)
    
    for lat,lon in zip(sat_filtered['latitude'],sat_filtered['longitude']):
        folium.CircleMarker([lat, lon],
                                radius=6,
                                color='b',
                                fill=True,
                                fill_opacity=0.7,
                                fill_color=color,
                               ).add_to(map_ferry)
    
    return map_ferry


map_ferry = None
def execute(year,month,boat_color,map_ferry,radius_factor):
    '''
    Parameters:
        year (str) : desired year for validating the data
        month (str) : desired month for validating the data
        boat_color (list of strings) : colors for the boat markers
        map_ferry (object) : contains information for visualization of the data points on the map
        radius_factor (int) : parameter to increase or decrease radius around the ferry location

    Returns:
        map_ferry (object) : contains information for visualization of the data points on the map
        results_df (dataframe) :records of the results obtained for correlation for different instances

    '''

    results_df = pd.DataFrame(columns=['Date','Latitude','Longitude','Radius (Kms)','Correlation','Remarks'])
    for i in range(1,32):
        write_log("********************************\n")
                
        if i <10:
            cdate = "0"+str(i)
        else:
            cdate = str(i)
        current_date = year+"-"+month+"-"+cdate
        write_log("Processing data from {}/{}/{}".format(year,month,cdate))

        if not os.path.exists("../Processed_nc_to_csv/{}/{}/{}/filtered_nc_{}-{}-{}.csv".format(year,month,cdate,year,month,cdate)):
            remarks = "The satellite did not pass over the ferry route between Vancouver and Victoria on {}-{}-{}".format(cdate,month,year)
            write_log(remarks)
            results_df=results_df.append({"Date":current_date,"Latitude":"-","Longitude":"-",'Radius (Kms)':"-","Correlation":"-","Remarks":remarks},ignore_index=True)
            continue

        if not os.path.exists("../Processed_ferry_to_csv/{}/{}/{}/clean_ferry_data_{}-{}-{}.csv".format(year,month,cdate,year,month,cdate)):
            remarks = "Ferry data from {}}/{}/{} is not available".format(year,month,cdate)
            write_log(remarks)
            results_df=results_df.append({"Date":current_date,"Latitude":"-","Longitude":"-",'Radius (Kms)':"-","Correlation":"-","Remarks":remarks},ignore_index=True)
            continue

        s,f,lat,lon,radiusrange = read_and_filter("../Processed_nc_to_csv/{}/{}/{}/filtered_nc_{}-{}-{}.csv".format(year,month,cdate,year,month,cdate),
                        "../Processed_ferry_to_csv/{}/{}/{}/clean_ferry_data_{}-{}-{}.csv".format(year,month,cdate,year,month,cdate),radius_factor)
        if s is None:
            remarks = "The ferry is not operating in the satellite pass duration or there are not enough chl-a values in satellite data which are less than maximum ferry chl-a"
            write_log(remarks)
            results_df=results_df.append({"Date":current_date,"Latitude":lat,"Longitude":lon,'Radius (Kms)':"-","Correlation":"-","Remarks":remarks},ignore_index=True)
            continue
        elif len(s) == 0:
            remarks = "The satellite pass is taking the capture from the ferry route between Vancouver and Victoria but the position of ferry in that duration does not overlap with the area covered in satellite pass"
            write_log(remarks)
            results_df=results_df.append({"Date":current_date,"Latitude":lat,"Longitude":lon,'Radius (Kms)':"-","Correlation":"-","Remarks":remarks},ignore_index=True)
            continue
        s.to_csv("../Processed_nc_to_csv/{}/{}/{}/sat_filtered_{}-{}-{}.csv".format(year,month,cdate,year,month,cdate))
        # f.to_csv("../Processed_ferry_to_csv/2018/{}/{}/ferry_filtered_2018-{}-{}.csv".format(month,cdate,month,cdate))
        o_c,sat_oversample = oversampling(s,f)
        s.to_csv("../Processed_nc_to_csv/{}/{}/{}/sat_oversampled_{}-{}-{}.csv".format(year,month,cdate,year,month,cdate))

        # o_c = undersampling(s,f)
        #write_log(np.mean(o_c),np.std(o_c))
        corr = np.mean(o_c)
        results_df=results_df.append({"Date":current_date,"Latitude":lat,"Longitude":lon,'Radius (Kms)':radiusrange,"Correlation":corr,"Remarks":"-"},ignore_index=True)

        map_ferry = heatmap(s,f,lat,lon,corr,map_ferry,boat_color)
    return map_ferry,results_df
    


args = get_args()
month = args.month
year = str(args.year)
radius_factor = args.radius_factor

write_log(" Experiment {} - Increasing the area of radius by a factor of {} to consider more satellite data for validation".format(str(radius_factor),str(radius_factor)))

write_log("---------------- Processing data from {}/{} -------------".format(month,year))
map_ferry,results = execute(year,month,'blue',map_ferry,radius_factor)
results.to_csv("Results_exp_{}/{}_{}.csv".format(month, year, str(radius_factor)))


map_ferry.save('map_exp{}.html'.format(str(radius_factor)))

