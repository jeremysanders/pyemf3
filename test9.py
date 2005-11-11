#!/usr/bin/env python

import pyemf

from math import radians,cos,sin

print "Test of world transformations."

def path(emf,text,x,y,size=300):
    emf.BeginPath()
    emf.MoveTo(x,y)
    emf.LineTo(x+100,y+300)

    emf.ArcTo(x+100,y+300,x+100+size,y+300+size,x+100,y+300,x+100+size,y+300)

    emf.PolylineTo([(x+100+size,y+300),(x+150+size,y+200),(x+200+size,y+300),(x+250+size,y+100)])

    emf.PolyBezierTo([(x+100+size,y+50),(x+size,y+150),(x+size-100,y+100)])

    emf.CloseFigure()
    emf.EndPath()

    emf.StrokeAndFillPath()
    emf.TextOut(x,y,text);
    

width=6
height=4
dpi=300
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
font = emf.CreateFont( -50, 0, 0, 0, pyemf.FW_NORMAL, 0, 0, 0,
                       pyemf.ANSI_CHARSET, pyemf.OUT_TT_PRECIS,
                       pyemf.CLIP_TT_ALWAYS, pyemf.PROOF_QUALITY,
                       pyemf.DEFAULT_PITCH | pyemf.FF_DONTCARE,
                       "Helvetica" )

emf.SelectObject(font)

dx=50
dy=50
dotted=emf.CreatePen(pyemf.PS_DOT,1,(0x02,0x03,0x04))
emf.SelectObject(dotted)
emf.Polyline([(dx,0),(dx,dy),(0,dy)])
emf.SelectObject(dashed)


emf.SetWorldTransform(1.0,0.0,0.0,1.0,dx,dy)
path(emf,"translate (%d,%d) loc: 0,0" % (dx,dy),0,0,300)



dx=500
dy=800
emf.ModifyWorldTransform(pyemf.MWT_IDENTITY)
emf.SelectObject(dotted)
emf.Polyline([(dx,0),(dx,dy),(0,dy)])
emf.SelectObject(dashed)

d=45
angle=radians(d)
emf.SetWorldTransform(cos(angle),-sin(angle),sin(angle),cos(angle),dx,dy)
path(emf,"rotate %d deg, translate (%d,%d) loc: 0,0" % (d,dx,dy),0,0,300)




dx=1000
dy=1000
# reset broken transform
emf.SetWorldTransform(1.0,0.0,0.0,1.0,0,0)
emf.SelectObject(dotted)
emf.Polyline([(dx,0),(dx,dy),(0,dy)])
emf.SelectObject(dashed)

d=80
angle=radians(d)
emf.ModifyWorldTransform(pyemf.MWT_RIGHTMULTIPLY,cos(angle),-sin(angle),sin(angle),cos(angle),dx,dy)
path(emf,"rotate %d deg, translate (%d,%d) loc: 0,0" % (d,dx,dy),0,0,300)


ret=emf.save("test9.emf")
print "SaveEMF returns %s" % str(ret)

