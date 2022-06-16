## Data pipeline

### 1. download comments

Run `reddit_counts.py` to download comment data for all combinations of prefixes and suffixes specified in the script using the Pushshift API.

Comments will be saved as arrays of json objects in `comment_data/`, with one file per compound (e.g. `comment_data/poophead.json`). Comment arrays are sorted by date, ascending.

There is a cap on the number of comments that will be downloaded per term (default 40k, configurable via `MAX_REQUESTS_PER_TERM`). This is because we can only download comments 100 at a time, and downloading all comments for very high-frequency terms (e.g. *dumbass*) would take many hours. We deal with terms that hit the cap in step 2.

### 1.5 compute preliminary counts

To get preliminary counts based on the data downloaded in this step, run:

```
python compute_counts.py --raw > raw_reddit_counts.csv
```

This will output a csv mapping compounds to raw counts, which are simply the number of comments in the corresponding json file. e.g. `poophead,100` means that the array of comments at `comment_data/poophead.json` has length 100.

### 2. download sampled comments for high-frequency compounds

Run `sampled_counts.py` (with the `main()` subroutine). For each term in `raw_reddit_counts.csv` (created in step 1.5) which hit the cap on max comments downloaded, it will download a random *sample* of comments containing that term. Sampling is done by date - we download comments for 30 randomly chosen days out of each year. Downloaded comments are saved in a separate directory from the main comment data, `sampled_comment_data`.

### 3. compute final counts, with sampling and filtering

Run

```
python compute_counts.py > counts.csv
```

For terms that were sampled (in step 3), the script will calculate an estimated total comment count based on the sampling rate. For other terms, it will do a count over all comment data.

In both cases, the script will also do some filtering of comments that should not be counted for various reasons, including:
- the term only appears as part of a URL, or a reference to a Reddit username or subreddit (the pushshift API does some fuzzy matching, such that the query "ratwaffle" will match tokens like "/u/ratwaffle" or "www.yelp.com/ratwaffle-house")
- the comment is a known "copypasta" (in particular, there are a couple commonly reposted comments that consist entirely of lists of dirty words - these have an especially distortionary effect on rare terms which appear in the list)

### 4. record wiktionary presence

Run `wikt.py` to generate the file `wikt.csv`, which will record, for each compound, whether there is a corresponding English dictionary definition at en.wiktionary.org.

This will make one request per row in `counts.csv`, taking around 20 minutes.

## Guide to IPython notebooks

`viz_helpers.py` is a module of helper functions used across these notebooks. `heatmap.py` has helpers specific to making heatmap affix-affix heatmap visualizations.

Main notebooks:
- `affixes.ipynb`: generates the affix 'flexibility' plots using collision probability and Shannon entropy. Also some other by-affix visualizations not used in writeup.
                   NB: some of these take a while to generate because they use adjust_text to jiggle around markers/labels
- `minimaps.ipynb`: generates the mini-matrices used in writeup for comparing narrow groups of related affixes (e.g. butt vs ass vs bum)
- `monoword.ipynb`: experiments with comments consisting of only a compound pejorative and nothing else
- `subreddits.ipynb`: very limited experiments with subreddit dimension
- `viz.ipynb`: main heatmap visualization experiments
- `wikt.ipynb`: charts/data relating to questions of most popular terms lacking a wikt entry and least popular terms having a wikt entry
- `zipf.ipynb`: looking at distribution of counts, Zipf visualization of log-frequency vs. log-rank
- 

The following notebooks are early experiments or explorations that have been obsoleted by later developments:
- `compounds.ipynb`: a few exploratory early matrix visualizations. Predates helper modules.
- `extrapolation.ipynb`: early experiments with filtering comments and computing extrapolated counts for capped compounds. Has some interesting CDF visualizations showing popularity of terms over time. Might be worth developing that theme more.
- `flexibility.ipynb`: superseded by affixes.ipynb
- `jan.ipynb`: ???
- `wikt_obsolete.ipynb`: experiments with Wiktionary API. Led to development of `wikt.py` script.

## Guide to data files

`counts.csv` seems to be most recent data file. Has the most rows, so.

`wikt.csv` seems to be most up-to-date data file for wikt presence (but need to rerun)

Looks like data was collected in Jan 2021. `reddit_counts.py` sets an end limit of 1/1/2021, so counts should be cumulative through 2020.

`suffixes.csv` and `prefixes.csv` are dataframes generated in the `affixes.ipynb` notebook. They have some data associated with each affix, such as measures of flexibility (collision probability, Shannon entropy), total frequency, most frequent counterpart, and the proportion of all occurrences comprised by that most-frequent combination.

## Ngram stuff

`compound_unigrams.tsv` has Google Books ngram data for compounds. There is a slight discrepancy in terms of compound coverage with the latest version of `counts.csv` and related files, since some affixes were added and removed since the ngram data was collected.

`parse_unigrams.py` takes that file as input and crunches the year dimension to create `ngram_counts.csv`, which has the same format as `counts.csv` and `wikt.csv`.
