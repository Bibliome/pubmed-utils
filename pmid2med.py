#!/bin/env python

from sys import argv
from os.path import basename
import re

PMID_PATTERN = re.compile(r'<PMID Version="1">(\d+)</PMID>')

for fn in argv[1:]:
    f = open(fn)
    fn = basename(fn)
    pmid = False
    for line in f:
        if line.startswith('<MedlineCitation '):
            pmid = False
            continue
        if pmid:
            continue
        m = PMID_PATTERN.search(line)
        if m is not None:
            print '%s\t%s' % (m.group(1), fn)
            pmid = True
    f.close()
