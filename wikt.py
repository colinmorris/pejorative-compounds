import sys
import time
import itertools

from wiktionaryparser import WiktionaryParser
import pandas as pd

from reddit_counts import prefixes, suffixes

parser = WiktionaryParser()
"""
Seems like this returns a pseudo-Json object, in the form of a 
list of dictionaries, each dict having keys like
- pronunciations
- definitions
- etymology
If the word doesn't exist, then it returns the following empty shell:
[{'etymology': '',
  'definitions': [],
  'pronunciations': {'text': [], 'audio': []}}]
"""
fetch = lambda w: parser.fetch(w)

def exists(w):
    # Special case: we'll search for capitalized versions of "trump-" prefixed terms.
    if w.startswith('trump'):
        w = w.capitalize()
    dat = fetch(w)
    if len(dat) != 1:
        sys.stderr.write(f"WARNING: Got unexpected results length of {len(dat)} for term {w}.\n")
        # Seems like length 0 means there's a page but no English definitions, and > 1 might
        # correspond to the case of multiple etymologies?
        if len(dat) == 0:
            return False
    return len(dat[0]['definitions']) > 0

def checkrow(row):
    word = row.pre + row.suff
    return exists(word)

def add_wikt_column(df):
    """Add a boolean column to given df indicating whether given term has a wiktionary entry.
    """
    col_name = 'wikt'
    assert col_name not in df.columns
    df.loc[:, col_name] = df.apply(checkrow, axis=1)

def main():
    t0 = time.time()
    try:
        fname = sys.argv[1]
    except IndexError:
        print(f"Usage: {sys.argv[0]} INPUT_CSV [OUT_FNAME]")
        sys.exit(1)
    try:
        outname = sys.argv[2]
    except IndexError:
        outname = 'wikt.csv'

    sep = '\t' if fname.endswith('.tsv') else ','
    df = pd.read_csv(fname, sep=sep)
    add_wikt_column(df)
    df.to_csv(outname, index=False)
    elapsed = time.time() - t0
    print(f"Finished in {elapsed:.1f} seconds.")

def main2():
    extant_fname = 'wikt.csv'
    df = pd.read_csv(extant_fname)
    # Header
    print("pre,suff,wikt")
    for (pre, suff) in itertools.product(prefixes, suffixes):
        extant = df.loc[(df.pre == pre) & (df.suff == suff)]
        assert len(extant) <= 1
        if len(extant) == 1 and pre != 'trump': # XXX
            wikt = extant.iloc[0].wikt
        else:
            term = pre + suff
            sys.stderr.write(f"Fetching term {term}\n")
            wikt = exists(term)
        print(f"{pre},{suff},{wikt}")

if __name__ == '__main__':
    main()
    #main2()
