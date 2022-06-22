#start by importing nemo
import nemo
#Then we need to load in the scenarios 
from nemo import scenarios
#context is a class. We are setting up a default context  object? 
c = nemo.Context()
scenarios.re100_batteries(c)
scenarios.re100(c)
print(c.generators)

#Now we run the similation 
nemo.run(c)
print(c)

c = nemo.Context()
c.generators[0].set_capacity(10)
c.generators[1].set_capacity(50)
nemo.run(c)
print(c)

print(c.surplus_energy)

from matplotlib.pyplot import ioff
from nemo import utils 
ioff()
utils.plt.rcParams["figure.figsize"] = (12, 6)
utils.plot(c)

c.generators[1].surplus_energy()

from matplotlib.pyplot import ioff
from datetime import datetime
ioff()
utils.plt.rcParams["figure.figsize"] = (12, 6)  # 12" x 6" figure
utils.plot(c, xlim=[datetime(2010, 1, 5), datetime(2010, 1, 12)])


c = nemo.Context()
scenarios._one_ccgt(c)
for i in range(0, 40):
    c.generators[0].set_capacity(i)
    nemo.run(c)
    if c.unserved_energy() == 0:
        break
print(c.generators)

#### To run Evolve in terminal, navigate to the working directory /phdCode/NEMO and then:
#python3 evolve ..... 

#This creates an Evolve Icon and saves it on my desk top
from pyshortcuts import make_shortcut
make_shortcut("/Users/elonarey-costa/Documents/phdCode/NEMO/evolve.py", name = 'Evolve', icon= '/Users/elonarey-costa/Documents/phdCode/NEMO/myicon.ico')

#def re100_nocst(context):
 #   """100% renewables, but no CST."""
  #  re100(context)
   # newlist = [g for g in context.generators if not isinstance(g, CST)]
    #context.generators = newlist


#Practicing with a custome scenario 
#Includes: Solar, Wind, PumpedHydro, Hydro, Batteries in that merit order 
#No CST, no biofuels 


#start by importing nemo
import nemo
#Then we need to load in the scenarios 
from nemo import scenarios
#context is a class. We are setting up a default context  object? 
c = nemo.Context()
#scenarios.re100SWH(c)
scenarios.re100SWH_batteries(c)
nemo.run(c)

## Adding in generators for solar and wind into the same polygon. One polygon for each state for now. 
## Capacity is set at 30GW for each poly. 

#PV QLD in poly 4
c.generators[4].set_capacity(30)
#PV NSW in poly 30
c.generators[30].set_capacity(30)
#PV VIC in poly 37
c.generators[37].set_capacity(30)
#PV TAS in poly 41
c.generators[41].set_capacity(30)
#PV SA in poly 19
c.generators[19].set_capacity(30)

#WIND QLD in poly 4
c.generators[47].set_capacity(30)
#WIND NSW in poly 30
c.generators[73].set_capacity(30)
#WIND VIC in poly 37
c.generators[80].set_capacity(30)
#WIND TAS in poly 41
c.generators[84].set_capacity(30)
#WIND SA in poly 19
c.generators[62].set_capacity(30)




print(c.generators)

from matplotlib.pyplot import ioff
from datetime import datetime
ioff()
utils.plt.rcParams["figure.figsize"] = (12, 6)  # 12" x 6" figure
utils.plot(c, xlim=[datetime(2010, 1, 5), datetime(2010, 1, 12)])