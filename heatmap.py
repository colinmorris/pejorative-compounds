import seaborn as sns
import matplotlib as mpl
from matplotlib import pyplot as plt
import math
import numpy as np

DEFAULT_FIGSIZE = (18, 14)

WIKI_GLYPH = '📖'

def ticks_for_max(maxval):
    ticks = [0]
    val = 1
    while val <= maxval:
        ticks.append(val)
        val *= 10
    l = int(math.log10(maxval))
    final = math.floor(maxval / 10**l) * 10**l
    if final not in ticks:
        ticks.append(final)
    return ticks

def cbar_format_fn(tickval, _ignored_posn):
    if tickval >= 10**6:
        mills = int(tickval / 10**6)
        return f'{mills}m'
    else:
        return f'{tickval:,}'
CBAR_FORMATTER = mpl.ticker.FuncFormatter(cbar_format_fn)

def make_heatmap(df,
        figsize=DEFAULT_FIGSIZE,
        sort=True,
        cmap='Blues',
        wiki=False,
        wiki_glyph=WIKI_GLYPH,
        # We default to a symlog colorbar scale, but passing gamma will use a powernorm instead.
        gamma=None,
        annot_kws=None,
        ax=None,
        return_fig=False,
        normalize_rows=False,
        **heatmap_kwargs,
        ):
    assert not (ax and return_fig), "return_fig not supported when providing ax"
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    mat = matricize_df(df, sort, 'count')

    if normalize_rows:
        # make rows sum to same amount
        rowsum = mat.mean(axis=1).mean()
        mat = mat.apply(lambda row: rowsum * (row/row.mean()), axis=1) 

    if wiki:
        dd = df.copy()
        # Column for annot text
        dd['wtext'] = ''
        dd.loc[dd.wikt, 'wtext'] = wiki_glyph
        annots = matricize_df(dd, sort, 'wtext')
    else:
        annots = None

    #vmin = df['count'].min()
    #vmax = df['count'].max()
    vmin = mat.min().min()
    vmax = mat.max().max()
    if gamma:
        norm = mpl.colors.PowerNorm(vmin=vmin, vmax=vmax, gamma=gamma)
    else:
        norm = mpl.colors.SymLogNorm(linthresh=1.0, linscale=0.5, vmin=vmin, vmax=vmax, base=10)
    heatmap_kwargs.setdefault('norm', norm)

    # Colorbar ticks
    heatmap_kwargs.setdefault('cbar_kws', {})
    ticks = ticks_for_max(vmax)
    heatmap_kwargs['cbar_kws'].setdefault('ticks', ticks)
    heatmap_kwargs['cbar_kws'].setdefault('format', CBAR_FORMATTER)

    sns.heatmap(
            data=mat,
            ax=ax,
            cmap=cmap,
            square=True,
            annot=annots,
            fmt='s',
            annot_kws=annot_kws,
            **heatmap_kwargs,
    )
    ax.tick_params(axis='x', labeltop=True, labelbottom=False,
                       labelrotation=45,
                  )
    ax.tick_params(axis='y', labelrotation=0)
    ax.tick_params(axis='both', labelsize='large')
    ax.set_xlabel('')
    ax.set_ylabel('')
    if return_fig:
        return fig, ax
    else:
        return ax

def matricize_df(df, sort=False, col='count'):
    """Return a pandas dataframe with rows and columns labelled by affixes.
    mat['poop', 'muffin'] will be the count of comments for 'poopmuffin'.

    Params:
    - df: dataframe with row per compound, having columns "pre", "suff", and "count"
          this sort of dataframe can be obtained by running viz_helpers.load_df()
    - sort: if 'log', sort rows and columns by the sum of log counts
            otherwise if truthy, sort by sum of counts
            otherwise, order of rows and columns is undefined
    - col: name of column in df having comment counts
    """
    mat = df.pivot("pre", "suff", col)
    if sort == 'log':
        xf = df.copy()
        xf['logcount'] = np.log10(xf['count'] + 10)
        precounts = xf.groupby('pre')['logcount'].sum().sort_values(ascending=False)
        suffcounts = xf.groupby('suff')['logcount'].sum().sort_values(ascending=False)
        mat = mat.loc[precounts.index, suffcounts.index]

    elif sort:
        precounts = df.groupby('pre')['count'].sum().sort_values(ascending=False)
        suffcounts = df.groupby('suff')['count'].sum().sort_values(ascending=False)
        mat = mat.loc[precounts.index, suffcounts.index]
    return mat
