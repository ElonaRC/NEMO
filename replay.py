# Copyright (C) 2012, 2013, 2014 Ben Elliston
# Copyright (C) 2014, 2015 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Replay NEM runs from a text file of generators."""
import argparse
import json
import re
import numpy as np

import costs
import configfile as cf
import nem
import scenarios
import utils

np.set_printoptions(precision=3)

parser = argparse.ArgumentParser(description='Bug reports to: nemo-devel@lists.ozlabs.org')
parser.add_argument("-f", type=str, help='replay file', required=True)
parser.add_argument("-d", "--demand-modifier", type=str, action="append", help='demand modifier [default: unchanged]')
parser.add_argument("--no-legend", action="store_false", help="hide legend")
parser.add_argument("-t", "--transmission", action="store_true", help="show region exchanges [default: False]")
parser.add_argument("-v", action="count", help='verbose mode')
parser.add_argument("-x", action="store_true", help='producing a balancing plot')
parser.add_argument("--nsp-limit", type=float, default=cf.get('limits', 'nonsync-penetration'),
                    help='Non-synchronous penetration limit [default: %s]' %
                    cf.get('limits', 'nonsync-penetration'))
parser.add_argument("--spills", action="store_true", help='plot spills')
args = parser.parse_args()


def set_generators(chromosome):
    """Set the generator list from the chromosome."""
    i = 0
    for gen in context.generators:
        for (setter, min_cap, max_cap) in gen.setters:
            # keep parameters within bounds
            newval = max(min(chromosome[i], max_cap), min_cap)
            setter(newval)
            i += 1
    # Check every parameter has been set.
    assert i == len(chromosome), '%d != %d' % (i, len(chromosome))


def run_one(chromosome):
    """Run a single simulation."""
    context.costs = costs.AETA2013_2030Mid(0.05, 1.86, 11, 27)
    context.costs.carbon = 0
    set_generators(chromosome)
    context.verbose = args.v > 1
    if args.transmission:
        context.track_exchanges = 1
    nem.run(context)
    context.verbose = args.v > 0
    print context
    if args.transmission:
        x = context.exchanges.max(axis=0)
        print np.array_str(x, precision=1, suppress_small=True)
        f = open('results.json', 'w')
        json.dump(x.tolist(), f)
        f.close()


context = nem.Context()
context.nsp_limit = args.nsp_limit
assert context.nsp_limit >= 0 and context.nsp_limit <= 1, \
    "NSP limit must be in the interval [0,1]"

# Apply each demand modifier in the order given on the command line.
if args.demand_modifier is not None:
    for arg in args.demand_modifier:
        scenarios.demand_switch(arg)(context)

capacities = []
replayfile = open(args.f)
for line in replayfile:
    if re.search(r'^\s*$', line):
        continue
    if re.search(r'^\s*#', line):
        print line,
        continue
    if not re.search(r'^\s*[\w\-\+]+:\s*\[.*\]\s*.?$', line):
        print 'skipping malformed input:', line
        continue
    m = re.match(r'^\s*([\w\-\+]+):\s*\[(.*)\]\s*.?$', line)
    scenario = m.group(1)
    print 'scenario', scenario
    capacities = m.group(2).split(',')
    scenarios.supply_switch(scenario)(context)
    capacities = [float(elt) for elt in capacities]  # str -> float
    run_one(capacities)
    print

    if args.x:  # pragma: no cover
        utils.plot(context, spills=args.spills, showlegend=args.no_legend)
