# Copyright (C) 2012, 2013, 2014, 2022 Ben Elliston
# Copyright (C) 2014, 2015, 2016 The University of New South Wales
# Copyright (C) 2016 IT Power (Australia)
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.


RUNFAST = 1 #changes everypoly from 44 to 10 

"""Supply side scenarios."""

from nemo import configfile, regions
from nemo.generators import (CCGT, CCGT_CCS, CST, OCGT, Battery, Biofuel,
                             Black_Coal, CentralReceiver, Coal_CCS,
                             DemandResponse, Hydro, PumpedHydro, PV1Axis, Wind,
                             WindOffshore)
from nemo.polygons import (WILDCARD, cst_limit, pv_limit, wind_limit,
                           offshore_wind_limit)


def _demand_response():
    """Return a list of DR 'generators'."""
    dr1 = DemandResponse(WILDCARD, 1000, 100, "DR100")
    dr2 = DemandResponse(WILDCARD, 1000, 500, "DR500")
    dr3 = DemandResponse(WILDCARD, 1000, 1000, "DR1000")
    return [dr1, dr2, dr3]


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

    # Pumped hydro
    # QLD: Wivenhoe (http://www.csenergy.com.au/content-%28168%29-wivenhoe.htm)
    psh17 = PumpedHydro(17, 500, 5000, label='poly 17 pumped-hydro')
    # NSW: Tumut 3 (6x250), Bendeela (2x80) and Kangaroo Valley (2x40)
    psh36 = PumpedHydro(36, 1740, 15000, label='poly 36 pumped-hydro')
    return [psh17, psh36] + \
        [hydro24, hydro31, hydro35, hydro36, hydro38, hydro39] + \
        [hydro40, hydro41, hydro42, hydro43]


def replacement(context):
    """Replace the current NEM fleet, more or less."""
    context.generators = \
        [Black_Coal(WILDCARD, 0)] + _hydro() + [OCGT(WILDCARD, 0)]


def _one_ccgt(context):
    """One CCGT only."""
    context.generators = [CCGT(WILDCARD, 0)]


def ccgt(context):
    """All gas scenario."""
    context.generators = [CCGT(WILDCARD, 0)] + _hydro() + [OCGT(WILDCARD, 0)]


def ccgt_ccs(context):
    """CCGT CCS scenario."""
    # pylint: disable=redefined-outer-name
    ccgt = CCGT_CCS(WILDCARD, 0)
    ocgt = OCGT(WILDCARD, 0)
    context.generators = [ccgt] + _hydro() + [ocgt]


def coal_ccs(context):
    """Coal CCS scenario."""
    coal = Coal_CCS(WILDCARD, 0)
    ocgt = OCGT(WILDCARD, 0)
    context.generators = [coal] + _hydro() + [ocgt]


def _every_poly(gentype):
    """Create a generator of type gentype in each of the 44 polygons."""
    result = []
    
    for poly in range(1, 10 if RUNFAST else 44):
        if gentype == Biofuel:
            result.append(gentype(poly, 0, label=f'polygon {poly} GT'))
        elif gentype == PV1Axis:
            cfg = configfile.get('generation', 'pv1axis-trace')
            result.append(gentype(poly, 0, cfg, poly - 1,
                                  build_limit=pv_limit[poly],
                                  label=f'polygon {poly} PV'))
        elif gentype == CentralReceiver:
            cfg = configfile.get('generation', 'cst-trace')
            result.append(gentype(poly, 0, 2.0, 6, cfg, poly - 1,
                                  build_limit=cst_limit[poly],
                                  label=f'polygon {poly} CST'))
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
    for g in [PV1Axis, Wind, WindOffshore, PumpedHydro, Hydro,
              CentralReceiver, Biofuel]:
        if g == PumpedHydro:
            result += [h for h in _hydro() if isinstance(h, PumpedHydro)]
        elif g == Hydro:
            result += [h for h in _hydro() if not isinstance(h, PumpedHydro)]
        elif g == WindOffshore:
            cfg = configfile.get('generation', 'offshore-wind-trace')
            for column, poly in enumerate([31, 36, 38, 40]):
                result.append(g(poly, 0, cfg, column,
                                build_limit=offshore_wind_limit[poly],
                                label='polygon {poly} offshore'))
        elif g in [Biofuel, PV1Axis, CentralReceiver, Wind]:
            result += _every_poly(g)
        else:
            raise ValueError('unhandled generator type')  # pragma: no cover
    context.generators = result


def re100_batteries(context):
    """Use lots of renewables plus battery storage."""
    re100(context)
    # discharge between 6pm and 6am daily
    hrs = list(range(0, 7)) + list(range(18, 24))
    battery = Battery(WILDCARD, 0, 4, discharge_hours=hrs)
    context.generators.insert(0, battery)


def _existingSolarWind(gentype):
    """Add in existing solar and wind generators for each polygon. ERC Addition""" 
    #(Total solarfarms capacity for each polygon - /Users/elonarey-costa/OneDrive\ -\ UNSW/PhD/Data/NEM_SolarGenerators_Spatial_Cap_OPENNEM.csv )
    #(Total windfarm capacty for each polygon - /Users/elonarey-costa/OneDrive\ -\ UNSW/PhD/Data/NEM_WindGenerators_Spatial_Cap_OPENNEM.csv)
    result = []
    if gentype == PV1Axis:
        cfg = configfile.get('generation', 'pv1axis-trace') 
        for (poly, capacity) in [(3, 50), (4, 879.01), (6, 254.47), (7, 148), (11, 149.38),
         (16, 579), (17, 1189.5), (23, 291), (24, 301), (26, 270), (28, 53.76), (29, 110), 
         (30, 661), (31, 134), (32, 149.25), (33, 1177), (34, 693.56), (35, 358), 
         (36, 42.205), (37, 55), (38, 239), (39, 143)]:
            result.append(gentype(poly, capacity, cfg, poly - 1,
                                build_limit=capacity/1000,
                                label=f'polygon {poly} Existing PV'))                                       
    elif gentype == Wind:
        cfg = configfile.get('generation', 'wind-trace')
        for (poly, capacity) in [(1, 192.45), (6, 43), (17, 452), (24, 445), 
        (26, 648.75), (27, 1086.86), (28, 198.94), (30, 113), (31, 152.22), 
        (32, 615.8), (36, 1441.57), (37, 3257.69), (38, 21), (39, 1018.184), 
        (40, 250), (41, 168), (43, 148)]:
            result.append(gentype(poly, capacity, cfg, poly - 1, 
                                build_limit = capacity/1000, 
                                label = f'polygon {poly} Existing Wind'))
    return result


def re100SWH(context):
    """100% renewable electricity with only PV, Wind, Hydro. ERC Addition"""
""" Start Elona's Scenarios """

def one_in_eachstate(gentype):
    """Create one generator of type gentype (only solar and wind) in each state."""
    """Capacity of 25 GW for each PV and Wind site = 250 GW """
    result = []
    for poly in range[17, 23, 37, 39, 26 ]: #Brisbane (QLD), Dubbo (NSW), Ballarat (VIC), Queenstown (TAS), Port Lincoln (SA) 
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
    context.regions.append(regions.wa) #adds WA into the picture. 
    re100SWH(context)

def re100SWH(context):
    """100% renewable electricity with only PV, Wind, Hydro."""
    """This will populate all polygons with an empty PV and Wind genererator & """
    """Put hydro and pumped hydro where they should be located"""
    result = []

    # The following list is in merit order.
    for g in [PV1Axis, Wind, PumpedHydro, Hydro]:
        if g == PumpedHydro:
            result += [h for h in _hydro() if isinstance(h, PumpedHydro)]
        elif g == Hydro:
            result += [h for h in _hydro() if not isinstance(h, PumpedHydro)]
        elif g in [PV1Axis, Wind]:
            result += _existingSolarWind(g)
            result += _every_poly(g)
        else:
            raise ValueError('unhandled generator type')  # pragma: no cover
    context.generators = result
    
def re100SWH_batteries(context):
    """Takes SWH and adds battery."""
    re100SWH(context)
    # discharge between 6pm and 6am daily
    hrs = list(range(0, 7)) + list(range(18, 24))
    batteryhornsdaleSA = Battery(19, 100, 1, discharge_hours=hrs, label = f'polygon 19 Battery Hornsdale SA', rte = 0.9)
    batteryWarratahNSW = Battery(30, 700, 2, discharge_hours=hrs, label = f'polygon 30 Battery Warratah NSW', rte = 0.9)
    context.generators = [batteryhornsdaleSA] + [batteryWarratahNSW] + context.generators

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
                    're100+batteries': re100_batteries,
                    're100SWH_WA': re100SWH_WA,
                    're100SWH': re100SWH, 
                    're100SWH_batteries': re100SWH_batteries,
                    're100+dsp': re100_dsp,
                    're100-nocst': re100_nocst,
                    'replacement': replacement}
