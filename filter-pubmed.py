#!/bin/env python

from os import listdir
from os.path import isdir
from sys import stderr
from optparse import OptionParser
from StringIO import StringIO
import re

PMID_PATTERN = re.compile(r'<PMID Version="1">(\d+)</PMID>')
MESH_PATTERN = re.compile(r'<DescriptorName.*UI="(D\d+)".*>.+</DescriptorName>')
XML_HEADER = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE PubmedArticleSet SYSTEM "http://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_170101.dtd">
<PubmedArticleSet>
'''
XML_FOOTER = '''
'''

class FilterPubMed(OptionParser):
    def __init__(self):
        OptionParser.__init__(self, usage='usage: %prog [options]')
        self.add_option('--mesh-tree', action='store', type='string', dest='mesh_trees', default='/bibdev/ressources/MeSH/mtrees2013.bin', metavar='FILE', help='read MeSH trees from FILE (default: %default)')
        self.add_option('--mesh-filter', action='store', type='string', dest='mesh_filter', metavar='FILE', help='read accepted MeSH indexes from FILE')
        self.add_option('--pubmed-xml', action='store', type='string', dest='pubmed_xml', default='/bibdev/corpus/PubMed2015/xml', metavar='DIR', help='read PubMed XML files in directory DIR (default: %default)')
        self.add_option('--pmid-filter', action='store', type='string', dest='pmid_filter', metavar='FILE', help='read accepted PMIDs from FILE')
        self.add_option('--xml-out', action='store', type='string', dest='xml_out', metavar='FILE', help='write filtered accepted in FILE')
        self.add_option('--pmid-out', action='store', type='string', dest='pmid_out', metavar='FILE', help='write accepted PMIDs in FILE')

    def _read_pmid_filter(self):
        if self.options.pmid_filter is None:
            self.pmid_filter = None
            return
        stderr.write('Reading PMID filter file: %s\n' % self.options.pmid_filter)
        f = open(self.options.pmid_filter)
        self.pmid_filter = set(line.strip() for line in f)
        f.close()

    def _read_mesh_filter(self):
        if self.options.mesh_filter is None:
            self.mesh_filter = None
            return
        stderr.write('Reading MeSH filter file: %s\n' % self.options.mesh_filter)
        f = open(self.options.mesh_filter)
        mesh_paths = set(line.strip() for line in f)
        f.close()
        stderr.write('Reading MeSH trees file: %s\n' % self.options.mesh_trees)
        f = open(self.options.mesh_trees)
        self.mesh_filter = set()
        for line in f:
            path, did, dname = line.strip().split('\t')
            for p in mesh_paths:
                if path.startswith(p):
                    stderr.write('  %s: %s\n' % (did, dname))
                    self.mesh_filter.add(did)
                    break

    def filter(self):
        self.options, self.args = self.parse_args()
        self._read_pmid_filter()
        self._read_mesh_filter()
        mem = Memory(self.options.xml_out, self.options.pmid_out, self.pmid_filter, self.mesh_filter)
        for filename in list_files(self.options.pubmed_xml): #listdir(self.options.pubmed_xml):
            if filename.endswith('.xml'):
                stderr.write('Reading PubMed XML file: %s\n' % filename)
                f = open(filename)
                state = mem.init()
                for line in f:
                    state = state(line, mem)
                f.close()
        mem.close()


def list_files(path):
    if isdir(path):
        for p in listdir(path):
            yield path + '/' + p
    yield path


class Memory:
    def __init__(self, xml_out, pmid_out, pmid_filter, mesh_filter):
        if xml_out is None:
            self.xml_out = None
        else:
            stderr.write('Writing XML into %s\n' % xml_out)
            self.xml_out = open(xml_out, 'w')
            self.xml_out.write(XML_HEADER)
        if pmid_out is None:
            self.pmid_out = None
        else:
            stderr.write('Writing PMIDs into %s\n' % pmid_out)
            self.pmid_out = open(pmid_out, 'w')
        self.pmid_filter = pmid_filter
        self.mesh_filter = mesh_filter
        self.init()

    def close(self):
        if self.xml_out is not None:
            self.xml_out.write(XML_FOOTER)
            self.xml_out.close()
        if self.pmid_out is not None:
            self.pmid_out.close()

    def init(self):
        if self.xml_out is None:
            self.buf = None
        else:
            self.buf = []
        self.pmid = None
        return state_start

    def output(self):
        if self.pmid_out is not None:
            self.pmid_out.write(self.pmid)
            self.pmid_out.write('\n')
        if self.xml_out is not None:
            for line in self.buf:
                self.xml_out.write(line)
            return state_output
        return self.init()

    def write(self, line):
        if self.xml_out is not None:
            self.xml_out.write(line)

    def buffer(self, line):
        if self.buf is not None:
            self.buf.append(line)


def state_start(line, mem):
    if line.strip().startswith('<PubmedArticle>'):
        mem.buffer(line)
        return state_buffer
    return state_start

def state_buffer(line, mem):
    mem.buffer(line)
    m = PMID_PATTERN.search(line)
    if m is not None:
        mem.pmid = m.group(1)
        if mem.pmid_filter is None or mem.pmid in mem.pmid_filter:
            if mem.mesh_filter is None:
                return mem.output()
            return state_pmid
        return state_reject
    return state_buffer

def state_reject(line, mem):
    if line.strip().startswith('</PubmedArticle>'):
        return mem.init()
    return state_reject

def state_pmid(line, mem):
    if line.strip().startswith('</PubmedArticle>'):
        return mem.init()
    mem.buffer(line)
    m = MESH_PATTERN.search(line)
    if m is not None:
        if m.group(1) in mem.mesh_filter:
            return mem.output()
    return state_pmid

def state_output(line, mem):
    mem.xml_out.write(line)
    if line.strip().startswith('</PubmedArticle>'):
        return mem.init()
    return state_output



FilterPubMed().filter()
