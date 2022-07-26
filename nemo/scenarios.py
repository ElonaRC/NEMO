# Copyright (C) 2012, 2013, 2014, 2022 Ben Elliston
# Copyright (C) 2014, 2015, 2016 The University of New South Wales
# Copyright (C) 2016 IT Power (Australia)
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

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

def _existingSolar():
    """Return a list of exiting large scale utility generators"""


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
    for poly in range(1, 44):
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
    """Add in existing generators for each polygon""" 
    #(Total solarfarms capacity for each polygon - https://pv-map.apvi.org.au/power-stations)
    #Total size of solarfarms in the NEM = 9175.9242MW according to APVI... AEMO say there is only 5897MW existing  
    #(Total windfarm capacty for each polygon )
    result = []
    if gentype == PV1Axis:
        cfg = configfile.get('generation', 'pv1axis-trace')
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=pv_limit[1],
                                label=f'polygon {1} PV'))
        result.append(gentype(2, 0, cfg, 2 - 1,
                                build_limit=pv_limit[2],
                                label=f'polygon {2} PV'))   
        result.append(gentype(3, 50, cfg, 3 - 1,
                                build_limit=pv_limit[3],
                                label=f'polygon {3} PV')) 
        result.append(gentype(4, 879.01, cfg, 4 - 1,
                                build_limit=pv_limit[4],
                                label=f'polygon {4} PV'))
        result.append(gentype(5, 0, cfg, 5 - 1,
                                build_limit=pv_limit[5],
                                label=f'polygon {5} PV'))
        result.append(gentype(6, 254.47, cfg, 6 - 1,
                                build_limit=pv_limit[6],
                                label=f'polygon {6} PV'))   
        result.append(gentype(7, 148, cfg, 7 - 1,
                                build_limit=pv_limit[7],
                                label=f'polygon {7} PV')) 
        result.append(gentype(8, 0, cfg, 8 - 1,
                                build_limit=pv_limit[8],
                                label=f'polygon {8} PV'))                                             
        result.append(gentype(9, 0, cfg, 9 - 1,
                                build_limit=pv_limit[9],
                                label=f'polygon {9} PV')) 
        result.append(gentype(10, 0, cfg, 10 - 1,
                                build_limit=pv_limit[10],
                                label=f'polygon {10} PV')) 
        result.append(gentype(11, 149.38, cfg, 11 - 1,
                                build_limit=pv_limit[11],
                                label=f'polygon {11} PV'))  
        result.append(gentype(12, 0, cfg, 12 - 1,
                                build_limit=pv_limit[12],
                                label=f'polygon {12} PV')) 
        result.append(gentype(13, 0, cfg, 13 - 1,
                                build_limit=pv_limit[13],
                                label=f'polygon {13} PV')) 
        result.append(gentype(14, 0, cfg, 14 - 1,
                                build_limit=pv_limit[14],
                                label=f'polygon {14} PV'))  
        result.append(gentype(15, 0, cfg, 15 - 1,
                                build_limit=pv_limit[15],
                                label=f'polygon {15} PV'))
        result.append(gentype(16, 579, cfg, 16 - 1,
                                build_limit=pv_limit[16],
                                label=f'polygon {16} PV'))
        result.append(gentype(17, 1189.5, cfg, 17 - 1,
                                build_limit=pv_limit[17],
                                label=f'polygon {17} PV'))
        result.append(gentype(18, 0, cfg, 18 - 1,
                                build_limit=pv_limit[18],
                                label=f'polygon {18} PV'))
        result.append(gentype(19, 0, cfg, 19 - 1,
                                build_limit=pv_limit[19],
                                label=f'polygon {19} PV'))
        result.append(gentype(20, 0, cfg, 20 - 1,
                                build_limit=pv_limit[20],
                                label=f'polygon {20} PV'))
        result.append(gentype(21, 0, cfg, 21 - 1,
                                build_limit=pv_limit[21],
                                label=f'polygon {21} PV'))
        result.append(gentype(22, 0, cfg, 22 - 1,
                                build_limit=pv_limit[22],
                                label=f'polygon {22} PV'))
        result.append(gentype(23, 291, cfg, 23 - 1,
                                build_limit=pv_limit[23],
                                label=f'polygon {23} PV'))
        result.append(gentype(24, 301, cfg, 24 - 1,
                                build_limit=pv_limit[24],
                                label=f'polygon {24} PV'))
        result.append(gentype(25, 0, cfg, 25 - 1,
                                build_limit=pv_limit[25],
                                label=f'polygon {25} PV'))
        result.append(gentype(26, 270, cfg, 26 - 1,
                                build_limit=pv_limit[26],
                                label=f'polygon {26} PV'))
        result.append(gentype(27, 0, cfg, 27 - 1,
                                build_limit=pv_limit[27],
                                label=f'polygon {27} PV'))
        result.append(gentype(28, 53.76, cfg, 28 - 1,
                                build_limit=pv_limit[28],
                                label=f'polygon {28} PV'))
        result.append(gentype(29, 110, cfg, 29 - 1,
                                build_limit=pv_limit[29],
                                label=f'polygon {29} PV'))
        result.append(gentype(30, 661, cfg, 30 - 1,
                                build_limit=pv_limit[30],
                                label=f'polygon {30} PV'))
        result.append(gentype(31, 134, cfg, 31 - 1,
                                build_limit=pv_limit[31],
                                label=f'polygon {31} PV'))
        result.append(gentype(32, 149.25, cfg, 32 - 1,
                                build_limit=pv_limit[32],
                                label=f'polygon {32} PV'))
        result.append(gentype(33, 1177, cfg, 33 - 1,
                                build_limit=pv_limit[33],
                                label=f'polygon {33} PV'))
        result.append(gentype(34, 693.56, cfg, 34 - 1,
                                build_limit=pv_limit[34],
                                label=f'polygon {34} PV'))
        result.append(gentype(35, 358, cfg, 35 - 1,
                                build_limit=pv_limit[35],
                                label=f'polygon {35} PV'))
        result.append(gentype(36, 42.205, cfg, 36 - 1,
                                build_limit=pv_limit[36],
                                label=f'polygon {36} PV'))
        result.append(gentype(37, 55, cfg, 37 - 1,
                                build_limit=pv_limit[37],
                                label=f'polygon {37} PV'))
        result.append(gentype(38, 239, cfg, 38 - 1,
                                build_limit=pv_limit[38],
                                label=f'polygon {38} PV'))
        result.append(gentype(39, 143, cfg, 39 - 1,
                                build_limit=pv_limit[39],
                                label=f'polygon {39} PV'))
        result.append(gentype(40, 0, cfg, 40 - 1,
                                build_limit=pv_limit[40],
                                label=f'polygon {40} PV'))
        result.append(gentype(41, 0, cfg, 41 - 1,
                                build_limit=pv_limit[41],
                                label=f'polygon {41} PV'))
        result.append(gentype(42, 0, cfg, 42 - 1,
                                build_limit=pv_limit[42],
                                label=f'polygon {42} PV'))
        result.append(gentype(43, 0, cfg, 43 - 1,
                                build_limit=pv_limit[43],
                                label=f'polygon {43} PV'))                                         
    elif gentype == Wind:
        cfg = configfile.get('generation', 'wind-trace')
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(2, 0, cfg, 2 - 1,
                                build_limit=wind_limit[2],
                                label=f'polygon {2} wind'))
        result.append(gentype(3, 0, cfg, 3 - 1,
                                build_limit=wind_limit[3],
                                label=f'polygon {3} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        result.append(gentype(1, 0, cfg, 1 - 1,
                                build_limit=wind_limit[1],
                                label=f'polygon {1} wind'))
        
    return result


def re100SWH(context):
    """100% renewable electricity with only PV, Wind, Hydro. ERC Addition"""
    result = []
    # The following list is in merit order.
    for g in [PV1Axis, Wind, PumpedHydro, Hydro]:
        if g == PumpedHydro:
            result += [h for h in _hydro() if isinstance(h, PumpedHydro)]
        elif g == Hydro:
            result += [h for h in _hydro() if not isinstance(h, PumpedHydro)]
        elif g in [PV1Axis, Wind]:
            result += _existingSolarWind(g)
        else:
            raise ValueError('unhandled generator type')  # pragma: no cover
    context.generators = result
    

def re100SWH_batteries(context):
    """Takes SWH and adds battery."""
    re100SWH(context)
    # discharge between 6pm and 6am daily
    hrs = list(range(0, 7)) + list(range(18, 24))
    battery = Battery(4, 1000, 1500, discharge_hours=hrs, rte = 1)
    #context.generators.insert(0, battery)
    context.generators = [battery] + context.generators


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
                    're100SWH': re100SWH, 
                    're100SWH+batteries': re100SWH_batteries,
                    're100+dsp': re100_dsp,
                    're100-nocst': re100_nocst,
                    'replacement': replacement}
