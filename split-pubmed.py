#!/bin/env python


from optparse import OptionParser
from os.path import dirname, exists
from os import makedirs
from sys import stderr

XML_HEADER = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE PubmedArticleSet SYSTEM "http://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_170101.dtd">
<PubmedArticleSet>
'''
XML_HEADER_NO_DOCTYPE = '''<?xml version="1.0" encoding="utf-8"?>
<PubmedArticleSet>
'''
XML_FOOTER = '''</PubmedArticleSet>
'''

class SplitPubMed(OptionParser):
    def __init__(self):
        OptionParser.__init__(self, usage='usage: %prog [options] XMLFILES...')
        self.add_option('--max-entries', action='store', type='int', dest='max_entries', default=1)
        self.add_option('--pattern', action='store', type='string', dest='pattern', default='%d.xml')
        self.add_option('--no-doctype', action='store_true', dest='no_doctype', default=False)

    def open_next(self, batch):
        filename = self.options.pattern % (batch,)
        dir = dirname(filename)
        if dir != '' and not exists(dir):
            makedirs(dir)
        result = open(filename, 'w')
        if self.options.no_doctype:
            result.write(XML_HEADER_NO_DOCTYPE)
        else:
            result.write(XML_HEADER)        
        return result

    def close(self, fout):
        fout.write(XML_FOOTER)
        fout.close()

    def split(self):
        self.options, self.args = self.parse_args()
        batch = 0
        n = 0
        fout = self.open_next(batch)
        for filename in self.args:
            fin = open(filename)
            inside = False
            for line in fin:
                if line.strip().startswith('<PubmedArticle>'):
                    inside = True
                if inside:
                    fout.write(line)
                if line.strip().startswith('</PubmedArticle>'):
                    n += 1
                    if n == self.options.max_entries:
                        self.close(fout)
                        batch += 1
                        n = 0
                        fout = self.open_next(batch)
                    inside = False
            fin.close()
        self.close(fout)


SplitPubMed().split()
