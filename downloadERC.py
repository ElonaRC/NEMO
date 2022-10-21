import requests
import time
import pandas as pd
import os
import glob
import csv
from pathlib import Path
import fnmatch


class RenewablesNinja():

    TOKEN = ''
    URLBASE = 'https://www.renewables.ninja/api/data'
    session = requests.Session()

    headers = {
        'Authorization': f'Token {TOKEN}'
    }

    def __init__(self, latlong, daterange):

        if not isinstance(latlong, tuple) and len(latlong) != 2:
            raise ValueError("latlong must be a pair (tuple)")

        if not isinstance(daterange, tuple) and len(daterange) != 2:
            raise ValueError("daternage must be a pair (tuple)")

        self.latitude, self.longitude = latlong

        self.params = {
            'lat': self.latitude,
            'lon': self.longitude,
            # verify date range
            'date_from': daterange[0],
            'date_to': daterange[1],
            'dataset': 'merra2',
            'capacity': 1.0,
            'format': 'csv'
        }

    @classmethod
    def fetch(cls, url, params):
        """Fetch the CSV data from the web server and parse it."""
        resp = cls.session.get(url, headers=cls.headers, params=params)
        if not resp.ok:
            raise RuntimeError(f'HTTP {resp.status_code}: {url}')
        for i in range(90, 0, -10):
            print(f"Sleeping for {i} seconds")
            time.sleep(10)
        return resp.text


class NinjaPV(RenewablesNinja):
    def __init__(self, latlong, daterange, axes, azimuth=180,
                 tilt=None):
        """
        Construct a PV system with trace data from Renewables.ninja.

        latlong: The location must be specified as a latitude/longitude tuple.
        daterange: The date range must be specified as a tuple.
        axes: Whether the system is fixed, single-axis or dual-axis tracking.
        azimuth: The azimuth angle of the system. 180 = to the equator.
        tilt: The tilt of the PV modules (default is latitude angle).
        """
        RenewablesNinja.__init__(self, latlong, daterange)

        if axes not in [0, 1, 2]:
            raise ValueError("values: 0, 1 (single axis) or 2 (double axis)")
        self.tilt = abs(self.latitude) if tilt is None else tilt
        assert 0 <= self.tilt <= 90, self.tilt

        # PV specific parameters
        for key, value in (('system_loss', 0.1), ('tracking', axes),
                           ('tilt', self.tilt), ('azim', azimuth)):
            self.params[key] = value

    def download(self, filename):
        print(filename)
        try:
            data = self.fetch(self.URLBASE + '/pv', self.params)
            if 'North' in filename:
                with open(os.path.join('/Users/elonarey-costa/Documents/phdCode/NEMO/data/PVTraceNorthRN',filename), 'w') as fhandle:
                    fhandle.write(data)
            else:
                with open(os.path.join('/Users/elonarey-costa/Documents/phdCode/NEMO/data/PVTraceWestRN',filename), 'w') as fhandle:
                    fhandle.write(data)
        except RuntimeError:
            pass

class NinjaWind(RenewablesNinja):
    def __init__(self, latlong, daterange, machine, height):
        """
        Construct a wind turbine with trace data from Renewables.ninja.

        latlong: The location must be specified as a latitude/longitude tuple.
        daterange: The date range must be specified as a tuple.
        machine: The wind turbine model must match those listed on the website.
        height: The hub height in metres.
        """
        RenewablesNinja.__init__(self, latlong, daterange)

        assert 10 <= height <= 150

        # Wind specific parameters
        for key, value in (('turbine', machine),
                           ('height', height)):
            self.params[key] = value

    def download(self, filename):
        print(filename)
        try:
            data = self.fetch(self.URLBASE + '/wind', self.params)
            with open(os.path.join('/Users/elonarey-costa/Documents/phdCode/NEMO/data/WindTraceRN',filename), 'w') as fhandle:
                fhandle.write(data)
        except RuntimeError:
            pass


# EXAMPLE CODE

# You'll need a list of latlongs (tuples) here, indexed by polygon.
#latlongs = [None, (-16.84,	145.68),(-19.49,	142.24)]

latlongs = [None,  # no polygon zero
            (-16.84,	145.68), (-19.49,	142.24),(-19.80,	144.74),(-20.39,	148.09),(-22.19,	142.39),(-22.33,	145.8),
            (-23.24,	150.37),(-24.83,	142.52),(-24.87,	145.51),(-24.85,	148.32),(-25.21,	152.04),
            (-27.54,	136.56),(-27.52,	139.46),(-27.49,	142.6),(-27.48,	145.85),(-27.48,	149.06),
            (-27.51,	152.64),(-30.20,	133.19),(-30.20,	136.56),(-30.19,	139.48),(-30.02,	142.61),
            (-30.36,	145.7),(-30.38,	148.63),(-30.69,	152.23),(-32.34,	133.04),(-33.80,	136.23),
            (-32.63,	139.47),(-32.17,	142.53),(-32.89,	145.28),(-32.93,	147.71),(-33.31,	150.94),
            (-35.88,	139.52),(-34.28,	142.45),(-34.84,	145.01),(-35.13,	146.9),(-35.81,	149.66),
            (-37.06,	142.35),(-38.13,	147.57),(-37.94,	144.87),(-40.91,	144.98),(-40.82,	147.9),
            (-42.95,	145.29),(-42.95,	147.71)
            ]


NOTRACKING = 0
SINGLEAXIS = 1
DUALAXIS = 2

#Extracts the files for each polygon for that year. 
for year in [('2009-01-01', '2009-12-31'), ('2008-01-01', '2008-12-31'), ('2007-01-01', '2007-12-31'), ('2006-01-01', '2006-12-31')]:  # etc
    for poly in range(1, 44):
        # north facing, latitutde tilt
        pv = NinjaPV(latlongs[poly], year, SINGLEAXIS)
        pv.download(f'PV-{poly}-{year[0]}-{year[1]}-North.csv')

        # west facing, latitude + 15
        AZIM = 270
        tilt = int(abs(latlongs[poly][0]) + 15)
        pv2 = NinjaPV(latlongs[poly], year, SINGLEAXIS, AZIM, tilt)
        pv2.download(f'PV-{poly}-{year[0]}-{year[1]}-West.csv')

        MACHINE = 'Vestas V90 2000'
        HEIGHT = 100
        wind = NinjaWind(latlongs[poly], year, MACHINE, HEIGHT)
        wind.download(f'Wind-{poly}-{year[0]}-{year[1]}.csv')


