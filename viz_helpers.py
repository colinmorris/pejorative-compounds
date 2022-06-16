import os
import pandas as pd
import itertools

from reddit_counts import prefixes, suffixes

WIKT_FNAME = 'wikt.csv'

#DEFAULT_COUNT_FNAME = 'all_reddit_counts.tsv'
DEFAULT_COUNT_FNAME = 'counts.csv'

def load_df(fname=DEFAULT_COUNT_FNAME, wikt=True):
    sep = '\t' if fname.endswith('.tsv') else ','
    df = pd.read_csv(fname, sep=sep)
    if wikt:
        wdf = pd.read_csv(WIKT_FNAME)
        df = df.merge(wdf)
    return df

def all_compounds():
    return [pre+suff for (pre, suff) in itertools.product(prefixes, suffixes)]

BLOGDIR = os.path.expanduser("~/src/colinmorris.github.com/assets/compound_curses/")
def savefig(fig, name, **kwargs):
    if '.' not in name:
        name += '.png'
    path = os.path.join(BLOGDIR, name)
    # Default to doubling dpi to make these less squinty
    kws = kwargs.copy()
    if 'dpi' not in kwargs:
        kws['dpi'] = fig.dpi * 2
    fig.savefig(path, **kws)
