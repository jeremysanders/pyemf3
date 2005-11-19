#!/usr/bin/env python

import pyemf

print "Test of GetStockObject"

width=8
height=6
dpi=100
pointstopixels=dpi/72.0

emf=pyemf.EMF(width,height,dpi,verbose=False)
pen=emf.GetStockObject(pyemf.BLACK_PEN)
emf.SelectObject(pen)

# Device coordinates seem to be dimension in .01mm units / 31.25 mmunits/deviceunit

emf.Rectangle(0,0,320,640)

pen=emf.GetStockObject(pyemf.WHITE_PEN)
emf.SelectObject(pen)
emf.Rectangle(0,100,500,200)

print "after Rectangle"


brush=emf.GetStockObject(pyemf.WHITE_BRUSH)
emf.SelectObject(brush)
points=[(200,200),(300,400),(100,400)]
emf.Polygon(points);
print "after Polygon"

ret=emf.save("test-stockobject.emf")
print "save returns %d" % ret

