####-------------------- SET WD() -----------------------#####
import os
os.chdir('/Users/elonarey-costa/Documents/phdCode/NEMO')

####---------------- EVOLVE OPTIMISER -------------------#####

''' To run Evolve in terminal, navigate to the working directory /phdCode/NEMO and then:
#python3 evolve ..... 

This creates an Evolve Icon and saves it on my desk top. The idea is to be able to double click on this icon, 
and it opens up the evolve optimiser 
    #from pyshortcuts import make_shortcut
    #make_shortcut("/Users/elonarey-costa/Documents/phdCode/NEMO/evolve.py", name = 'Evolve', icon= '/Users/elonarey-costa/Documents/phdCode/NEMO/myicon.ico')
Currently works but just spits out the default. 
'''

####-------------------- Test CASE  ---------------------#####
## Create a test scenario that only includes: Solar, Wind, PumpedHydro, Hydro, Batteries in that merit order 
## This scenario has been created in scenario.py
## I can run this scenario in this script. 

#start by importing nemo and relevant info (scenarios, generators etc that I want to use )

import nemo
from nemo import scenarios
from nemo.generators import PV, Battery, PV1Axis

#Always set up an empty context class
c = nemo.Context()

#Select my chosen scenario
#Just SWH
scenarios.re100SWH_batteries(c)
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
utils.plot(c)
utils.plot(c, xlim=[datetime(2018, 1, 5), datetime(2018, 1, 12)])


#c = nemo.Context()
#scenarios._one_ccgt(c)
#for i in range(0, 40):
    #c.generators[0].set_capacity(i)
    #nemo.run(c)
    #if c.unserved_energy() == 0:
        #break
#print(c.generators)



####-------------------- Run re100SWH and map the outcome for one iteration ---------------------#####
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

#Plot scenario output
from matplotlib.pyplot import ioff
from nemo import utils 
from datetime import datetime
ioff()
utils.plt.rcParams["figure.figsize"] = (12, 6)  # 12" x 6" figure
utils.plot(c, xlim=[datetime(2010, 1, 5), datetime(2010, 1, 12)])

####-------------------- Commands ---------------------#####
'''
EVOLVE Optimiser 
In terminal widow -s = scenario -g = generators

python3 evolve -s re100SWH -g 3 #Runs the scenario 
python3 evolve -s re100SWH -g 3 > erc.txt #> erc.txt saves output. 

'''


'''
SAVING OUTPUT FROM EVOLVE 

script filename
evolve command 


cat > re100SWHrun1  #saves output from evolve into a file called re100SWHrun1
python3 summary < re100SWHrun1 #gives summary output in a nice table 

Table like below:
tech	          GW	share	  TWh	share	CF
          PV	36.0	0.480	111.9	0.575	0.355
        wind	32.8	0.438	 68.9	0.354	0.240
       hydro	 3.9	0.052	  9.6	0.049	0.278
         PSH	 2.2	0.030	  4.3	0.022	0.221
     surplus     N/A	  N/A	 58.7	0.287
'''


'''
REPLAY RESULTS

python3 replay -f results.json  #gives us the saved results of the last optimisation run so I can go back to it. 
python3 replay -f results.json -v   #gives us more saved results broken down more. 

Replay GUI box: (after running evolve first)
/usr/local/bin/python3.9 replay #gives us the replay gui box to print the results in a graph. 
'''


'''
GIT SYNC FROM BEN MASTER UPSTREAM 
go to git desktop. Leave the current branch as master which is mine branch to work in. 
Click choose a branch to merge into master. 
In terminal:

git pull upstream
git merge upstream/master
'''



#create dataframe that saves the spilled energy for each time step for each generator
#Do the same for spilled energy at each generator. 
import nemo
from nemo import scenarios 
import numpy as np 
import pandas as pd
c = nemo.Context()
scenarios.re100SWH(c)
nemo.run(c)

#create an array of all the generators and their power output for each time step. 
len(c.generators)
power = np.zeros((137, 8760))
for i, g in enumerate(c.generators):
    power[i] = list(g.series_power.values())
np.savetxt("powerTest.csv", power, delimiter=",")

#create an array of all the spilled energy for each time step. 
spills = np.zeros((137, 8760))
for i, g in enumerate(c.generators):
    spills[i] = list(g.series_spilled.values())
np.savetxt("spillsTest.csv", spills, delimiter=",")



print(c.generators[0])
print(c.generators[0].series_spilled) #print time series of energy spilled for generator 0 (PV in this case)


#All the different things that you can extract from evolve 
c.__dict__.keys()

#Total unserved energy 
c.unserved_energy()

#panda dataframe that lists all the unserved events and their time point.
#does not yet include a full time series with zeros for no unserved and filled with unserved 
print(c.unserved)

#To consider: one battery per state and make them discharge over night as peakers 

#script -c re100SWH50runs 
#script -c "/usr/local/bin/python3.9 -m scoop evolve -s re100SWH_batteries -g50" re100SWH50runs 

#/usr/local/bin/python3.9 summary < re100SWH50runs
#/usr/local/bin/python3.9 replay -f results.json  
#/usr/local/bin/python3.9 replay --plot --spills  

#/usr/local/bin/python3.9 replay -v -f results.json | /usr/local/bin/python3.9 summary
#piped replay output into summary to get 
#control d to close
#shell scripts 
 


import nemo
c = nemo.Context()
scenarios.re100SWH(c)
#scenarios.re100SWH_batteries(c)
nemo.run(c, "01/01/2020", "01/02/2020")
print(c)

#Old code for setting new generators 
#result.append(gentype(poly, capacity, cfg, poly - 1, 
#                                build_limit = capacity/1000, 
#                                label = f'polygon {poly} Existing Wind'))