#!/usr/bin/env python

import pyemf

# Test of handles and deleting objects.

width=8
height=6
dpi=100

emf=pyemf.EMF(width,height,dpi)
pen=[]
for i in range(16):
    pen.append(emf.CreatePen(pyemf.PS_SOLID,i,(i*16,0x20,0x40)))

for i in range(16):
    emf.SelectObject(pen[i])
    x1=0
    x2=width*dpi//2
    y=i*32
    emf.Polyline([(x1,y),(x2,y)])

emf.DeleteObject(pen[4])
emf.DeleteObject(pen[10])
emf.DeleteObject(pen[2])
emf.DeleteObject(pen[8])
emf.DeleteObject(pen[15])
for i in range(16):
    pen.append(emf.CreatePen(pyemf.PS_DASH,8,(0x01,(15-i)*16,0x03)))

for i in range(16):
    emf.SelectObject(pen[i])
    x1=width*dpi//2
    x2=width*dpi
    y=i*32
    emf.Polyline([(x1,y),(x2,y)])


ret=emf.save("test-deleteobject.emf")
print("save returns %s" % str(ret))
