####-------------------- SET WD() -----------------------#####
import os

from nemo import polygons 
os.chdir('/Users/elonarey-costa/Documents/phdCode/NEMO')

####---------------- EVOLVE OPTIMISER -------------------#####

#### To run Evolve in terminal, navigate to the working directory /phdCode/NEMO and then:
#python3 evolve ..... 

#This creates an Evolve Icon and saves it on my desk top. The idea is to be able to double click on this icon, 
#and it opens up the evolve optimiser 
    #from pyshortcuts import make_shortcut
    #make_shortcut("/Users/elonarey-costa/Documents/phdCode/NEMO/evolve.py", name = 'Evolve', icon= '/Users/elonarey-costa/Documents/phdCode/NEMO/myicon.ico')


####-------------------- Test CASE  ---------------------#####
## Create a test scenario that only includes: Solar, Wind, PumpedHydro, Hydro, Batteries in that merit order 
## This scenario has been created in scenario.py
## I can run this scenario in this script. 

#start by importing nemo and relevant info (scenarios, generators etc)

import nemo
from nemo import scenarios
from nemo.generators import PV, Battery, PV1Axis


#Set up an empty context class
c = nemo.Context()


#Select my chosen scenario
#Just SWH
scenarios.re100SWH(c)
#SWH + battery
#scenarios.re100_batteries(c)

## Adding in generators for solar and wind into the same polygon. 
## One polygon for each state.
## Capacity is set at 30GW for all generators.
hrs = range(0,24)
b4 = Battery(4, 2000, 2000, discharge_hours=hrs, rte = 1)
c.generators = [b4] + c.generators
b30 = Battery(30, 2000, 2000, discharge_hours=hrs, rte = 1)
c.generators = [b30] + c.generators

#Currently installed Large Scale PV (data retrieved from https://pv-map.apvi.org.au/power-stations and solarfarm coordinates superimposed onto polygons in "coords.py")
#Final solar capacity sum for each polygon in /Users/elonarey-costa/OneDrive\ -\ UNSW/PhD/Data/NEM_AEMOPoly_OnlySolarfarms.xlsx 
c.generators[10].set_capacity(100)

#PV NSW in poly 30
c.generators[30].set_capacity(50)
#PV VIC in poly 37
c.generators[37].set_capacity(50)
#PV TAS in poly 41
c.generators[41].set_capacity(50)
#PV SA in poly 19
c.generators[19].set_capacity(50)

#WIND QLD in poly 4
c.generators[47].set_capacity(50)
#WIND NSW in poly 30
c.generators[73].set_capacity(50)
#WIND VIC in poly 37
c.generators[80].set_capacity(50)
#WIND TAS in poly 41
c.generators[84].set_capacity(50)
#WIND SA in poly 19
c.generators[62].set_capacity(50)


#Run the scenario through NEMO
nemo.run(c)
print(c)

print(c.surplus_energy())

#Plot scenario output
from matplotlib.pyplot import ioff
from nemo import utils 
from datetime import datetime
ioff()
utils.plt.rcParams["figure.figsize"] = (12, 6)  # 12" x 6" figure
utils.plot(c, xlim=[datetime(2010, 1, 5), datetime(2010, 1, 12)])


#c = nemo.Context()
#scenarios._one_ccgt(c)
#for i in range(0, 40):
    #c.generators[0].set_capacity(i)
    #nemo.run(c)
    #if c.unserved_energy() == 0:
        #break
#print(c.generators)



####-------------------- Test CASE  ---------------------#####
import nemo
from nemo import scenarios
from nemo.generators import Battery, PV1Axis, PV

#Set up an empty context class
c = nemo.Context()
#Chosen scenario 
scenarios.re100SWH(c)

nemo.run(c)
print(c)
print(c.generators)

