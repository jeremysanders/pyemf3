#!/usr/bin/env python

# Test polygon fill mode

import pyemf

def polygon(emf,x,y):
    points=[(x,y+100),(x+400,y+400),(x+500,y+100),(x+800,y+400),(x+800,y+100),(x,y+400),
            (x,y),(x+850,y),(x+850,y+450)]
    emf.Polygon(points)


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


emf.TextOut(500,50,"Test of polygon fill mode")



x=100
y=300
emf.TextOut(x,y,"ALTERNATE")
emf.SetPolyFillMode(pyemf.ALTERNATE)
polygon(emf,x,y)


y=900
emf.TextOut(x,y,"WINDING")
emf.SetPolyFillMode(pyemf.WINDING)
polygon(emf,x,y)


ret=emf.save("test-poly2.emf")
print "save returns %s" % str(ret)
