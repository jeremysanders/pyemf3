#!/usr/bin/env python

# Test of bounds checking and 16bit/32bit versions of polygon, polyline, etc.

import pyemf

width=8
height=6
dpi=300

emf=pyemf.EMF(width,height,dpi)
pen=emf.CreatePen(pyemf.PS_SOLID,10,(0x01,0xa0,0xff))
emf.SelectObject(pen)
brush=emf.CreateSolidBrush((0x50,0x50,0x50))
emf.SelectObject(brush)

emf.SetBkMode(pyemf.TRANSPARENT)
# set baseline for text to be bottom left corner
emf.SetTextAlign(pyemf.TA_BOTTOM|pyemf.TA_LEFT) 
emf.SetTextColor((0,0,0))
font = emf.CreateFont( 50, 0, 0, 0, pyemf.FW_BOLD, 0, 0, 0,
                       pyemf.ANSI_CHARSET, pyemf.OUT_DEFAULT_PRECIS,
                       pyemf.CLIP_DEFAULT_PRECIS, pyemf.DEFAULT_QUALITY,
                       pyemf.DEFAULT_PITCH | pyemf.FF_DONTCARE, "Arial");
emf.SelectObject( font );


emf.TextOut(500,50,"Test of polypolygon and polypolyline")

x=100
y=300

emf.TextOut(x,y,"several filled-in squares.  OpenOffice doesn't seem to complete the polygons.")
polylist=[]
for x1 in range(x,x+1000,200):
    polylist.append([(x1,y),(x1+100,y),(x1+100,y+100),(x1,y+100)])
emf.PolyPolygon(polylist)


x=100
y=800
polylist=[]
emf.TextOut(100,y,"it's ... just a bunch of wavy lines.")
for y1 in range(y,y+500,100):
    points=[]
    for x in range(100,1000,50):
        points.append((x,y1))
        points.append((x+25,y1+25))
    polylist.append(points)
emf.PolyPolyline(polylist)

ret=emf.save("test-poly1.emf")
print("save returns %s" % str(ret))
