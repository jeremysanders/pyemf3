#!/usr/bin/env python

from __future__ import print_function

import os,sys
import glob
import filecmp
import pyemf

is_py3 = sys.version_info[0] == 3
if is_py3:
    bchr = lambda x: bytes((x,))
else:
    bchr = chr

def dump(fh, length=8):
    """"Return a hex dump of the file."""
    N=0; result=''
    s=fh.read(length)
    while len(s)>0:
        hexa = ' '.join(["%02X"%ord(s[i:i+1]) for i in range(len(s))])
        FILTER=b''.join([ bchr(x) if 32 <= x < 127 else b'.'
                          for x in range(256) ])
        s = s.translate(FILTER)
        result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s.decode('ascii'))
        N+=length
        s=fh.read(length)
    return result

def dumpfile(filename):
    fh=open(filename, "rb")
    if fh:
        result=dump(fh)
        fh=open(filename+".hex", "w")
        fh.write(result)

class Comparison:
    def __init__(self,verbose=False):
        self.verbose=verbose
        self.total=0
        self.passed=[]
        self.failed=[]

    def show(self,char):
        sys.stdout.write(char)
        sys.stdout.flush()

    def comparepy(self,pyfilename):
        self.total+=1
        filename=pyfilename[:-3]+".emf"
        outputfile=filename+".out.emf"
        try:
            exec(open(pyfilename).read())
            e=pyemf.EMF(verbose=self.verbose)
            e.load(filename)
            if os.path.exists(outputfile): os.remove(outputfile)
            ret=e.save(outputfile)
            if ret:
                if filecmp.cmp(filename,outputfile,shallow=False):
                    self.show(".")
                    self.passed.append(filename)
                else:
                    self.show("F")
                    self.failed.append(filename)
                    dumpfile(filename)
                    dumpfile(outputfile)
            else:
                self.failed.append(filename)
                self.show("0")
        except Exception as e:
            print(e)
            self.failed.append(filename)
            self.show("E")
            dumpfile(filename)
            dumpfile(outputfile)

    def test(self,tests):
        for filename in tests:
            self.comparepy(filename)
        self.stats()
            
    def stats(self):
        print()
        print("%d passed out of %d" % (len(self.passed),self.total))
        print("passed: %s" % self.passed)
        print("failed: %s" % self.failed)


def test(tests,options):
    total=0
    verbose=False
    passed=[]
    failed=[]

    tests.sort()
    for test in tests:
        print("Running %s" % test)
        total+=1
        try:
            exec(open(test).read())
            filename=test[:-3]+".emf"
            try:
                e=pyemf.EMF(verbose=options.verbose)
                e.load(filename)
                outputfile=filename+".out.emf"
                if os.path.exists(outputfile): os.remove(outputfile)
                ret=e.save(outputfile)
                if ret:
                    if filecmp.cmp(filename,outputfile,shallow=False):
                        print(".",)
                        passed.append(filename)
                    else:
                        print("F",)
                        failed.append(filename)
                        dumpfile(filename)
                        dumpfile(outputfile)
                else:
                    failed.append(filename)
                    print("0",)
            except Exception as e:
                print(e)
                failed.append(filename)
                print("E")
                dumpfile(filename)
                dumpfile(outputfile)
        except:
            failed.append(test)
            print("** test %s failed" % test)

    print("%d passed out of %d" % (len(passed),total))
    print("passed: %s" % passed)
    print("failed: %s" % failed)


if __name__=="__main__":
    from optparse import OptionParser

    parser=OptionParser(usage="usage: %prog [options] emf-files...")
    parser.add_option("-v", action="store_true", dest="verbose", default=False)
    (options, args) = parser.parse_args()

    if len(args)>0:
        tests=args
    else:
        tests=glob.glob("test-[a-z0-9]*py")

    comp=Comparison(options.verbose)
    comp.test(tests)
