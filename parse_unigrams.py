import itertools
import sys
import pandas as pd

from reddit_counts import prefixes, suffixes

all_combos = itertools.product(prefixes, suffixes)
# Map compound strings to (pre, suff) tuples
compound_to_parts = {
        (pre+suff): (pre, suff)
        for pre, suff in all_combos
}
def split_compound(token):
    return compound_to_parts[token]

def parse_counts(countstrings):
    count = 0
    for s in countstrings:
        year, n, volumes = s.split(',')
        count += int(n)
    return count

class PosError(Exception):
    pass

def parse_line(line):
    parts = line.split('\t')
    token = parts[0]
    if '_' in token:
        raise PosError()
    pre, suff = split_compound(token)
    count = parse_counts(parts[1:])
    return pre, suff, count

# dataframe with wiktionary flags
WIKI_FNAME = 'wikt_2020.csv'

if __name__ == '__main__':
    try:
        fname = sys.argv[1]
    except IndexError:
        fname = 'compound_unigrams.tsv'
    
    # Read in existing df, including wiktionary stuff, and reset counts to 0.
    df = pd.read_csv(WIKI_FNAME)
    df['count'] = 0

    with open(fname) as f:
        for line in f:
            try:
                pre, suff, count = parse_line(line)
            except PosError:
                # ignoring tokens tagged with a part of speech
                continue
            df.loc[(df.pre == pre) & (df.suff == suff), 'count'] = count
    df.to_csv('ngram_counts.csv', index=False)

