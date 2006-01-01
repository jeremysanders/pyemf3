#!/usr/bin/env python

import glob

tests=glob.glob("test-[a-z0-9]*py")
tests.sort()
for test in tests:
    print "Running %s" % test
    try:
        execfile(test)
    except:
        print "** test %s failed" % test
