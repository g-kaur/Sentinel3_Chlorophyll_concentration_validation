import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--month","-m",type=str, help = "Type two digits for the desired month such as 07 for july", required=True)
parser.add_argument("--dataset", "-d", type=str, choices = ["Ferry","Satellite"],required=True)
args = parser.parse_args()
if args.dataset == "Ferry":
    processed_dir = "Processed_ferry_to_csv"
else:
    processed_dir="Processed_nc_to_csv"
dataset_ = args.dataset
month_ = args.month
input_directory = "{}/{}/2018/{}".format(os.path.dirname(os.getcwd()),processed_dir,month_)
output_directory = "{}/Distribution_Plots/{}/{}".format(os.path.dirname(os.getcwd()),dataset_,month_)
# print(input_directory)



for fn in glob.glob(input_directory+"/*/*_filtered_*.csv"):
    # print(fn)
    df = pd.read_csv(fn)
    out_fn = fn.split("/")[-1].split(".")[0]
    save_at = output_directory +"/"+ out_fn
    
    # print(save_at)
    chl = np.array(df['chl'])
    plt.figure()
    plt.hist(chl)
    plt.axvline(chl.mean(),linestyle="dashed", color='orange')
    plt.title(out_fn)
    plt.xlabel("Chl-a mg/m3")
    plt.ylabel("Frequency")
    plt.savefig(save_at+".png")

   

