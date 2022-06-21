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


from pyshortcuts import make_shortcut
make_shortcut("/Users/elonarey-costa/Documents/phdCode/NEMO/evolve.py", name = 'Evolve', icon= '/Users/elonarey-costa/Documents/phdCode/NEMO/myicon.ico')
