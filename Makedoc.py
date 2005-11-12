#!/usr/bin/env python

import os,sys,re
from datetime import date
from optparse import OptionParser
from Cheetah.Template import Template

import pyemf

namespace={
    'prog':'pyemf',
    'version':pyemf.__version__,
    'author':pyemf.__author__,
    'author_email':pyemf.__author_email__,
    'url':pyemf.__url__,
    'description':pyemf.__description__,
    'release_date':'... er, soon', # should stat the file instead
    'today':date.today().strftime("%d %B %Y"),
    'year':date.today().strftime("%Y"),
    'htmlBody':'',
    'preBody':'',
    }

def store(keyword,infile):
    fh=open(infile)
    t=Template(file=fh,searchList=[namespace])
    namespace[keyword]=str(t)

def parse(infile):
    fh=open(infile)
    t=Template(file=fh,searchList=[namespace])
    return str(t)

if __name__=='__main__':
    usage="usage: %prog [-o file] [-n variablename file] [-t template] [files...]"
    parser=OptionParser(usage=usage)
    parser.add_option("-o", action="store", dest="outputfile")
    parser.add_option("-n", "--name", action="append", nargs=2,
                      dest="namespace")
    parser.add_option("-t", "--template", action="store", dest="template")
    (options, args) = parser.parse_args()

    all=''

    if options.namespace:
        for keyword,filename in options.namespace:
            # print "keyword=%s filename=%s" % (keyword,filename)
            store(keyword,filename)

    if options.template:
        all=parse(options.template)

    for filename in args:
        txt=parse(filename)
        if options.outputfile:
            print 'saving to %s' % options.outputfile
            all+=txt
        else:
            if filename.endswith('.in'):
                outfile=filename[:-3]
            else:
                outfile=filename+".out"
            fh=open(outfile,"w")
            fh.write(txt)
            fh.close()

    if options.outputfile:
        fh=open(options.outputfile,"w")
        fh.write(all)
        fh.close()
    else:
        print all
        
