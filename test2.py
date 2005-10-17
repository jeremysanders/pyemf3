#!/usr/bin/env python

import pyemf

width=8
height=6
dpi=300
pointstopixels=dpi/72.0

emf=pyemf.EMF(width,height,dpi,verbose=True)
brush=emf.CreateSolidBrush((0xff,0x00,0xff))
emf.SelectObject(brush)
thick=emf.CreatePen(pyemf.PS_SOLID,10,(0x00,0xff,0x00))
dashed=emf.CreatePen(pyemf.PS_DASH,1,(0x00,0x00,0x00))
thin=emf.CreatePen(pyemf.PS_SOLID,1,(0x01,0x02,0x03))
emf.SelectObject(thick)

emf.Rectangle(0,0,320,640)
emf.Rectangle(0,0,100,100)
print "after Rectangle"
emf.Ellipse(200,200,400,400)
emf.Arc(400,400,600,600,600,600,600,600)
print "after Ellipse"
emf.SelectObject(dashed)

emf.Polyline(((1000,1000),(2000,0)))
p1=[(0,0),(width*dpi,height*dpi)]
p2=[(0,height*dpi),(width*dpi,0)]
emf.Polyline(p1)
emf.SelectObject(thin)
emf.Polyline(p2)
print "after Line"


points=[(0,100),(300,200),(0,300),(300,400),(0,500)]
emf.Polyline(points)
print "after Polyline"


brush=emf.CreateSolidBrush((0x00,0xff,0xff))
emf.SelectObject(brush)
points=[(200,200),(300,400),(100,400)]
emf.Polygon(points);
print "after Polygon"

dashedyellow=emf.CreatePen(pyemf.PS_DASH,1,(0xff,0xff,0x00))
emf.SelectObject(dashedyellow)
emf.BeginPath()
emf.MoveTo(220,220)
emf.LineTo(320,420)
emf.LineTo(120,420)

# Don't forget EndPath!  Subsequent graphics commands won't appear without it
emf.EndPath()
emf.StrokePath()
print "after StrokePath"


test1="Yellow Helvetica Test"
emf.SetBkMode(pyemf.TRANSPARENT)
# set baseline for text to be bottom left corner
emf.SetTextAlign(pyemf.TA_BOTTOM|pyemf.TA_LEFT) 
emf.SetTextColor((0xff,0xff,0x00))
font = emf.CreateFont( -12, 0, 0, 0, pyemf.FW_NORMAL, 0, 0, 0, pyemf.ANSI_CHARSET,
                    pyemf.OUT_TT_PRECIS, pyemf.CLIP_TT_ALWAYS, pyemf.PROOF_QUALITY,
                    pyemf.DEFAULT_PITCH | pyemf.FF_DONTCARE, "Helvetica" );
emf.SelectObject(font)
emf.TextOut( 50, 75, test1);
print "after Font";

emf.SelectObject(thin)

fontlist = ["Arial","Times New Roman","Andale Mono","Trebuchet MS","Georgia","Verdana","Courier New","Helvetica"]

fonty=100
emf.SetTextColor((0x00,0x00,0x00))
for face in fontlist:
    font = emf.CreateFont( 12, 0, 0, 0, pyemf.FW_BOLD, 0, 0, 0,
                          pyemf.ANSI_CHARSET, pyemf.OUT_DEFAULT_PRECIS,
                          pyemf.CLIP_DEFAULT_PRECIS, pyemf.DEFAULT_QUALITY,
                          pyemf.DEFAULT_PITCH | pyemf.FF_DONTCARE, face);
    emf.SelectObject( font );
    emf.TextOut( 100, fonty, face)
    
    font = emf.CreateFont( -12, 0, 0, 0, pyemf.FW_BOLD, 0, 0, 0,
                          pyemf.ANSI_CHARSET, pyemf.OUT_DEFAULT_PRECIS,
                          pyemf.CLIP_DEFAULT_PRECIS, pyemf.DEFAULT_QUALITY,
                          pyemf.DEFAULT_PITCH | pyemf.FF_DONTCARE, face);
    emf.SelectObject( font );
    emf.TextOut(300, fonty, face)

    emf.Polyline([(90,fonty),(320,fonty)])
    emf.Polyline(((90,fonty),(320,fonty)))
    
    print "after %s Font" % face
    fonty+=25;

ret=emf.save("test2.emf")
print "SaveEMF returns %d" % ret

