#!/bin/env python

from optparse import OptionParser
from struct import unpack
from sys import stderr, stdout, stdin
from io import open

XML_HEADER = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE MedlineCitationSet PUBLIC "-//NLM//DTD Medline Citation, 1st January, 2009//EN"
                                    "http://teamsite.nlm.nih.gov:81/iw-mount/default/main/nlm/STAGING/htdocs/databases/dtd/nlmmedline_090101.dtd">
<MedlineCitationSet>
'''
XML_HEADER_NO_DTD = '''<?xml version="1.0" encoding="UTF-8"?>
<MedlineCitationSet>
'''
XML_FOOTER = '''</MedlineCitationSet>
'''

def _read_int(f):
    return unpack('<i', f.read(4))[0]

class PMIDFastFilter(OptionParser):
    def __init__(self):
        OptionParser.__init__(self, usage='usage: %prog [options]')
        self.add_option('--index-file', action='store', type='string', dest='index_file', default='/bibdev/corpus/PubMed2012/pmid-index.dat', metavar='FILE', help='file where to store the index')
        self.add_option('--include-dtd', action='store_true', dest='include_dtd', default=False, metavar='FILE', help='either to include DTD declaration')

    def run(self):
        options, args = self.parse_args()
        
        stderr.write('Reading index file %s\n' % options.index_file)
        fidx = open(options.index_file, 'rb')
        max_pmid = _read_int(fidx)
#        n = 3 * max_pmid
#        stderr.write('Loading PMID index (max PMID: %d)\n' % max_pmid)
#        b = fidx.read(n * 4)
#        data = unpack('<%di' % n, b)
        stderr.write('Loading file names\n')
        xml_files = []
        n = 3 * max_pmid
        fidx.seek(4 + n * 4)
        for _ in xrange(_read_int(fidx)):
            l = _read_int(fidx)
            xml_files.append(unpack('<%ds' % l, fidx.read(l))[0])
#        fidx.close()


        stderr.write('Reading PMIDs\n')
        pmids = set()
        for line in stdin:
            pmid = int(line)
            if pmid in pmids:
                stderr.write('WARNING: duplicate PMID: %d\n' % pmid)
            elif pmid < 0 or pmid > max_pmid:
                stderr.write('WARNING: invalid PMID: %d\n' % pmid)
            else:
                pmids.add(pmid)
        pmids = sorted(pmids)

        stderr.write('Fetching source positions\n')
        map = {}
        for pmid in pmids:
            n = 3 * pmid
            fidx.seek(4 + n * 4)
            b = fidx.read(12)
            (fi, start, length) = unpack('<iii', b)
#            (fi, start, length) = data[i:(i+3)]
            if fi == -1:
                stderr.write('WARNING: PMID not in index: %d\n' % pmid)
                continue
            if fi in map:
                pos = map[fi]
            else:
                pos = []
                map[fi] = pos
            pos.append((start, length))

        if options.include_dtd:
            stdout.write(XML_HEADER)
        else:
            stdout.write(XML_HEADER_NO_DTD)
        for fi, pos in map.iteritems():
            fn = xml_files[fi]
            stderr.write('Reading %s\n' % fn)
            f = open(fn, 'rb')
            pos.sort()
            for start, length in pos:
                f.seek(start)
                b = f.read(length)
                stdout.write(b)
            f.close()
        stdout.write(XML_FOOTER)

PMIDFastFilter().run()
