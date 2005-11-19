#!/usr/bin/env python

import pyemf

from math import radians,cos,sin

print "Test of clip paths."

def clippath(emf,text,x,y,size=300):
    emf.TextOut(x+40,y,text);
    
    emf.BeginPath()
    emf.MoveTo(x,y)
    emf.LineTo(x+100,y+300)

    emf.ArcTo(x+100,y+300,x+100+size,y+300+size,x+100,y+300,x+100+size,y+300)

    emf.PolylineTo([(x+100+size,y+300),(x+150+size,y+200),(x+200+size,y+300),(x+250+size,y+100)])

    emf.PolyBezierTo([(x+100+size,y+50),(x+size,y+150),(x+size-100,y+100)])

    emf.CloseFigure()
    emf.EndPath()

    emf.SelectClipPath()
    

width=6
height=4
dpi=150
pointstopixels=dpi/72.0

emf=pyemf.EMF(width,height,dpi,verbose=False)
brush=emf.CreateSolidBrush((0x7f,0x7f,0xff))
emf.SelectObject(brush)
dashed=emf.CreatePen(pyemf.PS_DASHDOT,1,(0xf0,0x00,0x80))
emf.SelectObject(dashed)

emf.SetBkMode(pyemf.TRANSPARENT)
# set baseline for text to be top left corner
emf.SetTextAlign(pyemf.TA_TOP|pyemf.TA_LEFT) 
emf.SetTextColor((0,0,0))
font = emf.CreateFont( -18, 0, 0, 0, pyemf.FW_NORMAL, 0, 0, 0,
                       pyemf.ANSI_CHARSET, pyemf.OUT_TT_PRECIS,
                       pyemf.CLIP_TT_ALWAYS, pyemf.PROOF_QUALITY,
                       pyemf.DEFAULT_PITCH | pyemf.FF_DONTCARE,
                       "Helvetica" )

emf.SelectObject(font)

dotted=emf.CreatePen(pyemf.PS_DOT,1,(0x02,0x03,0x04))
emf.SelectObject(dashed)

id=emf.SaveDC()

clippath(emf,"Clip path:",0,0,300)

for x in range(0,width*dpi,10):
    emf.Polyline([(0,0),(x,height*dpi)])

for y in range(height*dpi,0,-10):
    emf.Polyline([(0,0),(width*dpi,y)])


smallfont = emf.CreateFont( -12, 0, 0, 0, pyemf.FW_NORMAL, 0, 0, 0,
                       pyemf.ANSI_CHARSET, pyemf.OUT_TT_PRECIS,
                       pyemf.CLIP_TT_ALWAYS, pyemf.PROOF_QUALITY,
                       pyemf.DEFAULT_PITCH | pyemf.FF_DONTCARE,
                       "Helvetica" )

emf.SelectObject(smallfont)
emf.TextOut(100,300,"This line is drawn while the clipping region is active and should be clipped by the clipping region");

emf.RestoreDC(-1)
emf.TextOut(0,200,"This line is drawn after the RestoreDC() and should be bigger and not be clipped by the clipping region");
emf.SelectObject(smallfont)
emf.TextOut(0,400,"This line is drawn after the RestoreDC(), should be smaller, and should not be clipped by the clipping region");



ret=emf.save("test-selectclippath1.emf")
print "save returns %s" % str(ret)
