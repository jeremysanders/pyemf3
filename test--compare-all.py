#!/usr/bin/env python

import os,sys
import glob
import filecmp

import pyemf

FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

def dump(fh, length=8):
    N=0; result=''
    s=fh.read(length)
    while len(s)>0:
       hexa = ' '.join(["%02X"%ord(x) for x in s])
       s = s.translate(FILTER)
       result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
       N+=length
       s=fh.read(length)
    return result

def dumpfile(filename):
    fh=open(filename)
    result=dump(fh)
    fh=open(filename+".hex","w")
    fh.write(result)

class Comparison:
    def __init__(self):
        self.verbose=False
        self.total=0
        self.passed=[]
        self.failed=[]

    def show(self,char):
        sys.stdout.write(char)
        sys.stdout.flush()

    def compare(self,filename):
        self.total+=1
        outputfile=filename+".out.emf"
        try:
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

    def stats(self):
        print()
        print("%d passed out of %d" % (len(self.passed),self.total))
        print("passed: %s" % self.passed)
        print("failed: %s" % self.failed)

comp=Comparison()
tests=glob.glob("test-[a-z0-9]*.py")
tests.sort()
for filename in tests:
    #print "Running %s" % test
    filename=filename[:-3]+".emf"
    comp.compare(filename)

# check some other (non-redistributable, unfortunately) tests
tests=['mapping1.emf','mapping2.emf','example1.emf','clip-art-computer.emf','features.emf']
for filename in tests:
    if os.path.exists(filename):
        comp.compare(filename)

comp.stats()
