import requests
import time
import sys
import json
import random
import datetime
import pandas as pd
import numpy as np
import os

import viz_helpers
from reddit_counts import shake_comment_data

"""
Have approx 15 years to sample over (though very little data in first few years)
Could do something like...
for each year
    randomly select 30 days
    for each day
        randomly select a 10 second interval
        count all comments from that interval

multiply the result by (24*60*60/10) * (365/30)

Could use existing comment_data as a testing ground to get some estimate
of the error bars on this sort of sampling method. Use a term that's just
below the ceiling (e.g. slimeball, with 33k), and repeat the sampling a
few times with different seeds. See how close our estimate is to the true
value.
"""

DAYS_PER_YEAR = 30

# Approx date of earliest Reddit comments indexed by pushshift 
FIRST_YEAR = 2006
LAST_YEAR = 2020

SECONDS_PER_DAY = 24 * 60 * 60

# If we get a response code other than 200, we will retry up to this many times,
# waiting 2, 4, 8... seconds between attempts
MAX_RETRIES = 8
# Max value of the limit param. cf. https://www.reddit.com/r/pushshift/comments/ih66b8/difference_between_size_and_limit_and_are_they/
MAX_RESULTS_PER_REQUEST = 100

def comments_from_interval(term, start, end, limit=None):
    retries = 0
    comments = []
    while limit is None or len(comments) < limit:
        url = f"https://api.pushshift.io/reddit/comment/search?limit={MAX_RESULTS_PER_REQUEST}&sort=asc&before={end+1}&after={start-1}&q={term}"
        response = requests.get(url, headers={'User-Agent': "script by /u/halfeatenscone"})
        if response.status_code != 200:
            retries += 1
            if retries > MAX_RETRIES:
                sys.stderr.write(f"WARNING: aborting term {term} after max retries for url {url}\n")
                break
            wait = 2**retries
            time.sleep(wait)
            continue
        dat = response.json()
        results = dat['data']
        comments += results
        if len(results) < MAX_RESULTS_PER_REQUEST:
            break
        # If we got 100 results, then keep going, starting from after the
        # last comment
        start = results[-1]['created_utc'] + 1
        time.sleep(1)
    time.sleep(1)
    return comments

def get_intervals(seed=1337):
    """Return a list of inclusive (start, end) utc timestamp tuples

    NB: for pushshift API, "after" and "before" are non-inclusive (as you
    might expect).
    """
    np.random.seed(seed)
    intervals = []
    for year in range(FIRST_YEAR, LAST_YEAR+1):
        base_date = datetime.datetime(year, 1, 1)
        leap_year = year % 4 == 0
        possible_day_offsets = range(365 + int(leap_year))
        day_offsets = np.random.choice(possible_day_offsets, DAYS_PER_YEAR, replace=False)
        for offset in day_offsets:
            date = base_date + datetime.timedelta(days=int(offset))
            # make sure interval doesn't bleed into next day
            #second_offset = random.randint(0, SECONDS_PER_DAY - INTERVAL_SIZE_SECONDS)
            #dt = date + datetime.timedelta(seconds=second_offset)
            start_timestamp = int(date.timestamp())
            interval = (start_timestamp, start_timestamp + SECONDS_PER_DAY-1)
            intervals.append(interval)
    return intervals

CACHE_DIR = 'sampled_comment_data'
def fetch_sampled_comments(term, intervals):
    outpath = os.path.join(CACHE_DIR, f'{term}.json')
    assert not os.path.exists(outpath)
    comments = []
    for start, end in intervals:
        comms = comments_from_interval(term, start, end)
        comments += [shake_comment_data(comm) for comm in comms]
    with open(outpath, 'w') as f:
        json.dump(comments, f, indent=0)

def main():
    """Download sampled data for terms with recorded counts exceeding our
    cap of 40k.
    """
    ints = get_intervals(seed=1337)
    df = viz_helpers.load_df('raw_reddit_counts.csv', wikt=False)
    cap = 40000
    exceeders = df[df['count'] >= cap].apply(lambda row: row.pre+row.suff, axis=1)
    sys.stderr.write(f'Fetching sampled comments for {len(exceeders)} terms.\n')
    for term in exceeders:
        sys.stderr.write(term + '\n')
        fetch_sampled_comments(term, ints)

if __name__ == '__main__':
    main()
