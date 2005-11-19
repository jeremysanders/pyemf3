#!/usr/bin/env python

import pyemf

def path(emf,text,x,y,size=300):
    emf.TextOut(x,y,text);
    y+=50
    
    emf.BeginPath()
    emf.MoveTo(x,y)
    emf.LineTo(x+100,y+300)

    emf.ArcTo(x+100,y+300,x+100+size,y+300+size,x+100,y+300,x+100+size,y+300)

    emf.PolylineTo([(x+400,y+300),(x+450,y+200),(x+500,y+300),(x+550,y+100)])

    emf.PolyBezierTo([(x+400,y+50),(x+300,y+150),(x+200,y+100)])

    emf.CloseFigure()
    emf.EndPath()

width=8
height=6
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


path(emf,"FillPath",0,0)
emf.FillPath()

path(emf,"StrokePath",800,0)
emf.StrokePath()

path(emf,"StrokePath,FillPath",0,800)
emf.StrokePath()
emf.FillPath()

path(emf,"FillPath,StrokePath",800,800)
emf.FillPath()
emf.StrokePath()

path(emf,"StrokeAndFillPath",1600,800)
emf.StrokeAndFillPath()


ret=emf.save("test-paths1.emf")
print "save returns %s" % str(ret)

