#!/usr/bin/env python

import pyemf

width=8
height=6
dpi=150

emf=pyemf.EMF(width,height,dpi,verbose=False)

thin=emf.CreatePen(pyemf.PS_SOLID,1,(0x01,0x02,0x03))


emf.SetBkColor((0,255,0))
emf.SetBkMode(pyemf.OPAQUE)
# set baseline for text to be bottom left corner
emf.SetTextAlign(pyemf.TA_BOTTOM|pyemf.TA_LEFT) 
emf.SetTextColor((0x00,0x00,0xff))
font = emf.CreateFont( -48, 0, 0, 0, pyemf.FW_NORMAL, 0, 0, 0, pyemf.ANSI_CHARSET,
                    pyemf.OUT_TT_PRECIS, pyemf.CLIP_TT_ALWAYS, pyemf.PROOF_QUALITY,
                    pyemf.DEFAULT_PITCH | pyemf.FF_DONTCARE, "Helvetica" );
emf.SelectObject(font)
emf.TextOut( 100, 100, "height=48");
emf.TextOut( 700, 100, "height=-48");
print "after Font";

emf.SelectObject(thin)

fontlist = ["Arial","Times New Roman","Andale Mono","Trebuchet MS","Georgia","Verdana","Courier New","Helvetica"]

fonty=200
fontheight=48
emf.SetTextColor((0x80,0x00,0x00))
for face in fontlist:

    emf.Polyline(((90,fonty-fontheight),(1200,fonty-fontheight)))
    emf.Polyline(((90,fonty-fontheight/2),(1200,fonty-fontheight/2)))
    emf.Polyline(((90,fonty),(1200,fonty)))

    font = emf.CreateFont( fontheight, 0, 0, 0, pyemf.FW_BOLD, 0, 0, 0,
                          pyemf.ANSI_CHARSET, pyemf.OUT_DEFAULT_PRECIS,
                          pyemf.CLIP_DEFAULT_PRECIS, pyemf.DEFAULT_QUALITY,
                          pyemf.DEFAULT_PITCH | pyemf.FF_DONTCARE, face);
    emf.SelectObject( font );
    emf.TextOut( 100, fonty, face)
    
    font = emf.CreateFont( -fontheight, 0, 0, 0, pyemf.FW_BOLD, 0, 0, 0,
                          pyemf.ANSI_CHARSET, pyemf.OUT_DEFAULT_PRECIS,
                          pyemf.CLIP_DEFAULT_PRECIS, pyemf.DEFAULT_QUALITY,
                          pyemf.DEFAULT_PITCH | pyemf.FF_DONTCARE, face);
    emf.SelectObject( font );
    emf.TextOut(700, fonty, face)

    
    print "after %s Font" % face
    fonty+=80;

emf.TextOut(0,fonty,"All text should be on a green background")

ret=emf.save("test10.emf")

