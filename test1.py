#!/usr/bin/env python

import pyemf

width=8
height=6
dpi=300

emf=pyemf.EMF(width,height,dpi)
thin=emf.CreatePen(pyemf.PS_SOLID,1,(0x01,0x02,0x03))
emf.SelectObject(thin)
emf.Polyline([(0,0),(width*dpi,height*dpi)])
emf.Polyline([(0,height*dpi),(width*dpi,0)])
emf.save("test1.emf")
