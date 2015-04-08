#!/usr/bin/env python

import os,sys,re,os.path
from cStringIO import StringIO
from datetime import date
from optparse import OptionParser
from string import Template

module=None

namespace={
    'prog':None,
    'author':None,
    'author_email':None,
    'url':None,
    'description':None,
    'cvs_version':None,
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


def setnamespace():
    if module:
        defaults={
            'prog':module.__name__,
            'author':module.__author__,
            'author_email':module.__author_email__,
            'url':module.__url__,
            'description':module.__description__,
            'cvs_version':module.__version__,
            }
        
        for key,val in defaults.iteritems():
            namespace[key]=val
            # print "%s=%s" % (key,val)
    
    findlatest()

    if int(namespace['yearstart'])<int(namespace['year']):
        namespace['yearrange']=namespace['yearstart']+'-'+namespace['year']
    else:
        namespace['yearrange']=namespace['year']



def store(keyword,infile):
    if isinstance(infile,str):
        fh=open(infile)
    else:
        fh=infile
    txt=fh.read()
    t=Template(txt)
    out=t.safe_substitute(namespace)
    namespace[keyword]=out

def remap(keyword,value):
    if value.startswith('$'):
        value=namespace[value[1:]]
    namespace[keyword]=value

def parse(infile):
    if isinstance(infile,str):
        fh=open(infile)
    else:
        fh=infile
    txt=fh.read()
    t=Template(txt)
    out=t.safe_substitute(namespace)
    return out

def parsedocstring(infile):
    if isinstance(infile,str):
        fh=open(infile)
    else:
        fh=infile
    doc=StringIO()
    count=0
    while count<2:
        line=fh.readline()
        if line.find('"""')>=0: count+=1
        doc.write(line)
    txt=doc.getvalue()
    unparsed=fh.read()
    t=Template(txt)
    out=t.safe_substitute(namespace)
    return out+unparsed



if __name__=='__main__':
    usage="usage: %prog [-m module] [-o file] [-n variablename file] [-t template] [files...]"
    parser=OptionParser(usage=usage)
    parser.add_option("-m", action="store", dest="module",
                      help="module to import")
    
    parser.add_option("-o", action="store", dest="outputfile",
                      help="output filename")
    parser.add_option("-n", "--name", action="append", nargs=2,
                      dest="namespace", metavar="KEY FILENAME",
                      help="expand the named variable KEY with the contents of FILENAME")
    parser.add_option("-r", "--remapkey", action="append", nargs=2,
                      dest="remapkey", metavar="KEY1 KEY2",
                      help="remap the named variable KEY1 with the value of the named variable KEY2")
    parser.add_option("-k", "--keyvalue", action="append", nargs=2,
                      dest="keyvalue", metavar="KEY VALUE",
                      help="remap the named variable KEY with the supplied constant VALUE, or if VALUE begins with a $, with the value of that named variable.  Note that you probably have to escape the $ from the shell with \\$")
    parser.add_option("-t", "--template", action="store", dest="template",
                      help="filename of template file")
    parser.add_option("-p", "--print-namespace", action="store_true",
                      dest="printnamespace", help="print namespace and exit without processing")
    parser.add_option("-d", "--docstring-only", action="store_true",
                      dest="docstringonly", help="only variable-expand the named file's docstring only; leave the remaining contents unchanged.")
    (options, args) = parser.parse_args()

    all=''

    if options.module:
        module=__import__(options.module)

    setnamespace()

    if options.namespace:
        for keyword,filename in options.namespace:
            # print "keyword=%s filename=%s" % (keyword,filename)
            store(keyword,filename)

    if options.keyvalue:
        for keyword,value in options.keyvalue:
            print "keyword=%s value=%s" % (keyword,value)
            remap(keyword,value)

    if options.remapkey:
        for key1,key2 in options.remapkey:
            value=namespace[key2]
            print "keyword=%s value=%s" % (key1,value)
            remap(key1,value)

    if options.template:
        all=parse(options.template)

    if options.printnamespace:
        print namespace
        sys.exit()

    for filename in args:
        if options.docstringonly:
            txt=parsedocstring(filename)
        else:
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
        
