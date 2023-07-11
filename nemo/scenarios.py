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
from nemo.polygons import (WILDCARD, cst_limit, offshore_wind_limit, pv_limit,
                           wind_limit)
from nemo.storage import (PumpedHydroStorage, BatteryStorage)
from nemo.types import UnreachableError

RUNFAST = 0  # changes everypoly from 44 to 10


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

    # NSW: Tumut 3 (6x250), Bendeela (2x80) and Kangaroo Valley (2x40)
    psh36stg = PumpedHydroStorage(15000, label='Tumut 3 storage')
    psh36pump = PumpedHydroPump(36, 1740, psh36stg, label='Tumut 3 pump')
    psh36turb = PumpedHydroTurbine(36, 1740, psh36stg,
                                   label='Tumut 3 generator')

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
                                  build_limit=pv_limit[poly],
                                  label=f'polygon {poly} rooftop PV'))
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
                                label='polygon {poly} offshore'))
        elif g in [Biofuel, PV1Axis, CentralReceiver, Wind]:
            result += _every_poly(g)
        else:
            raise UnreachableError('unhandled generator type')
    context.generators = result


""" Start Elona's Scenarios """


def _one_battery(context):
    """Add in one 2 hour into the middle of NSW battery"""
    result = []
    # discharge between 5pm and 7am daily
    # discharge between 5pm and 7am daily
    hrs = list(range(0, 8)) + list(range(17, 24))
    batteryNew = Battery(24, 100, 2, discharge_hours=hrs,
                         label=f'{"P24 New Added Batt NSW"}', rte=0.9)
    result.append(batteryNew)
    return result


def _existingSolarWind(gentype):
    """Add in existing large scale solar and wind generators for each polygon."""
    """ERC Addition"""
    # (Total solarfarms capacity for each polygon -
    # /Users/elonarey-costa/OneDrive\ -\ UNSW/PhD/Data/
    # NEM_SolarGenerators_Spatial_Cap_OPENNEM.csv )
    # (Total windfarm capacty for each polygon -
    # /Users/elonarey-costa/OneDrive\ -\ UNSW/PhD/Data/
    # NEM_WindGenerators_Spatial_Cap_OPENNEM.csv)
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
    return result


def _allSolarWind(gentype):
    """Add in existing large sclae solar, rooftop PV, and wind generators for each polygon. All data is in MW"""
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
        cfg = configfile.get('generation', 'pv1axis-trace')
        for (poly, capacity) in [(1, 373.933), (2, 5.91), (3, 11.239), 
                                 (4, 1657.773), (5, 1.364), (6, 81.177), (7, 191.463), 
                                 (8, 22.504), (9, 2.135), (10, 245.874), (11, 571.568), 
                                 (14, 5.125), (15, 7.411), (16, 1240.491), (17, 4965.095), (19, 147.906), 
                                 (21, 54.218), (22, 113.322), (23, 284.104), (24, 1295.258), 
                                 (25, 4.74), (26, 426.236), (27, 111.214), (28, 31.744), 
                                 (29, 132.212), (30, 886.123), (31, 3592.998), (32, 2247.75), 
                                 (33, 1454.935), (34, 826.244), (35, 623.525), (36, 916.345), 
                                 (37, 145.318), (38, 530.565), (39, 3819.245), (40, 47.774), 
                                 (41, 92.129), (42, 6.101), (43, 119.205), ]:
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


def one_in_eachstate(gentype):
    """Create one generator of type gentype
    (only solar and wind) in each state."""
    """Capacity of 25 GW for each PV and Wind site = 25 GW """
    result = []
    for poly in range[17, 23, 37, 39, 26]:
        # Brisbane (QLD), Dubbo (NSW), Ballarat (VIC),
        # Queenstown (TAS), Port Lincoln (SA)
        if gentype == PV1Axis:
            cfg = configfile.get('generation', 'pv1axis-trace')
            result.append(gentype(poly, 25, cfg, poly - 1,
                                  build_limit=pv_limit[poly],
                                  label=f'polygon {poly} PV'))
        elif gentype == Wind:
            cfg = configfile.get('generation', 'wind-trace')
            result.append(gentype(poly, 25, cfg, poly - 1,
                                  build_limit=wind_limit[poly],
                                  label=f'polygon {poly} wind'))
    return result


def re100SWH_WA(context):
    '''Adds WA into the picture'''
    context.regions.append(regions.wa)  # adds WA into the picture.
    re100SWH(context)


def re100SWH(context):
    """100% renewable electricity with only PV, Wind, Hydro."""
    """This will populate all polygons with an empty
    PV and Wind genererator & """
    """Put hydro and pumped hydro where they should be located"""
    result = []

    # The following list is in merit order.
    for g in [Behind_Meter_PV, PV1Axis, Wind, PumpedHydroStorage, Hydro]:
        if g == PumpedHydroStorage:
            result += [h for h in _hydro() if isinstance(h, PumpedHydroStorage)]
        elif g == Hydro:
            result += [h for h in _hydro() if not isinstance(h, PumpedHydroStorage)]
        elif g in [Behind_Meter_PV, PV1Axis, Wind]:
            result += _allSolarWind(g)
            result += _every_poly(g)
        else:
            raise ValueError('unhandled generator type')  # pragma: no cover
    context.generators = result


def re100SWHBMid(context):
    """100% renewable electricity with PV, Wind, Battery, Hydro."""
    """This will populate all polygons with an empty
    PV and Wind genererator & """
    """Put a 2 hour battery into Polygon 24 in NSW"""
    """Put hydro and pumped hydro where they should be located"""
    result = []

    # The following list is in merit order.
    for g in [PV1Axis, Wind, Battery, PumpedHydroStorage, Hydro]:
        if g == PumpedHydroStorage:
            result += [h for h in _hydro() if isinstance(h, PumpedHydroStorage)]
        elif g == Hydro:
            result += [h for h in _hydro() if not isinstance(h, PumpedHydroStorage)]
        elif g in [PV1Axis, Wind]:
            result += _existingSolarWind(g)
            result += _every_poly(g)
        elif g == Battery:
            result += _one_battery(g)
        else:
            raise ValueError('unhandled generator type')  # pragma: no cover
    context.generators = result


def re100SWHBLast(context):
    """100% renewable electricity with PV, Wind, Battery, Hydro."""
    """This will populate all polygons with an empty
    PV and Wind genererator & """
    """Put hydro and pumped hydro where they should be located"""
    """Put a 2 hour battery into Polygon 24 in NSW"""
    result = []

    # The following list is in merit order with Battery Last.
    for g in [PV1Axis, Wind, PumpedHydroStorage, Hydro, Battery]:
        if g == PumpedHydroStorage:
            result += [h for h in _hydro() if isinstance(h, PumpedHydroStorage)]
        elif g == Hydro:
            result += [h for h in _hydro() if not isinstance(h, PumpedHydroStorage)]
        elif g in [PV1Axis, Wind]:
            result += _existingSolarWind(g)
            result += _every_poly(g)
        elif g == Battery:
            result += _one_battery(g)
        else:
            raise ValueError('unhandled generator type')  # pragma: no cover
    context.generators = result


def re100SWHB4(context):
    """100% renewable electricity with PV, Wind, Battery, Hydro."""
    """This will populate all polygons with an empty
    PV and Wind genererator & """
    """Put hydro and pumped hydro where they should be located"""
    """Put a 1, 2, 4, 8 hour battery into Polygon 24 in NSW with a flexible capacity to test which one is least-cost"""
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
    """100% renewable electricity with PV, Wind, Battery, Hydro."""
    """This will populate all polygons with an empty
    PV and Wind genererator & """
    """Put hydro and pumped hydro where they should be located"""
    """Put a 1, 2, 4, 8 hour battery into Polygon 24 in NSW with a flexible capacity to test which one is least-cost"""
    """Add in the gas generation fleet at the end. """
    re100SWHB4(context)
    gasNew = OCGT(24, 6700, label=f'{"P24 Existing OCGT NSW"}')
    gasNew.setters = []
    context.generators = (context.generators + [gasNew])
    

def re100SWHB1G(context):
    """100% renewable electricity with PV, Wind, Hydro, Pumped Hydrp, Battery, Gas."""
    """This will populate all polygons with an empty
    PV and Wind genererator & """
    """Put hydro and pumped hydro where they should be located"""
    """Put a 2 hour battery into Polygon 24 in NSW"""
    """Put a open cycle gas turbine 6.7 GW into Polygon 24 in NSW"""
    re100SWHBLast(context)
    gasNew = OCGT(24, 6700, label=f'{"P24 Existing OCGT NSW"}')
    gasNew.setters = []
    context.generators = (context.generators + [gasNew])


def re100SWHB_David(context):
    """Takes SWH and adds David Osmond Battery."""
    re100SWH(context)
    # discharge between 5pm and 7am daily
    hrs = list(range(0, 8)) + list(range(16, 24))
    rte = 1

    # David Osmond Battery 1 24GW/120GWh (4 hours)
    batteryDavid1 = Battery(19, 24000, 4, discharge_hours=hrs,
                            label=f'{"P19 Battery David 1 SA"}',
                            rte=rte)
    batteryDavid1.capcost = lambda costs: 0
    batteryDavid1.setters = []

    # David Osmond Battery 2 24GW/120GWh (1 hours)
    batteryDavid2 = Battery(19, 24000, 1, discharge_hours=hrs,
                            label=f'{"P19 Battery David 2 SA"}',
                            rte=rte)
    batteryDavid2.capcost = lambda costs: 0
    batteryDavid2.setters = []

    context.generators = ([batteryDavid1]
                          + [batteryDavid2]
                          + context.generators)


def re100SWH_batteries(context):
    """Takes SWH and adds existing batteries only."""
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


def re100SWH_batteries2(context):
    """Takes SWH and adds existing battery +
    one flexible battery to fill in the gaps at 5pm and 7pm
    that pop up in the re100SWH_batteries scenario."""
    re100SWH_batteries(context)
    # discharge between 5pm and 7am daily
    hrs = list(range(0, 8)) + list(range(17, 24))
    batteryNew = Battery(24, 100, 2, discharge_hours=hrs,
                         label=f'{"P24 New Added Batt NSW"}', rte=0.9)
    context.generators = [batteryNew] + context.generators


def re100SWH_batteries3(context):
    """Takes SWH and adds one flexible battery to fill in the gaps at 5pm and 7pm."""
    re100SWH(context)
    # discharge between 5pm and 7am daily
    hrs = list(range(0, 8)) + list(range(17, 24))

    #Specs of the Victorian Big Battery for testing latest battery changes
    battstorage = BatteryStorage(600) #600 MWh 
    batt = Battery(38, 300, battstorage, label = 'P38 Vic Big Batt', 
                   discharge_hours=hrs) #300 capacity MW
    battload = BatteryLoad(38, 300, battstorage, hrs, rte = 0.9)

    context.generators = [batt] + [battload]+ context.generators


def re100SWHB_dr(context):
    re100SWH_batteries(context)
    dr = DemandResponse(36, 500, 500, label=f'{"P36 Demand response NSW"}')
    dr.setters = []
    context.generators = [dr] + context.generators


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
                    're100SWH_WA': re100SWH_WA,
                    're100SWH': re100SWH,
                    're100SWHBMid':re100SWHBMid,
                    're100SWHBLast':re100SWHBLast,
                    're100SWHB4':re100SWHB4,
                    're100SWHB4G':re100SWHB4G,
                    're100SWHB1G':re100SWHB1G, 
                    're100SWHB_David': re100SWHB_David,
                    're100SWH_batteries': re100SWH_batteries,
                    're100SWH_batteries2': re100SWH_batteries2,
                    're100SWH_batteries3': re100SWH_batteries3,
                    're100SWHB_dr': re100SWHB_dr,
                    're100+dsp': re100_dsp,
                    're100-nocst': re100_nocst,
                    'replacement': replacement}
