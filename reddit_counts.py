import os
import requests
import json
import datetime
import time
import itertools
import sys
import pandas as pd

END_TIMESTAMP = int(datetime.datetime(2021, 1, 1).timestamp())
# Get all comments before 2021. This can be set to a later date to, e.g. fetch only comments for 2020
EARLIEST_TIMESTAMP = 0

# Max value of the limit param. cf. https://www.reddit.com/r/pushshift/comments/ih66b8/difference_between_size_and_limit_and_are_they/
MAX_RESULTS_PER_REQUEST = 100

# If we get a response code other than 200, we will retry up to this many times,
# waiting 2, 4, 8... seconds between attempts
MAX_RETRIES = 8

# Cap to avoid spending huge amounts of time on the most common compounds (e.g. douchebag)
MAX_REQUESTS_PER_TERM = 400

CACHE_DIR = 'comment_data'

# This script draws some inspiration from https://github.com/Watchful1/Sketchpad/blob/master/postDownloader.py

# Categorizations aren't being used anywhere currently, but at least makes it easier to keep track of what's there.
prefixes_by_cat = dict(
        bodyfluid='cum,snot,spit,jizz,piss,puke,spunk',
        scatological='fart,shit,crap,poop,poo,turd',
        privateparts='butt,ass,bum,dick,cock,twat,knob,pecker,prick,pussy,tit',
        other_expletive='fuck,wank',
        # removed fat - few hits, mostly on fatass, a few on fatboy, fathead, fatfuck
        insult_adj='dumb,lame',
        sexuality='gay,homo,queer,fag',
        insult_noun='douche,jerk,dork,creep,dip,nazi,geek,slut,whore,bitch',
        # Removed cheese - too many false +ves
        food='lard',
        base_substance='scum,slime,dirt,skeeze,sleaze',
        animal='dog,monkey,rat,weasel,bird',
        political='fem,lib,right,soy,trump',
        other='stink',
        # XXX: newly added
        disyllables='bastard,donkey,moron,idiot,loser,harpy,faggot',
)
# (Removed slice as it only got 100 combined hits.)
suffixes_by_cat = dict(
        collection='wad,bag,bucket,sack,ball,splash,pot,pile',
        animal='weasel,monkey,dog,rat,bird,goblin,puffin',
        action='licker,muncher,fucker,sucker',
        person='lord,clown,slut,pirate,bro,nazi,whore,boy,boi,burglar,bandit,bitch',
        # Removing pie - not enough hits
        food='waffle,burger,cake',
        thing='nugget,rag,nozzle,stain,wagon,weed,hat,canoe,boat,stick,socket,trumpet,mitten',
        privateparts='twat,dick,cunt,ass,cock,balls',
        bodypart='face,head,nuts,brain,brains,knuckle,mouth,nose,skull',
        bound='tard,oid,ster,azoid,let',
        expletive='fuck,shit,fart',
        other='wit,lib,breath',
)

def flatcats(affixes_by_cat):
    affixes = []
    for cat, affixstring in affixes_by_cat.items():
        affixes += affixstring.split(',')
    # Ensure no dupes
    assert len(set(affixes)) == len(affixes)
    return affixes

prefixes = flatcats(prefixes_by_cat)
suffixes = flatcats(suffixes_by_cat)


COMMENT_ATTR_WHITELIST = set('body,created_utc,permalink,score,subreddit,total_awards_received,author'.split(','))
def shake_comment_data(dat):
    """Given a jsondict of information about a comment, return a copy with only
    the fields we care about saving.
    """
    d = {k:v for k, v in dat.items() if k in COMMENT_ATTR_WHITELIST}
    return d

def load_extant(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def download_comments(term):
    outpath = os.path.join(CACHE_DIR, f'{term}.json')
    comments = load_extant(outpath)
    if len(comments) == 0:
        endpoint = END_TIMESTAMP
    else:
        endpoint = comments[-1]['created_utc'] - 1
    retries = 0
    while len(comments) < MAX_REQUESTS_PER_TERM * MAX_RESULTS_PER_REQUEST:
        url = f"https://api.pushshift.io/reddit/comment/search?limit={MAX_RESULTS_PER_REQUEST}&sort=desc&before={endpoint}&after={EARLIEST_TIMESTAMP}&q={term}"
        response = requests.get(url, headers={'User-Agent': "script by /u/halfeatenscone"})
        time.sleep(1)
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
        comments.extend([shake_comment_data(comm) for comm in results])
        if len(results) < MAX_RESULTS_PER_REQUEST:
            break

        endpoint = results[-1]['created_utc'] - 1

    with open(outpath, 'w') as f:
        json.dump(comments, f, indent=0)

TERMLIMIT = None
if __name__ == '__main__':
    sys.stderr.write(f"Crunching {len(prefixes)} prefixes and {len(suffixes)} suffixes, for a total of {len(prefixes)*len(suffixes)} combinations.\n")
    n = 0
    df = pd.read_csv('counts.csv')
    for pre, post in itertools.product(prefixes, suffixes):
        match = df[(df.pre == pre) & (df.suff == post)]
        assert len(match) in (0, 1)
        if len(match) == 1:
            # Skip any compounds for which we already have data.
            continue
        term = pre + post
        print(f"Dowloading comments for term {term!r}")
        download_comments(term)
        n += 1
        if TERMLIMIT and n >= TERMLIMIT:
            break
