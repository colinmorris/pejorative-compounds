Experiment in collecting and analysing data on the frequencies of compound insults - e.g. *butthead*, *dirtwad*, *weaselboy* - in Reddit comments. Writeup forthcoming.

Warning: this repository contains language that some readers may find **very offensive**, including slurs.

There are three main ingredients in this repo:
- `counts.csv`, a dataset mapping ~4,800 compound pejoratives to the number of Reddit comments containing that compound. (`wikt.csv` has the same format with a column recording whether the term has an entry in Wiktionary)
- various Python scripts used to generate this dataset. This process is documented in the "Data pipeline" section below, though you probably don't need to run these unless you want to expand the dataset with a different set of affixes or time range.
- various IPython notebooks exploring and visualizing the dataset (See "Guide to IPython notebooks" section below)

## Overview

I manually curated lists of around 70 prefixes and 70 suffixes (with some overlap between them) which could plausibly be used to form a variety of pejorative compounds. These lists can be found in `reddit_counts.py`.

For each of the ~70x70 possible A+B compounds from the product of these lists, I used the Pushshift API to collect comments containing that compound. I then applied some data cleaning steps and heuristics to estimate the number of comments using that term on Reddit up to the end of 2020.

### Affix selection

The process for selecting the set of prefixes and suffixes to combine was pretty unscientific. I mostly drew inspiration from scanning the ["English derogatory terms" category on Wiktionary](https://en.wiktionary.org/wiki/Category:English_derogatory_terms). I aimed to find affixes which were both frequent and productive (i.e. not limited to just a handful of fixed combinations).

As future work, it would be interesting to explore some sort of semi-supervised method of generating affixes. For example, we could start with a small set of "obvious" affixes (e.g. *shit-*, *fuck-*, *butt-*, *-face*, *-head*, *-wad*) and iteratively expand the set by searching for a suffix that best combines with the current set of prefixes (optimizing for, say, sum of log counts) and adding a prefix that best combines with the current set of suffixes.

I was mostly interested in noun-noun compounds, but the suffix list also includes a small number of bound morphemes such as *-oid*, and *-let*.

### Data cleaning

There are two main categories of spurious usage which I aim to filter out (implemented in `compute_counts.py`):

1. "Copypasta". There are some frequently reposted comments consisting of lists of dirty words ([example](https://www.reddit.com/r/copypasta/comments/jmt0xx/every_single_swear_word_i_didnt_write_this_i/)). These have a tendency to hugely inflate the counts for rare terms. We attempt to exclude them by a) Searching for the presence of substrings that distinctly identify some specific copypastas. b) Excluding all comments from the /r/copypasta subreddit.
2. Occurrences as part of a url or mention of a Reddit username ("/u/gayfart") or subreddit ("/r/titbird"). These are included as part of Pushshift's fuzzy matching algorithm, but I filter them out.

### Other false positives

A major confounder not addressed by the cleaning described above is that some of the compounds formed from our affixes are partially or entirely used with a meaning that is literal or non-pejorative. A few examples:

- *spitball*
- *shitstain*
- *stinkweed* (apparently the name for [a number of actual plants](https://en.wikipedia.org/wiki/Stinkweed))
- Some matches which potentially aren't even the right part of speech (*dogpile*, *buttfuck*)

At one point I had the idea of maintaining a blacklist of false positive terms to exclude, but this can't really be done cleanly because there are so many terms that are used with a mix of literal and pejorative meaning (e.g. *shitstain*).

### Dealing with high-frequency terms

Downloading every single comment having a very common compound such as *dumbass* would take a long time and disk space. For very high frequency terms, we estimate their total frequency by extrapolating from some randomly sampled time intervals spaced out over the years. We only use 30 random 10-second intervals per year, which is probably not a very robust sample size, but we use the same intervals across all terms, so any bias is at least applied consistently to all high-frequency terms.

## Data pipeline

### 1. download comments

Run `reddit_counts.py` to download comment data for all combinations of prefixes and suffixes specified in the script using the Pushshift API.

Comments will be saved as arrays of json objects in `comment_data/`, with one file per compound (e.g. `comment_data/poophead.json`). Comment arrays are sorted by date, ascending.

There is a cap for high-frequency terms (default 40k, configurable via `MAX_REQUESTS_PER_TERM`). We'll stop downloading comments for a term when we hit that cap (we'll extrapolate a sampled count for them in step 2).

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

In this step, we also apply filters to exclude "copypasta" comments and occurrences as part of urls or mentioned Reddit users or subreddits.

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
