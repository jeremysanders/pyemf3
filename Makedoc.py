#!/usr/bin/env python

import os,sys,re,os.path
from datetime import date
from optparse import OptionParser
from Cheetah.Template import Template

import pyemf

module=pyemf

namespace={
    'prog':module.__name__,
    'author':module.__author__,
    'author_email':module.__author_email__,
    'url':module.__url__,
    'description':module.__description__,
    'cvs_version':module.__version__,
    'release_version':None,
    'version':None,
    'release_date':None, # should stat the file instead
    'release_file':None,
    'today':date.today().strftime("%d %B %Y"),
    'year':date.today().strftime("%Y"),
    'yearstart':'2005',
    'htmlBody':'',
    'preBody':'',
    }

def findlatest():
    files=os.listdir('archive')
    timestamp=0
    filename=None
    for name in files:
        mtime=os.path.getmtime(os.path.join('archive',name))
        if mtime>timestamp:
            timestamp=mtime
            filename=name
    if timestamp>0:
        namespace['release_date']=date.fromtimestamp(timestamp).strftime("%d %B %Y")
        namespace['release_file']=filename
        match=re.search(r'-([0-9]+\.[0-9]+(\.[0-9]+([ab][0-9]+)?))',filename)
        if match:
            namespace['release_version']=match.group(1)
    else:
        namespace['release_date']='... er, soon'

    if namespace['release_version']:
        namespace['version']=namespace['release_version']
    else:
        namespace['version']=namespace['cvs_version']

##filename=namespace['prog']+'-'+namespace['version']+'.tar.gz'
##if os.path.exists(filename):
##    namespace['release_date']=date.fromtimestamp(os.path.getmtime(filename)).strftime("%d %B %Y")
##elif os.path.exists('archive/'+filename):
##    namespace['release_date']=date.fromtimestamp(os.path.getmtime('archive/'+filename)).strftime("%d %B %Y")
##else:
##    namespace['release_date']='... er, soon'

findlatest()

if int(namespace['yearstart'])<int(namespace['year']):
    namespace['yearrange']=namespace['yearstart']+'-'+namespace['year']
else:
    namespace['yearrange']=namespace['year']



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
    parser.add_option("-p", "--print-namespace", action="store_true", dest="printnamespace")
    (options, args) = parser.parse_args()

    all=''

    if options.namespace:
        for keyword,filename in options.namespace:
            # print "keyword=%s filename=%s" % (keyword,filename)
            store(keyword,filename)

    if options.template:
        all=parse(options.template)

    if options.printnamespace:
        print namespace
        sys.exit()

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
        
