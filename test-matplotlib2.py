#!/usr/bin/python

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

semilogy([12,49,78,42,.15,24,.30,60,1],label="stuff")
semilogy([25,62,76,66,.6,54,30,53,.098],label="$10^{-1}$")
xlabel("nm")
ylabel("diff")
legend(loc='best')
title("Title of stuff and things. ;qjkxbwz/,.pyfgcr!@#$%^&*(")
    
savefig("test-matplotlib2"+ext,dpi=300)
