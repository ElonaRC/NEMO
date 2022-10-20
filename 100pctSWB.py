"""
First attempt at 100% solar, wind, battery system. 

This script will:
- Read and clean NEM demand and fuel type data
- Collapse 5min data into hourly averages 
- Make a test case data set using only data for September 2021
- Set up all the variables for optimisation 
- present the equation needed to be solved to find the optimal amount of added 
solar, wind, battery to meet the current largest energy gap between demand/generation


"""
# ==============================================================================
# ======System Set up===========================================================

import os
import sys

#making sure working directory is set to the top folder of the repository
if not os.getcwd().endswith("Project1"):
    if "Project1" in os.getcwd():
        p1, p2, _ = os.getcwd().partition("Project1")
        os.chdir(p1+p2)
    else:
        raise OSError( 
            "Can't find working directory with Project1 in it."
        )
#add place to look for custom packages
sys.path.append(os.getcwd())

# ==============================================================================
# ======Import Packages=========================================================

import numpy as np  #math arrays
import pandas as pd #dataframes
import ipdb
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================================================
# =====Main script==============================================================

def main():
    #Load Data
    NEM_Demand = pd.read_csv("./data/NEM_DemandGen_2017_2021_5min.csv")
    NEM_Fuel = pd.read_csv("./data/NEM_FuelType_2017_2021_5min.csv")

    #Convert df into hourly time steps and average all variables
    NEM_Demand_hourly = hourlyprocessdf(NEM_Demand)
    NEM_Fuel_hourly = hourlyprocessdf(NEM_Fuel)

    #Extract test df for the month of September 2021
    september_dem = timeslice(NEM_Demand_hourly)
    september_dem.reset_index("Time", inplace=True)
    september_gen = timeslice(NEM_Fuel_hourly)
    september_gen.reset_index("Time", inplace=True)


    #New DataFrame 
    df=pd.DataFrame()
    df['time'] = september_dem.loc[:,'Time'].copy()
    df['demand'] = september_dem.loc[:,'NEM_TotalDemand'].copy()
    df['solar'] = september_gen.loc[:,'NEM_Solar_Total'].copy()
    df['wind'] = september_gen.loc[:,'NEM_Wind_Total'].copy()
    df['battery'] = september_gen.loc[:,'NEM_Battery_Total'].copy()
    
    #Solar & Wind Capacity variables 
    maxSolarCapacity = np.max(df.solar) ##Max amount of solar power produced in one hour -> current installed system solar capacity 
    df['solarCapacity'] = df.solar/maxSolarCapacity #Solar generation data converted to hourly solar capacity weighted against the maximum solar output = 100% capacity 
    maxWindCapacity = np.max(df.wind) #Max amount of wind power produced in one hour -> current installed system wind capacity
    df['windCapacity'] = df.wind/maxWindCapacity #Wind generation data converted to hourly wind capacity weighted against the maximum wind output = 100% capacity 
    maxDemand = np.max(df.demand) #27683.85 GW
    df['energyGap'] = df.demand - df.solar - df.wind - df.battery
    maxEnergyGap = np.max(df.energyGap) #26222.43 GW


    # ==============================================================================
    # =====Conceptualisation========================================================


    """
    Solar and wind capacity variables tell us how much power is generated at a 
    given time based on the max amount of solar or wind generated in the system. 

    Currently, there is a maximum renewable energy gap of 26MW, of which needs 
    to be added so that the system can reach 100% RE at any time. 

    The maximum energy gap occurs at an hour where solar capacity = 0.626019%, 
    wind capacity = 25.452019% & battery use = 48.5GW (6pm) which means that to add 
    26MW into the system, we probably need more MW than we think to close the gap. 

    #df.query('energyGap == @maxEnergyGap')

    Need to solve for x, y and battery at the lowest cost combination (optimisation problem)
    Battery at max energy gap can be the maximum drawn from battery possible. 
    Don't need to use current battery time series 

    (Current max battery discharge is 78.8)

    sCap * x + wCap *y + battery = maxEnergyGap

    df.query('energyGap == @maxEnergyGap')['solarCapacity'] * x + 
    df.query('energyGap == @maxEnergyGap')['windCapacity'] * y +
    df.query('energyGap == @maxEnergyGap')['battery'] =  maxEnergyGap

    Using september 2021 data:
    0.00626019 * x + 0.0025452019 * y + b = 26222.43

    """

    # ==============================================================================
    # =====Optimise Solar, Wind, Battery============================================

    #Insert cost data from GenCost2021 report 

    #insert optimsation code here

    #Scenario1 - Arbitrary numbers for now (added generation needed above current levels)
    addedSolarS1 = 20000 #GW
    addedWindS1 = 10000 #GW
    addedBatteryS1 = 5000 #GW
    batteryMax = 100000


# ==============================================================================
# =====calculating excess generation under Scenario 1===========================
    
    df['excessS1'] = ""
    df['storageS1'] = ""
    df['unservedDemandS1'] = ""
    df['energyGapS1'] = ""

    df[['excessS1','storageS1','unservedDemandS1','energyGapS1']] = df[['excessS1','storageS1','unservedDemandS1','energyGapS1']].apply(pd.to_numeric)

    #solar and wind profiles if we were to add an extra 20MW and 5GW respectively into the system
    df['solarS1'] = np.where(df['solar'] == 0, 0, df.solar + df.solarCapacity*addedSolarS1) #To account for night time = no solar
    df['windS1'] = df.wind + df.windCapacity*addedWindS1
    
    #Assume storage is full at the first instance. 
    df.loc[0, 'storageS1'] = batteryMax

    # for i in range(1, len(df.demand)):
        # df.loc[i, 'energyGapS1'] = df.demand[i] - df.solarS1[i] - df.windS1[i]

        # if df.iloc[i].loc['energyGapS1'] > 0:
        #     df.loc[i,'storageS1'] = df.storageS1[i-1] - df.energyGapS1[i]

        #     if df.loc[i,'storageS1'] < 0:
        #         df.loc[i, 'unservedDemandS1'] = df.storageS1[i] #demand was not met that day 
        #         df.loc[i, 'storageS1'] = 0

        #     elif df.loc[i,'storageS1'] >= 0:
        #         df.loc[i,'storageS1'] = df.storageS1[i]
        #     else:
        #         print("9999") 

            
        # elif df.iloc[i].loc['energyGapS1'] < 0: 
        #     df.loc[i, 'excessS1'] = df.energyGapS1[i]*(-1)
        # else:
        #     print("22222")

    for i in range(1, len(df.demand)):
        df.loc[i, 'energyGapS1'] = df.demand[i] - df.solarS1[i] - df.windS1[i]

        if df.iloc[i].loc['energyGapS1'] > 0:
            df.loc[i,'storageS1'] = df.storageS1[i-1] - df.energyGapS1[i]



        elif df.iloc[i].loc['energyGapS1'] < 0: 
            df.loc[i, 'excessS1'] = -df.energyGapS1[i]
        else:
            print("9999")
        










        df.storageS1[i] = np.where(df.energyGapS1[i] > 0, df.storageS1[i-1] - df.energyGapS1[i], "lol")

        if df.energyGapS1[i] > 0: #demand > supply

            df.storageS1[i] = df.storageS1[i-1] - df.energyGapS1[i]

            if df.storageS1[i] < 0:
                df.unservedDemandS1[i] == df.storageS1[i] #demand was not met that day 
                df.storage[i] = 0



# ==============================================================================
# =====Functions==============================================================

def hourlyprocessdf(df):
    df["Time"] = pd.to_datetime(df["Time"], format="%d/%m/%y %H:%M")
    df.set_index("Time", inplace = True)
    df_hourly = df.resample("H").mean()
    return(df_hourly)

def timeslice(df):
    return df['2021-09-01':'2021-09-30']

# ==============================================================================
if __name__ == '__main__':
    main()