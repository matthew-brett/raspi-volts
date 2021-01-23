#!/usr/bin/env python
""" Measure voltage normalized per hour
"""

import re
from datetime import datetime as DTM, timedelta
from collections import Counter

LOG_FILE = '/var/log/messages'

#Jan 17 15:30:32 freshpi kernel: [12372.101685] Voltage normalised (0x00000000)
LLINE_RE = re.compile(
    r'(?P<date>\w+ \d+ \d\d:\d\d:\d\d) \w+ kernel: '
    r'\[(?P<kno>[ 0-9.]+)\] (?P<msg>.*)')

ONE_HOUR = timedelta(hours=1)

NOW = DTM.now()
YEAR_PREFIX = str(NOW.year) + ' '
NOW_HOUR = DTM(NOW.year, NOW.month, NOW.day, NOW.hour)


def as_dt_hour(dt_str):
    return DTM.strptime(YEAR_PREFIX + dt_str.split(':')[0], r'%Y %b %d %H')


def counts2tab(ctr):
    """ Convert to table, dropping first and last hour
    """
    hours = sorted(ctr)[1:-1]
    return [(h, ctr[h]) for h in hours]


def parsed_lines(fname):
    results = []
    with open(fname, 'rt') as fobj:
        for line in fobj:
            m = LLINE_RE.match(line)
            if m:
                results.append(m.groups())
    return results


def get_ctrs(plines):
    last_kno = 0
    ctrs = [Counter()]
    start_hour = as_dt_hour(plines[0][0])
    for dt_str, kn_str, msg in plines:
        this_kno = float(kn_str)
        if this_kno < last_kno:
            # New kernel started.
            hour = as_dt_hour(dt_str)
            ctrs[-1] = fill_ctr(ctrs[-1], start_hour, hour)
            start_hour = hour
            ctrs.append(Counter())
        last_kno = this_kno
        if msg.startswith('Voltage normalised'):
            ctrs[-1][as_dt_hour(dt_str)] += 1
    ctrs[-1] = fill_ctr(ctrs[-1], start_hour, NOW_HOUR)
    return ctrs


def fill_ctr(ctr, start_hour, end_hour):
    """ Fill missing hours with zero counts
    """
    # We need to know when kernels turned over.  Start end can be first date in
    # log, and now.
    new_ctr = {}
    hour = start_hour
    while hour <= end_hour:
        if not hour in new_ctr:
            new_ctr[hour] = 0
        hour += ONE_HOUR
    return new_ctr


def print_tab(tab):
    if len(tab) == 0:
        return
    total = 0
    for dt, count in tab:
        total += count
        print(dt.strftime('%B %d %I %p'), count)
    average = total / float(len(tab))
    print('Average: {:0.1f}'.format(average))


def main():
    plines = parsed_lines(LOG_FILE)
    ctrs = get_ctrs(plines)
    tabs = [counts2tab(c) for c in ctrs]
    if len(tabs) == 0:
        print('No "Voltage normalised" in log')
        return
    for kno, tab in enumerate(tabs):
        print('Table for kernel', kno)
        print_tab(tab)
        print('-' * 10)


if __name__ == '__main__':
    main()
