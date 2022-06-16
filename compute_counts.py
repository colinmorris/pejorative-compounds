"""Use raw json comment data to create a csv of (all-time) counts per term.
Takes care of the following details:
    - Filtering comments which should be ignored e.g. because the target term
      occurs as part of a URL, or a reference to a subreddit name.
    - Extrapolating counts for high-frequency terms for which we have sampled
      comment data.

TODO: Consider adding (optionally?) columns related to munging:
    - raw count (w/o any filtering or scaling)
    - whether count is extrapolated based on sampling
    - number of comments filtered
might be useful for debugging
"""
import re
import os
import json
import itertools
from collections import defaultdict
import argparse

from reddit_counts import prefixes, suffixes

SAMPLED_DIR = 'sampled_comment_data'
RAW_DIR = 'comment_data'

def tokens_having_term(text, term):
    """Case insensitive."""
    # We also split on square brackets to account for markdown formatting (don't want link text to be mingled with url)
    tokens = re.split('[\s\[\]]', text)
    for token in tokens:
        if term in token.lower():
            yield token

# Pattern matching textual references to subreddits or reddit users
reddit_entity_ref_pattern = re.compile('/?[rRuU]/')
def looks_urlish(token):
    # coarse but probably precise enough
    return (
        ('.' in token and '/' in token)
        or
        # Reference to username or subreddit
        re.match(reddit_entity_ref_pattern, token)
    )

def is_probably_copypasta(text):
    # Tested this on cockshit.json. 42/501 comments were identified as copypasta, and all were true +ves.
    # Somewhere around 2-4 false negatives, which were corrupted from the originals enough to be
    # unrecognizable.
    # Could maybe get higher recall (and deal with other, unseen copypastas), by matching on structure
    # rather than content. Basically looking for long comments with tokens regularly separated by
    # spaces / commas / newlines.
    # Could even just exclude comments longer than, say, 15k characters (character limit is 40k. Before 2015,
    # it was 40k for text subreddits and 15k for subs that allowed link submissions.) Would have bad precision,
    # but great recall. Actually, would need to set it lower. Typical size ranges from 2.7k - 9k characters.
    # Tried manually inspecting comments above 2.6k characters in douchebag.json. Got 16 legit comments and
    # 10 that should have been excluded (some because they were unidentified copy-pasta, but others were
    # just copy-pastes of lists/code related to swearing which was not necessarily a meme). Out of ~1.75k comments.
    
    # https://www.reddit.com/r/copypasta/comments/jmt0xx/every_single_swear_word_i_didnt_write_this_i/
    # This copypasta comes up pretty frequently, distorting counts for long tail terms in the list.
    # An exact string comparison won't work because it's been subject to lots of mutations. But can
    # check for the simultaneous presence of a few distinctive tokens to identify with pretty high
    # precision/recall. NB there are variants with r's and/or l's replaced with w's, so avoid matching
    # on tokens containing those letters
    every_swearword_tokens = ['homodumbshit', 'cocknugget', 'doochbag']
    if all(token in text for token in every_swearword_tokens):
        return True
    
    # Another similar copypasta purporting to be google's 2,027 blocked words:
    # /r/copypasta/comments/awviys/all_of_googles_blocked_words/ehpexe4/
    # Similar one that comes up is dark souls 2 chat blacklist
    if '2 girls 1 cup, 2g1c' in text:
        return True
    
    
    return False

def is_valid_comment(comment, term):
    """Return whether the given comment should contribute to our cuont of the
    occurrences of the given term. Currently disqualifying if
    - the term occurs as part of a URL.
    - matches some signatures of known spammy/copy-pasta comments that just list lots of curse words
    - occurs in a subreddit known to have a bad signal-to-noise ratio
    In the future may add more criteria (e.g. if the author appears to be a bot.)
    """
    sub = comment['subreddit']
    if sub == 'copypasta':
        return False
    body = comment['body']
    if is_probably_copypasta(body):
        return False
    
    for token in tokens_having_term(body, term):
        if not looks_urlish(token):
            return True
    return False

def load_comments(term):
    fname = f'{term}.json'
    samplepath = os.path.join(SAMPLED_DIR, fname)
    if os.path.exists(samplepath):
        with open(samplepath) as f:
            return json.load(f), True
    path = os.path.join(RAW_DIR, fname)
    with open(path) as f:
        return json.load(f), False

def count_for_term(term, raw):
    comments, sampled = load_comments(term)
    if raw:
        count = len(comments)
    else:
        count = sum(is_valid_comment(c, term) for c in comments)
    if sampled and not raw:
        # Our counts are based on sampling comments from 30 randomly
        # chosen days per year. So scale up by a bit more than a factor
        # of 10
        count *= 365.25 / 30
    return count

def sub_counts_for_term(term):
    """Return dict mapping subreddit name to count.
    """
    comments, sampled = load_comments(term)
    multiplier = (365.25 / 30) if sampled else 1.0
    counts = defaultdict(float)
    for comment in comments:
        if not is_valid_comment(comment, term):
            continue
        counts[comment['subreddit']] += multiplier
    return counts

def print_all_compound_counts(raw):
    # header
    print("pre,suff,count")
    for pre, suff in itertools.product(prefixes, suffixes):
        term = pre + suff
        count = count_for_term(term, raw)
        print(f"{pre},{suff},{count}")

def print_counts_by_subreddit():
    # header
    print("pre,suff,sub,count")
    for pre, suff in itertools.product(prefixes, suffixes):
        term = pre + suff
        counts = sub_counts_for_term(term)
        for (sub, count) in counts.items():
            print(f"{pre},{suff},{sub},{count}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Output a csv of term counts to stdout")
    parser.add_argument('--raw', action='store_true',
            help="Output raw comment counts with no filtering",
    )
    parser.add_argument('--sub', action='store_true',
            help="Add a grouping by subreddit",
    )
    args = parser.parse_args()
    if args.sub:
        assert not args.raw, "This combination of args not supported"
        print_counts_by_subreddit()
    else:
        print_all_compound_counts(raw=args.raw)
