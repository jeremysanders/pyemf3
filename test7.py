#!/usr/bin/env python

# Test of bounds checking and 16bit/32bit versions of polygon, polyline, etc.

import pyemf

width=8
height=6
dpi=300

emf=pyemf.EMF(width,height,dpi)
pen16=emf.CreatePen(pyemf.PS_SOLID,1,(0x01,0x02,0xff))
pen32=emf.CreatePen(pyemf.PS_SOLID,1,(0x01,0xff,0x03))

emf.SelectObject(pen16)
emf.Polyline([(0,0),(width*dpi,height*dpi/2)])
emf.SelectObject(pen32)
emf.Polyline([(0,0),(40000,height*dpi/2)])
emf.SelectObject(pen16)
emf.Polyline([(width*dpi,height*dpi/2),(0,height*dpi)])
emf.SelectObject(pen32)
emf.Polyline([(40000,height*dpi/2),(0,height*dpi)])

emf.save("test7.emf")
