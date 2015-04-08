#!/usr/bin/env python

import pyemf

width=8
height=6
dpi=300
pointstopixels=dpi/72.0

emf=pyemf.EMF(width,height,dpi,verbose=False)

emf.Polyline([(1000,1000),(2000,0)])
emf.Polyline(((1000,1000),(2000,0)))
p1=[(0,0),(width*dpi,height*dpi)]
p2=[(0,height*dpi),(width*dpi,0)]
emf.Polyline(p1)
emf.Polyline(p2)

x=100
y=800
points=[]
for x in range(100,1000,50):
    points.append((x,y))
    points.append((x+25,1+25))
emf.Polyline(points)

ret=emf.save("test-polyline1.emf")
print("save returns %s" % str(ret))

