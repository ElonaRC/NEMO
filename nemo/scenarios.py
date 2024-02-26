# Copyright (C) 2012, 2013, 2014, 2022 Ben Elliston
# Copyright (C) 2014, 2015, 2016 The University of New South Wales
# Copyright (C) 2016 IT Power (Australia)
# Copyright (C) 2023 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Supply side scenarios."""

from nemo import configfile, regions
from nemo.generators import (CCGT, CCGT_CCS, CST, OCGT, Biofuel, Black_Coal,
                             CentralReceiver, Coal_CCS, DemandResponse, Hydro,
                             PumpedHydroPump, PumpedHydroTurbine, PV1Axis, Behind_Meter_PV,
                             Wind, WindOffshore, Battery, BatteryLoad)
from nemo.polygons import (WILDCARD, cst_limit, offshore_wind_limit, pv_limit, rooftop_limit,
                           wind_limit)
from nemo.storage import (PumpedHydroStorage, BatteryStorage)
from nemo.types import UnreachableError

RUNFAST = 0  # changes everypoly from 44 to 10

class DualSetter:
    def __init__(self, setter1, setter2):
        self.setters = [setter1[0], setter2[0]]

    def set_capacity(self, cap):
        for setter in self.setters:
            setter(cap)

def _demand_response():
    """Return a list of DR 'generators'."""
    dr1 = DemandResponse(WILDCARD, 1000, 100, "DR100")
    dr2 = DemandResponse(WILDCARD, 1000, 500, "DR500")
    dr3 = DemandResponse(WILDCARD, 1000, 1000, "DR1000")
    return [dr1, dr2, dr3]


def _pumped_hydro():
    """Return a list of existing pumped hydro generators."""
    # QLD: Wivenhoe (http://www.csenergy.com.au/content-%28168%29-wivenhoe.htm)
    psh17stg = PumpedHydroStorage(5000, label='poly 17 pumped storage')
    psh17pump = PumpedHydroPump(17, 500, psh17stg, label='poly 17 PSH pump')
    psh17turb = PumpedHydroTurbine(17, 500, psh17stg,
                                   label='poly 17 PSH generator')

    # NSW: Tumut 3, Bendeela (2x80 MW) and Kangaroo Valley (2x40 MW)
    # Tumut 3 is 600 MW pumping and 1800 MW generating
    psh36stg = PumpedHydroStorage(15000, label='poly 36 pumped storage')
    psh36pump = PumpedHydroPump(36, 1740, psh36stg,
                                label='poly 36 PSH pump') ##Paper 1 has cap at 1740. Paper 2 had it as 600 + 160 + 80
    psh36turb = PumpedHydroTurbine(36, 1740, psh36stg,
                                   label='poly 36 PSH generator') ##Paper 1 has cap at 1740 Paper 2 had it as 1800 + 160 + 80

    return [psh17pump, psh36pump, psh17turb, psh36turb]


def _hydro():
    """Return a list of existing hydroelectric generators."""
    hydro24 = Hydro(24, 42.5, label='poly 24 hydro')
    hydro31 = Hydro(31, 43, label='poly 31 hydro')
    hydro35 = Hydro(35, 71, label='poly 35 hydro')
    hydro36 = Hydro(36, 2513.9, label='poly 36 hydro')
    hydro38 = Hydro(38, 450, label='poly 38 hydro')
    hydro39 = Hydro(39, 13.8, label='poly 39 hydro')
    hydro40 = Hydro(40, 586.6, label='poly 40 hydro')
    hydro41 = Hydro(41, 280, label='poly 41 hydro')
    hydro42 = Hydro(42, 590.4, label='poly 42 hydro')
    hydro43 = Hydro(43, 462.5, label='poly 43 hydro')

    return [hydro24, hydro31, hydro35, hydro36, hydro38, hydro39,
            hydro40, hydro41, hydro42, hydro43]


def replacement(context):
    """Replace the current NEM fleet, more or less."""
    context.generators = \
        [Black_Coal(WILDCARD, 0)] + _pumped_hydro() + _hydro() + \
        [OCGT(WILDCARD, 0)]


def _one_ccgt(context):
    """One CCGT only."""
    context.generators = [CCGT(WILDCARD, 0)]


def ccgt(context):
    """All gas scenario."""
    context.generators = [CCGT(WILDCARD, 0)] + _pumped_hydro() + \
        _hydro() + [OCGT(WILDCARD, 0)]


def ccgt_ccs(context):
    """CCGT CCS scenario."""
    # pylint: disable=redefined-outer-name
    ccgt = CCGT_CCS(WILDCARD, 0)
    ocgt = OCGT(WILDCARD, 0)
    context.generators = [ccgt] + _pumped_hydro() + _hydro() + [ocgt]


def coal_ccs(context):
    """Coal CCS scenario."""
    coal = Coal_CCS(WILDCARD, 0)
    ocgt = OCGT(WILDCARD, 0)
    context.generators = [coal] + _pumped_hydro() + _hydro() + [ocgt]


def _every_poly(gentype):
    """Create a generator of type gentype in each of the 44 polygons."""
    result = []

    for poly in range(1, 10 if RUNFAST else 44):
        # for poly in range(1, 44):
        if gentype == Biofuel:
            result.append(gentype(poly, 0, label=f'polygon {poly} GT'))
        elif gentype == PV1Axis:
            cfg = configfile.get('generation', 'pv1axis-trace')
            result.append(gentype(poly, 0, cfg, poly - 1,
                                  build_limit=pv_limit[poly],
                                  label=f'polygon {poly} PV'))
        elif gentype == Behind_Meter_PV:
            cfg = configfile.get('generation', 'rooftop-pv-trace')
            result.append(gentype(poly, 0, cfg, poly - 1,
                                  build_limit=rooftop_limit[poly],
                                  label=f'polygon {poly} rooftop'))
        elif gentype == Wind:
            cfg = configfile.get('generation', 'wind-trace')
            result.append(gentype(poly, 0, cfg, poly - 1,
                                  build_limit=wind_limit[poly],
                                  label=f'polygon {poly} wind'))
    return result


def re100(context):
    """100% renewable electricity."""
    result = []
    # The following list is in merit order.
    for g in [PV1Axis, Wind, WindOffshore, PumpedHydroTurbine, Hydro,
              CentralReceiver, Biofuel]:
        if g == PumpedHydroTurbine:
            result += _pumped_hydro()
        elif g == Hydro:
            result += _hydro()
        elif g == WindOffshore:
            cfg = configfile.get('generation', 'offshore-wind-trace')
            for column, poly in enumerate([31, 36, 38, 40]):
                result.append(g(poly, 0, cfg, column,
                                build_limit=offshore_wind_limit[poly],
                                label=f'polygon {poly} offshore'))
        elif g in [Biofuel, PV1Axis, CentralReceiver, Wind]:
            result += _every_poly(g)
        else:
            raise UnreachableError('unhandled generator type')
    context.generators = result


def _batterySet(polygon, capacity, shours, comment):
   """
   Generate and return a pair of battery generator objects: one for the charging
   side and one for the discharging side.

   capacity is the initial generating capacity (in MW)
   shours is the number of full load storage hours
   comment is the prefix for the object titles (eg. "P24 battery")
   """
   # discharge between 5pm and 7am daily
   hrs = list(range(0, 8)) + list(range(17, 24))
   storage = BatteryStorage(capacity * shours, f"{comment} Storage")
   batt = Battery(polygon, capacity, shours, storage, f"{comment} Discharge", discharge_hours=hrs)
   load = BatteryLoad(polygon, capacity, storage, f"{comment} Charge", discharge_hours=hrs, rte=0.9)
   dual = DualSetter(batt.setters[0], load.setters[0])
   load.setters = []
   batt.setters = [(dual.set_capacity, 0, 40)]
   return (batt, load)


""" Start Elona's Scenarios """


def _existingSolarWind(gentype):
    """Add in existing large scale solar, rooftop PV, and wind generators for each polygon. All data is in MW"""
    """INCLUDES ROOFTOP SOLAR HERE"""
    """ERC Addition"""
    # (Total solarfarms capacity for each polygon -
    # /Users/elonarey-costa/OneDrive\ -\ UNSW/PhD/Data/
    # NEM_SolarGenerators_Spatial_Cap_OPENNEM.csv )
    # (Total windfarm capacty for each polygon -
    # /Users/elonarey-costa/OneDrive\ -\ UNSW/PhD/Data/
    # NEM_WindGenerators_Spatial_Cap_OPENNEM.csv)
    # Total rooftop PV capacity for each polygon - 
    # /Users/elonarey-costa/OneDrive\ -\ UNSW/PhD/
    # 2.0Project_Surplus/Data/RooftopPV_APVI/
    # TotalPVCapacity_per_Polygon.xlsx
    result = []
    if gentype == PV1Axis:
        cfg = configfile.get('generation', 'pv1axis-trace')
        for (poly, capacity) in [(1, 12.5), (2, 5), (3, 50), (4, 962), (6, 205.7),
                                 (7, 26), (11, 141.13), (16, 14.7),
                                 (17, 302.75), (23, 267.7), (24, 20),
                                 (26, 135), (27,4.9),(28, 53), (29, 1.2),
                                 (30, 256.5), (31, 134.5), (32, 110.3),
                                 (33, 868.13), (34, 617.6), (35, 121),
                                 (36, 55.5), (37, 55), (38, 217), (39, 111.8)]:
            g = gentype(poly, capacity, cfg, poly - 1,
                        build_limit=capacity / 1000,
                        label=f'polygon {poly} Existing PV')
            g.capcost = lambda costs: 0
            g.setters = []
            result.append(g)
    elif gentype == Wind:
        cfg = configfile.get('generation', 'wind-trace')
        for (poly, capacity) in [(1, 192.52), (24, 442.48),
                                 (26, 355.03), (27, 1086.26), (28, 198.94),
                                 (30, 113.19), (31, 9.9),
                                 (32, 614.3), (36, 1137.44), (37, 2026.35),
                                 (38, 21), (39, 874.4),
                                 (40, 251.35), (41, 168), (43, 144)]:
            g = gentype(poly, capacity, cfg, poly - 1,
                        build_limit=capacity / 1000,
                        label=f'polygon {poly} Existing Wind')
            g.capcost = lambda costs: 0
            g.setters = []
            result.append(g)
    elif gentype == Behind_Meter_PV:
        cfg = configfile.get('generation', 'rooftop-pv-trace')
        for (poly, capacity) in [(1, 184.5), (2, 1.2), (3, 7.4), 
                                 (4, 296.8), (5, 0.6), (6, 2.9), (7, 141.11), 
                                 (8, 2.2), (9, 1.1), (10, 16.2), (11, 219.8), 
                                 (14, 0.9), (15, 4.2), (16, 39.5), (17, 3005.6), (19, 3.6), 
                                 (21, 0.8), (22, 6.2), (23, 46.2), (24, 428.2), 
                                 (25, 3.1), (26, 106.8), (27, 39.1), (28, 20.6), 
                                 (29, 5.9), (30, 86.3), (31, 2147.2), (32, 1330.1), 
                                 (33, 53.6), (34, 45.4), (35, 166.9), (36, 566.2), 
                                 (37, 94.8), (38, 190.1), (39, 2434.1), (40, 34.8), 
                                 (41, 65.7), (42, 5), (43, 95.8)]:
            g = gentype(poly, capacity, cfg, poly - 1,
                        build_limit=capacity / 1000,
                        label=f'polygon {poly} Existing Rooftop')
            g.capcost = lambda costs: 0
            g.setters = []
            result.append(g)
    return result


"""100% renewable electricity with only PV, Wind, Hydro.
ERC Addition"""
""" Start Elona's Scenarios """


def re100SWH(context):
    """This scenario is the original Re100SWH scenario that was used in paper 1"""
    """IT ASSUMES: """
    """100% renewable electricity with only PV, Wind, Hydro."""
    """NO ROOFTOP SOLAR"""
    """Existing capacity for PV and Wind are as of June 2022"""
    """Existing Hydro and Pumped Hydro are placed where they are located IRL"""
    """Adds a new PV and Wind generator to each polygon"""

    """Note: PumpedHydroTurbine used to be called PumpedHydro in paper 1 but the code for these generators has since changed"""

    result = []

    # The following list is in merit order.
    for g in [PV1Axis, Wind, PumpedHydroTurbine, Hydro]:
        if g == PumpedHydroTurbine:
            result += _pumped_hydro()
        elif g == Hydro:
            result += _hydro()
        elif g in [PV1Axis, Wind]:
            result += _existingSolarWind(g)
            result += _every_poly(g)
        else:
            raise ValueError('unhandled generator type')  # pragma: no cover
    context.generators = result


def re100SWHB4(context):
    """This scenario is the original Re100SWHB scenario that was used in paper 1"""
    """IT ASSUMES: """
    """100% renewable electricity with only PV, Wind, Hydro."""
    """NO ROOFTOP SOLAR"""
    """Existing capacity for PV and Wind are as of June 2022"""
    """Existing Hydro and Pumped Hydro are placed where they are located IRL"""
    """Adds a new PV and Wind generator to each polygon"""
    """Put a 1, 2, 4, 8 hour battery into Polygon 24 in NSW with a flexible capacity to test which one is least-cost"""
    """BATTERY AT THE END OF MERIT ORDER"""

    re100SWH(context)
    # discharge between 5pm and 7am daily
    # discharge between 5pm and 7am daily
    hrs = list(range(0, 8)) + list(range(17, 24))
    battery1 = Battery(24, 100, 1, discharge_hours=hrs,
                         label=f'{"P24 New Batt 1 NSW"}', rte=0.9)
    battery2 = Battery(24, 100, 2, discharge_hours=hrs,
                         label=f'{"P24 New Batt 2 NSW"}', rte=0.9)
    battery4 = Battery(24, 100, 4, discharge_hours=hrs,
                         label=f'{"P24 New Batt 4 NSW"}', rte=0.9)
    battery8 = Battery(24, 100, 8, discharge_hours=hrs,
                         label=f'{"P24 New Batt 8 NSW"}', rte=0.9)
    context.generators = (context.generators
                          + [battery1]
                          + [battery2]
                          + [battery4]
                          + [battery8])


def re100SWHB4G(context):
    """This scenario is the original Re100SWHB+ (gas scenario) scenario that was used in paper 1"""
    """IT ASSUMES: """
    """100% renewable electricity with only PV, Wind, Hydro."""
    """NO ROOFTOP SOLAR"""
    """Existing capacity for PV and Wind are as of June 2022"""
    """Existing Hydro and Pumped Hydro are placed where they are located IRL"""
    """Adds a new PV and Wind generator to each polygon"""
    """Put a 1, 2, 4, 8 hour battery into Polygon 24 in NSW with a flexible capacity to test which one is least-cost"""
    """Add in the gas generation fleet at the end that is the size of the existing OCGT fleet."""

    re100SWHB4(context)
    gasNew = OCGT(24, 6700, label=f'{"P24 Existing OCGT NSW"}')
    gasNew.setters = []
    context.generators = (context.generators + [gasNew])


def re100SWH_existingbatteries(context):
    """This scenario is an original testing scenario but it was never used for paper 1"""
    """It takes scenario re100SWH but adds in the NEM existing battery fleet"""
    """I am leaving it here for the data on existing battery fleet as of 2023"""

    re100SWH(context)
    # discharge between 5pm and 7am daily
    # batteries operational as of July 2022 
    hrs = list(range(0, 8, 2)) + list(range(16, 24, 2))
    rte = 1
    # Hornsdale has 150MW capacity for 1.25 hours
    batteryhornsdaleSA = Battery(19, 120, 1, discharge_hours=hrs,
                                 label=f'{"P19 Existing Batt Hornsdale SA"}',
                                 rte=rte)
    batteryhornsdaleSA.capcost = lambda costs: 0
    batteryhornsdaleSA.setters = []
    # Dalrymple BESS is 30MW capacity for 0.27 hrs
    batDalrympleSA = Battery(26, 60, 1, discharge_hours=hrs,
                             label=f'{"P26 Existing Batt Dalrymple SA"}',
                             rte=rte)
    batDalrympleSA.capcost = lambda costs: 0
    batDalrympleSA.setters = []
    # Ballarat EES is 30MW for 1 hr
    batBallaratVIC = Battery(38, 30, 1, discharge_hours=hrs,
                             label=f'{"P38 Existing Batt Ballarat VIC"}',
                             rte=rte)
    batBallaratVIC.capcost = lambda costs: 0
    batBallaratVIC.setters = []
    # Gannawarra EES is 25MW for 1.97 hr
    batGannawarraVIC = Battery(34, 25, 2, discharge_hours=hrs,
                               label=f'{"P38 Existing Batt Gannawarra VIC"}',
                               rte=rte)
    batGannawarraVIC.capcost = lambda costs: 0
    batGannawarraVIC.setters = []
    # Lake Bonney BESS1 EES is 25MW for 2.08 hr
    batBonneySA = Battery(34, 25, 2, discharge_hours=hrs,
                          label=f'{"P38 Existing Batt Bonney VIC"}',
                          rte=rte)
    batBonneySA.capcost = lambda costs: 0
    batBonneySA.setters = []
    # Victorian Big Battery is 300MW for 1.5 hr - rounded to 2 hours
    batVicBB = Battery(39, 300, 2, discharge_hours=hrs,
                          label=f'{"P38 Existing Batt VicBB VIC"}',
                          rte=rte)
    batVicBB.capcost = lambda costs: 0
    batVicBB.setters = []
    # Bulgana is 20MW for 1.7 hr - rounded to 2 hours
    batBulgana = Battery(37, 20, 2, discharge_hours=hrs,
                          label=f'{"P38 Existing Batt Bulgana VIC"}',
                          rte=rte)
    batBulgana.capcost = lambda costs: 0
    batBulgana.setters = []

    context.generators = (context.generators 
                          + [batteryhornsdaleSA]
                          + [batDalrympleSA]
                          + [batBallaratVIC]
                          + [batGannawarraVIC]
                          + [batBonneySA]
                          + [batVicBB]
                          + [batBulgana])


def re100SWH_2(context):
    """This scenario is the original Re100SWH scenario that was used in paper 2"""
    """We do not use it explicitly in paper 2 BUT we use it inside of re100SWHB_2"""
    
    """It is the same as for paper 1 but ADDS in rooftop solar"""
    """IT ASSUMES: """
    """100% renewable electricity with only Large Scale PV, Rooftop PV, Wind, Hydro."""
    """Existing capacity for Large Scale PV and Wind are as of June 2022"""
    """Existing capacity for Rooftop Solar PV are as of September 2023"""
    """Existing Hydro and Pumped Hydro are placed where they are located IRL"""
    """Adds a new rooftop, largescale PV and Wind generator to each polygon"""

    """To Note: The code for battery and hydro generators has changed between Paper 1 and Paper 2"""
        
    result = []

    # The following list is in merit order.
    for g in [Behind_Meter_PV, PV1Axis, Wind, PumpedHydroTurbine, Hydro]:
        if g == PumpedHydroTurbine:
            result += _pumped_hydro()
        elif g == Hydro:
            result += _hydro()
        elif g in [Behind_Meter_PV, PV1Axis, Wind]:
            result += _existingSolarWind(g)
            result += _every_poly(g)
        else:
            raise ValueError('unhandled generator type')  # pragma: no cover
    context.generators = result


def re100SWHB_2(context):
    """This scenario is the original Re100SWHB scenario that was used in paper 2"""    
    """It is the same as for paper 1 but ADDS in rooftop solar and changes the config of battery storage and load"""
    """IT ASSUMES: """
    """100% renewable electricity with only Large Scale PV, Rooftop PV, Wind, Hydro."""
    """Existing capacity for Large Scale PV and Wind are as of June 2022"""
    """Existing capacity for Rooftop Solar PV are as of September 2023"""
    """Existing Hydro and Pumped Hydro are placed where they are located IRL"""
    """Adds a new rooftop, largescale PV and Wind generator to each polygon"""

    """To Note: The code for battery and hydro generators has changed between Paper 1 and Paper 2"""

    re100SWH_2(context)

    # discharge between 5pm and 7am daily
    hrs = list(range(0, 8)) + list(range(17, 24))

    #1 hour battery that NEMO can vary
    batt1, battload1 = _batterySet(24, 100, 1, "P24 Battery 1")
    #2 hour battery that NEMO can vary
    batt2, battload2 = _batterySet(24, 100, 2, "P24 Battery 2")
    #4 hour battery that NEMO can vary
    batt4, battload4 = _batterySet(24, 100, 4, "P24 Battery 4")
    #8 hour battery that NEMO can vary
    batt8, battload8 = _batterySet(24, 100, 8, "P24 Battery 8")

    context.generators = context.generators + [batt1, battload1, batt2, battload2, batt4, battload4, batt8, battload8] 


def re100SWHB_2_BattStartEnd(context):
    """This scenario is the original Re100SWHB scenario that was used in paper 2"""    
    """It is the same as for paper 1 but ADDS in rooftop solar and changes the config of battery storage and load"""
    """IT ASSUMES: """
    """100% renewable electricity with only Large Scale PV, Rooftop PV, Wind, Hydro."""
    """Existing capacity for Large Scale PV and Wind are as of June 2022"""
    """Existing capacity for Rooftop Solar PV are as of September 2023"""
    """Existing Hydro and Pumped Hydro are placed where they are located IRL"""
    """Adds a new rooftop, largescale PV and Wind generator to each polygon"""

    """To Note: The code for battery and hydro generators has changed between Paper 1 and Paper 2"""

    re100SWH_2(context)

    #1 hour battery that NEMO can vary
    battstorage1 = BatteryStorage(100, "P24 New Batt Storage 1 NSW") #Storage MWh
    batt1 = Battery(24, 100, 1, battstorage1, "P24 Batt Discharge 1 NSW") #Capacity MW
    battload1 = BatteryLoad(24, 100, battstorage1, "P24 Batt Charge 1 NSW") #Capacity MW
    dual1 = DualSetter(battload1.setters[0], batt1.setters[0])
    battload1.setters = []
    batt1.setters = [(dual1.set_capacity, 0, 40)]
    
    #2 hour battery that NEMO can vary
    battstorage2 = BatteryStorage(200, "P24 New Batt Storage 2 NSW") #Storage MWh 
    batt2 = Battery(24, 100, 2, battstorage2, "P24 New Batt Discharge 2 NSW") #Capacity MW
    battload2 = BatteryLoad(24, 100, battstorage2, "P24 New Batt Charge 2 NSW") #Capacity MW
    dual2 = DualSetter(battload2.setters[0], batt2.setters[0])
    battload2.setters = []
    batt2.setters = [(dual2.set_capacity, 0, 40)]
    
    #4 hour battery that NEMO can vary
    battstorage4 = BatteryStorage(400, "P24 New Batt Storage 4 NSW") #Storage MWh
    batt4 = Battery(24, 100, 4, battstorage4, "P24 New Batt Discharge 4 NSW") #Capacity MW
    battload4 = BatteryLoad(24, 100, battstorage4, "P24 New Batt Charge 4 NSW") #Capacity MW
    dual4 = DualSetter(battload4.setters[0], batt4.setters[0])
    battload4.setters = []
    batt4.setters = [(dual4.set_capacity, 0, 40)]

    #8 hour battery that NEMO can vary
    battstorage8 = BatteryStorage(800, "P24 New Batt Storage 8 NSW") #Storage MWh
    batt8 = Battery(24, 100, 8, battstorage8, "P24 New Batt Discharge 8 NSW") #Capacity MW
    battload8 = BatteryLoad(24, 100, battstorage8, "P24 New Batt Charge 8 NSW") #Capacity MW
    dual8 = DualSetter(battload8.setters[0], batt8.setters[0])
    battload8.setters = []
    batt8.setters = [(dual8.set_capacity, 0, 40)]

    #1 hour battery that NEMO can vary
    battstorage11 = BatteryStorage(100, "P24 New Batt Storage 11 NSW") #Storage MWh
    batt11 = Battery(24, 100, 1, battstorage11, "P24 Batt Discharge 11 NSW") #Capacity MW
    battload11 = BatteryLoad(24, 100, battstorage11, "P24 Batt Charge 11 NSW") #Capacity MW
    dual11 = DualSetter(battload11.setters[0], batt11.setters[0])
    battload11.setters = []
    batt11.setters = [(dual11.set_capacity, 0, 40)]
    
    #2 hour battery that NEMO can vary
    battstorage22 = BatteryStorage(200, "P24 New Batt Storage 22 NSW") #Storage MWh 
    batt22 = Battery(24, 100, 2, battstorage22, "P24 New Batt Discharge 22 NSW") #Capacity MW
    battload22 = BatteryLoad(24, 100, battstorage22, "P24 New Batt Charge 22 NSW") #Capacity MW
    dual22 = DualSetter(battload22.setters[0], batt22.setters[0])
    battload22.setters = []
    batt22.setters = [(dual22.set_capacity, 0, 40)]
    
    #4 hour battery that NEMO can vary
    battstorage44 = BatteryStorage(400, "P24 New Batt Storage 44 NSW") #Storage MWh
    batt44 = Battery(24, 100, 4, battstorage44, "P24 New Batt Discharge 44 NSW") #Capacity MW
    battload44 = BatteryLoad(24, 100, battstorage44, "P24 New Batt Charge 44 NSW") #Capacity MW
    dual44 = DualSetter(battload44.setters[0], batt44.setters[0])
    battload44.setters = []
    batt44.setters = [(dual44.set_capacity, 0, 40)]

    #8 hour battery that NEMO can vary
    battstorage88 = BatteryStorage(800, "P24 New Batt Storage 88 NSW") #Storage MWh
    batt88 = Battery(24, 100, 8, battstorage88, "P24 New Batt Discharge 88 NSW") #Capacity MW
    battload88 = BatteryLoad(24, 100, battstorage88, "P24 New Batt Charge 88 NSW") #Capacity MW
    dual88 = DualSetter(battload88.setters[0], batt88.setters[0])
    battload88.setters = []
    batt88.setters = [(dual88.set_capacity, 0, 40)]

    #battload.setters = batt.setters
    #batt.setters = [] # If you want fixed capacity batteries, you need to set the batt and battload setters to []. 
    #battload.setters = [] # Otherwise, NEMO will try varying the capacity which in turn varies the full loads hours to a non-{1,2,4,8} multiple.
    #context.generators = context.generators + [batt1, battload1, batt2, battload2, batt4, battload4, batt8, battload8] 
    context.generators = [batt1, battload1, batt2, battload2, batt4, battload4, batt8, battload8] + context.generators + [batt11, battload11, batt22, battload22, batt44, battload44, batt88, battload88] 


def re100SWHB_2_COMPARE_1(context):
    """THIS IS A TESTING SCENARIO"""
    """Here, we are comparing the original re100SWHB4 to re100SWHB4_2"""
    """This is because the code has changed for battery generators between paper 1 and 2"""

    re100SWH(context)
    # discharge between 5pm and 7am daily
    hrs = list(range(0, 8)) + list(range(17, 24))
    #1 hour battery that NEMO can vary
    battstorage1 = BatteryStorage(100, "Battery Storage 1 hours") #Storage MWh
    batt1 = Battery(38, 100, 1, battstorage1, "P38 Battery Discharge 1hr", discharge_hours = hrs) #Capacity MW
    battload1 = BatteryLoad(38, 100, battstorage1, "P38 Battery Charge 1hr", discharge_hours = hrs, rte=0.9) #Capacity MW
    dual1 = DualSetter(battload1.setters[0], batt1.setters[0])
    battload1.setters = []
    batt1.setters = [(dual1.set_capacity, 0, 40)]
    
    #2 hour battery that NEMO can vary
    battstorage2 = BatteryStorage(200, "Battery Storage 2 hours") #Storage MWh 
    batt2 = Battery(38, 100, 2, battstorage2, "P38 Battery Discharge 2hrs", discharge_hours = hrs) #Capacity MW
    battload2 = BatteryLoad(38, 100, battstorage2, "P38 Battery Charge 2hrs", discharge_hours = hrs, rte=0.9) #Capacity MW
    dual2 = DualSetter(battload2.setters[0], batt2.setters[0])
    battload2.setters = []
    batt2.setters = [(dual2.set_capacity, 0, 40)]
    
    #4 hour battery that NEMO can vary
    battstorage4 = BatteryStorage(400, "Battery Storage 4 hours") #Storage MWh
    batt4 = Battery(38, 100, 4, battstorage4, "P38 Battery Discharge 4hrs", discharge_hours = hrs) #Capacity MW
    battload4 = BatteryLoad(38, 100, battstorage4, "P38 Battery Charge 4hrs", discharge_hours = hrs, rte=0.9) #Capacity MW
    dual4 = DualSetter(battload4.setters[0], batt4.setters[0])
    battload4.setters = []
    batt4.setters = [(dual4.set_capacity, 0, 40)]

    #8 hour battery that NEMO can vary
    battstorage8 = BatteryStorage(800, "Battery Storage 8 hours") #Storage MWh
    batt8 = Battery(38, 100, 8, battstorage8, "P38 Battery Discharge 8hrs", discharge_hours = hrs) #Capacity MW
    battload8 = BatteryLoad(38, 100, battstorage8, "P38 Battery Charge 8hrs", discharge_hours = hrs, rte=0.9) #Capacity MW
    dual8 = DualSetter(battload8.setters[0], batt8.setters[0])
    battload8.setters = []
    batt8.setters = [(dual8.set_capacity, 0, 40)]

    #battload.setters = batt.setters
    #batt.setters = [] # If you want fixed capacity batteries, you need to set the batt and battload setters to []. 
    #battload.setters = [] # Otherwise, NEMO will try varying the capacity which in turn varies the full loads hours to a non-{1,2,4,8} multiple.
    context.generators = context.generators + [batt1] + [battload1] + [batt2] + [battload2] + [batt4] + [battload4] + [batt8] + [battload8] 


""" End Elonas Scenarios"""


def _one_per_poly(region):
    """Return three lists of wind, PV and CST generators, one per polygon."""
    pv = []
    wind = []
    cst = []

    wind_cfg = configfile.get('generation', 'wind-trace')
    pv_cfg = configfile.get('generation', 'pv1axis-trace')
    cst_cfg = configfile.get('generation', 'cst-trace')

    for poly in region.polygons:
        wind.append(Wind(poly, 0, wind_cfg,
                         poly - 1,
                         build_limit=wind_limit[poly],
                         label=f'poly {poly} wind'))
        pv.append(PV1Axis(poly, 0, pv_cfg,
                          poly - 1,
                          build_limit=pv_limit[poly],
                          label=f'poly {poly} PV'))
        cst.append(CentralReceiver(poly, 0, 2.5, 8, cst_cfg,
                                   poly - 1,
                                   build_limit=cst_limit[poly],
                                   label=f'poly {poly} CST'))
    return wind, pv, cst


def re100_one_region(context, region):
    """100% renewables in one region only."""
    re100(context)
    context.regions = [region]
    wind, pv, cst = _one_per_poly(region)
    newlist = wind
    newlist += pv
    newlist += [g for g in context.generators if
                isinstance(g, Hydro) and g.region() is region]
    newlist += cst
    newlist += [g for g in context.generators if
                isinstance(g, Biofuel) and g.region() is region]
    context.generators = newlist


def re_plus_ccs(context):
    """Mostly renewables with fossil and CCS augmentation."""
    re100(context)
    coal = Black_Coal(WILDCARD, 0)
    # pylint: disable=redefined-outer-name
    coal_ccs = Coal_CCS(WILDCARD, 0)
    # pylint: disable=redefined-outer-name
    ccgt = CCGT(WILDCARD, 0)
    ccgt_ccs = CCGT_CCS(WILDCARD, 0)
    ocgt = OCGT(WILDCARD, 0)
    context.generators = [coal, coal_ccs, ccgt, ccgt_ccs] + \
        context.generators[:-4] + [ocgt]


def re_plus_fossil(context):
    """Mostly renewables with some fossil augmentation."""
    re100(context)
    context.generators = \
        [Black_Coal(WILDCARD, 0), CCGT(WILDCARD, 0)] + \
        context.generators[:-4] + [OCGT(WILDCARD, 0)]


def re100_dsp(context):
    """Mostly renewables with demand side participation."""
    re100(context)
    context.generators += _demand_response()


def re100_nocst(context):
    """100% renewables, but no CST."""
    re100(context)
    newlist = [g for g in context.generators if not isinstance(g, CST)]
    context.generators = newlist


def re100_nsw(context):
    """100% renewables in New South Wales only."""
    re100_one_region(context, regions.nsw)


def re100_qld(context):
    """100% renewables in Queensland only."""
    re100_one_region(context, regions.qld)


def re100_south_aus(context):
    """100% renewables in South Australia only."""
    re100_one_region(context, regions.sa)


supply_scenarios = {'__one_ccgt__': _one_ccgt,  # nb. for testing only
                    'ccgt': ccgt,
                    'ccgt-ccs': ccgt_ccs,
                    'coal-ccs': coal_ccs,
                    're+ccs': re_plus_ccs,
                    're+fossil': re_plus_fossil,
                    're100': re100,
                    're100-qld': re100_qld,
                    're100-nsw': re100_nsw,
                    're100-sa': re100_south_aus,
                    're100SWH': re100SWH,
                    're100SWHB4':re100SWHB4,
                    're100SWHB4G':re100SWHB4G,
                    're100SWH_existingbatteries': re100SWH_existingbatteries,
                    're100SWHB_2': re100SWHB_2,
                    're100SWHB_2_BattStartEnd': re100SWHB_2_BattStartEnd,
                    're100SWHB_2_COMPARE_1': re100SWHB_2_COMPARE_1,
                    're100+dsp': re100_dsp,
                    're100-nocst': re100_nocst,
                    'replacement': replacement}