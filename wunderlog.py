#!/usr/bin/env python3
"""
Collect observations and forecast data from Weather Underground
"""

from datetime import date, datetime, timedelta, timezone
import json
from netrc import netrc
from pathlib import Path
import os

from requests_cache import CachedSession

WUNDERGROUND_API = 'https://api.wunderground.com/api'

# format for days
DAY_FMT = '%Y-%m-%d'
# format for dates (minute-resolution)
DATE_FMT = '%Y-%m-%dT%H-%M'
# hourly prefix
# for minute-resolution records,
# avoiding more-frequent-than-hourly observations
HOURLY_FMT = DATE_FMT[:-2]


def ensure_dir_exists(path):
    if os.path.exists(path):
        return
    else:
        try:
            os.makedirs(path)
        except FileExistsError:
            pass


def json_dump(data, f):
    """consistent json dump"""
    json.dump(data, f, sort_keys=True, indent=1)


def utcnow():
    """timezone-aware utcnow"""
    return datetime.now(tz=timezone.utc)


class Wunderlog():
    """
    Class to capture weather underground history

    api_key should be retrieved from weather underground website
    location should be a weather underground location, e.g. 'Norway/Asker'
    """

    def __init__(self, location, api_key=None, directory='.', cache_kwargs=None):
        if api_key is None:
            api_key = netrc().authenticators('api.wunderground.com')[2]
        self.api_key = api_key
        self.location = location
        self.directory = Path(directory)
        self.loc_dir = self.directory.joinpath(self.location.lower())
        ensure_dir_exists(self.loc_dir)

        if cache_kwargs is None:
            cache_kwargs = {}
        # expire after just under an hour by default
        cache_kwargs.setdefault(
            'expires_after', timedelta(minutes=55))
        cache_kwargs.setdefault(
            'cache_name', str(self.directory.joinpath('cache')))

        self.session = CachedSession(**cache_kwargs)

    def api_request(self, path):
        """Make an API request

        Checks for errors and returns JSON response"""
        path = path.strip('/')
        url = f'{WUNDERGROUND_API}/{self.api_key}/{path}/q/{self.location}.json'
        print(f"Fetching {url.replace(self.api_key, '{key}')}")
        r = self.session.get(url)
        r.raise_for_status()
        body = r.json()
        # API Errors still return 200!
        if body.get('response', {}).get('error'):
            url = url.replace(self.api_key, '{api_key}')
            raise ValueError(
                f"{url}: {body['response']['error']}"
            )

        return body

    def parse_date(self, date):
        return datetime(
            year=int(date['year']),
            month=int(date['mon']),
            day=int(date['mday']),
            hour=int(date['hour']),
            minute=int(date['min']),
        )

    def get_day(self, day=None):
        """Download daily observation data"""
        daily_dir = self.loc_dir.joinpath('daily')
        ensure_dir_exists(daily_dir)
        if day is None:
            day = date.today() - timedelta(days=1)
        daily_fname = daily_dir.joinpath(
            f"{day.strftime(DAY_FMT)}.json"
        )
        if daily_fname.exists():
            print(f"Already have observations for {daily_fname}")
            return

        # fetch the data
        history = self.api_request(day.strftime('history_%Y%m%d'))['history']
        dailysummary = history['dailysummary'][0]

        # save daily summary
        with open(daily_fname, 'w') as f:
            # check the date!
            json_dump(dailysummary, f)

        # save individual observations, as well
        obs_dir = self.loc_dir.joinpath('observations')
        ensure_dir_exists(obs_dir)
        for observation in history['observations']:
            dt = self.parse_date(observation['date'])
            date_str = dt.strftime(DATE_FMT)
            fname = obs_dir.joinpath(date_str + '.json')
            with fname.open('w') as f:
                json_dump(observation, f)

    def get_history(self, max_days=7):
        """Get a number of days of history"""
        today = date.today()
        for i in range(max_days, 0, -1):
            self.get_day(today - timedelta(days=1))

    def get_forecast(self, kind='daily'):
        if kind == 'daily':
            key = 'forecast10day'
            dirname = 'forecast'

            def extract(r):
                return r['forecast']['simpleforecast']['forecastday']

        elif kind == 'hourly':
            key = 'hourly10day'
            dirname = 'forecast_hourly'

            def extract(r):
                return r['hourly_forecast']

        else:
            raise ValueError(f"forecast kind must be 'hourly' or 'daily', not {kind:r}")

        fcast_dir = self.loc_dir.joinpath(dirname)
        ensure_dir_exists(fcast_dir)
        now = utcnow()
        hour_prefix = now.strftime(HOURLY_FMT)
        for fname in os.listdir(fcast_dir):
            if fname.startswith(hour_prefix):
                print(f"already have {fcast_dir.joinpath(fname)}")
                return
        fname = fcast_dir.joinpath(now.strftime(DATE_FMT) + '.json')
        r = self.api_request(key)
        fcast = extract(r)
        with fname.open('w') as f:
            json_dump(fcast, f)

    def collect(self):
        self.get_day()
        self.get_forecast('daily')
        self.get_forecast('hourly')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('location', help="The location, e.g. Norway/Asker")
    # add args for data-dir, etc.
    opts = parser.parse_args()
    W = Wunderlog(opts.location)
    W.collect()
