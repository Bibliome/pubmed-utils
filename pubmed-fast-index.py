#!/bin/env python

from struct import pack
from os import listdir
from optparse import OptionParser
import re
from sys import stderr
from io import open

PMID_PATTERN = re.compile(r'<PMID Version="\d+">(\d+)</PMID>')

class PMIDIndex(OptionParser):
    def __init__(self):
        OptionParser.__init__(self, usage='usage: %prog [options]')
        self.add_option('--max-pmid', action='store', type='int', dest='max_pmid', default=2**25, metavar='PMID', help='greatest PMID')
        self.add_option('--pubmed-xml', action='store', type='string', dest='pubmed_xml', default='/bibdev/corpus/PubMed2012/xml', metavar='DIR', help='read PubMed XML files in directory DIR (default: %default)')
        self.add_option('--index-file', action='store', type='string', dest='index_file', default='/bibdev/corpus/PubMed2012/pmid-index.dat', metavar='FILE', help='file where to store the index')

    def run(self):
        options, args = self.parse_args()
        stderr.write('Creating index array\n')
        data = [-1] * (3 * options.max_pmid)
        xml_files = tuple(sorted(options.pubmed_xml + '/' + fn for fn in listdir(options.pubmed_xml)))
        stderr.write('Found %d XML files\n' % len(xml_files))
        for fi, fn in enumerate(xml_files):
            self._read_xml_file(data, fi, fn)
        stderr.write('Creating index file %s\n' % options.index_file)
        out = open(options.index_file, 'wb')
        out.write(pack('<i', options.max_pmid))
        stderr.write('Writing index array\n')
        out.write(pack('<%di' % (3 * options.max_pmid), *data))
        stderr.write('Writing file names\n')
        out.write(pack('<i', len(xml_files)))
        for fn in xml_files:
            l = len(fn)
            out.write(pack('<i', l))
            out.write(pack('<%ds' % l, fn))
        out.close()
        stderr.write('Done.\n')

    def _read_xml_file(self, data, fi, fn):
        stderr.write('Reading %s\n' % fn)
        f = open(fn, 'rb')
        start = None
        pmid = None
        for lineno, line in enumerate(f):
            if line.startswith('<MedlineCitation '):
                pmid = None
                start = f.tell() - len(line)
                continue
            if line.startswith('</MedlineCitation>'):
                if pmid is None:
                    stderr.write('WARNING: no PMID found: %d\n' % lineno)
                    continue
                length = f.tell() - start
                i = pmid * 3
                data[i] = fi
                data[i+1] = start
                data[i+2] = length
                pmid = None
                continue
            if pmid is not None:
                continue
            m = PMID_PATTERN.search(line)
            if m is not None:
                pmid = int(m.group(1))
        f.close()


PMIDIndex().run()
