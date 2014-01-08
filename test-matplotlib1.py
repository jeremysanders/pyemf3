#!/usr/bin/env python

useEMF=True

import sys

try:
    import matplotlib
except:
    print("Requires matplotlib from http://matplotlib.sourceforge.net.")
    sys.exit()
    
if useEMF:
    matplotlib.use('EMF')
    ext=".emf"
else:
    matplotlib.use('Agg')
    ext=".png"

from pylab import *

plot([1,2,4,9,7,8,4,2,1,5,2,4,3,0,6,0,6,1,5,1,5,4,2,9,1,8,3,6,1],'o-b',label="stuff")
plot([2,5,6,2,7,6,0,1,6,6,0,6,5,4,3,0,5,3,9,8,1,5,2,8,3,4,1,3,7],'s-g',label="and things")
xlabel("nm")
ylabel("diff")
legend(loc='best')
title("Title of stuff and things. ;qjkxbwz/,.pyfgcr!@#$%^&*(")
    
savefig("test-matplotlib1"+ext,dpi=150)
