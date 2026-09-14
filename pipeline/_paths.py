"""Where the corpus is, whichever tree these scripts are sitting in.

They were written inside the working copy, where the built site lives at ../site and the data under
../site/data. In this repository the same data sits at ../data, because there is no site here -- only
the corpus it is made from. Rather than keep two copies of every script that differ by one path, each
one asks here, and this looks for the data instead of assuming where it is.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

def site_root():
    """The directory that holds `data/`. In the working copy that is ../site; here it is the repository.

    It looks for library.json rather than for a data directory, because an empty data directory is
    worse than none: any script that creates its own output folder would otherwise make one, and every
    script afterwards would resolve to it and report the corpus missing.
    """
    for candidate in (os.path.join(HERE, '..', 'site'), os.path.join(HERE, '..')):
        if os.path.exists(os.path.join(candidate, 'data', 'library.json')):
            return os.path.abspath(candidate)
    return os.path.abspath(os.path.join(HERE, '..', 'site'))

SITE = site_root()
DATA = os.path.join(SITE, 'data')
WORKS = os.path.join(DATA, 'works')     # present in the working copy; see teiread.py for this repository
TEI = os.path.join(SITE, 'tei')
