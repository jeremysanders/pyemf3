# Part of the pyemf library for handling EMF format files

# Copyright (C) 2005 Rob McMullen
# Copyright (C) 2016 Jeremy Sanders

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.

# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA  02110-1301, USA.

from __future__ import print_function, division

from .record import _EMR_UNKNOWN
from .field import *
from .constants import *
from .compat import cunicode

_emrmap = {}
def register(klass):
    """Register EMR with id."""
    _emrmap[klass.emr_id] = klass
    return klass

@register
class _HEADER(_EMR_UNKNOWN):
    """Header has different fields depending on the version of
    windows.  Also note that if offDescription==0, there is no
    description string."""

    emr_id=1
    typedef=[
        (Points(num=2),'rclBounds'),
        (Points(num=2),'rclFrame'),
        ('i','dSignature',1179469088),
        ('i','nVersion',0x10000),
        ('i','nBytes',0),
        ('i','nRecords',0),
        ('h','nHandles',0),
        ('h','sReserved',0),
        ('i','nDescription',0),
        ('i','offDescription',0),
        ('i','nPalEntries',0),
        (List(num=2),'szlDevice',[1024,768]),
        (List(num=2),'szlMillimeters',[320,240]),
        ('i','cbPixelFormat',0),
        ('i','offPixelFormat',0),
        ('i','bOpenGL',0),
        (List(num=2),'szlMicrometers'),
        (EMFString(num='nDescription',offset='offDescription'),'description'),
        ]

    def __init__(self,description=''):
        _EMR_UNKNOWN.__init__(self)
        print(self)
        print(self.__class__.format.default)
        # NOTE: rclBounds and rclFrame will be determined at
        # serialize time

        self.description = description
        if len(description)>0:
            self.description=u'pyemf'+u'\0'+description+u'\0\0'
        self.nDescription=len(self.description)

    def setBounds(self,dc,scaleheader):
        self.rclBounds=[[dc.bounds_left,dc.bounds_top],
                        [dc.bounds_right,dc.bounds_bottom]]
        self.rclFrame=[[dc.frame_left,dc.frame_top],
                       [dc.frame_right,dc.frame_bottom]]

        print(self)
        if scaleheader:
            self.szlDevice[0]=dc.pixelwidth
            self.szlDevice[1]=dc.pixelheight
            self.szlMicrometers[0]=dc.width*10
            self.szlMicrometers[1]=dc.height*10
        else:
            self.szlDevice[0]=dc.ref_pixelwidth
            self.szlDevice[1]=dc.ref_pixelheight
            self.szlMicrometers[0]=dc.ref_width*10
            self.szlMicrometers[1]=dc.ref_height*10

        self.szlMillimeters[0]=self.szlMicrometers[0]//1000
        self.szlMillimeters[1]=self.szlMicrometers[1]//1000

@register
class _POLYBEZIER(_EMR_UNKNOWN):
    emr_id=2
    typedef=[
        (Points(num=2),'rclBounds'),
        ('i','cptl'),
        (Points(num='cptl',fmt='i'),'aptl'),
        ]

    def __init__(self,points=[],bounds=((0,0),(0,0))):
        _EMR_UNKNOWN.__init__(self)
        self.setBounds(bounds)
        self.cptl=len(points)
        self.aptl=points

@register
class _POLYGON(_POLYBEZIER):
    emr_id=3

@register
class _POLYLINE(_POLYBEZIER):
    emr_id=4

@register
class _POLYBEZIERTO(_POLYBEZIER):
    emr_id=5

@register
class _POLYLINETO(_POLYBEZIERTO):
    emr_id=6

@register
class _POLYPOLYLINE(_EMR_UNKNOWN):
    emr_id=7
    typedef=[
        (Points(num=2),'rclBounds'),
        ('i','nPolys'),
        ('i','cptl'),
        (List(num='nPolys',fmt='i'),'aPolyCounts'),
        (Points(num='cptl',fmt='i'),'aptl'),
        ]

    def __init__(self,points=[],polycounts=[],bounds=((0,0),(0,0))):
        _EMR_UNKNOWN.__init__(self)
        self.setBounds(bounds)
        self.cptl=len(points)
        self.aptl=points
        self.nPolys=len(polycounts)
        self.aPolyCounts=polycounts

@register
class _POLYPOLYGON(_POLYPOLYLINE):
    emr_id=8

@register
class _SETWINDOWEXTEX(_EMR_UNKNOWN):
    emr_id=9
    typedef=[
        ('i','szlExtent_cx'),
        ('i','szlExtent_cy'),
        ]

    def __init__(self,cx=0,cy=0):
        _EMR_UNKNOWN.__init__(self)
        self.szlExtent_cx=cx
        self.szlExtent_cy=cy

@register
class _SETWINDOWORGEX(_EMR_UNKNOWN):
    emr_id=10
    typedef=[
        ('i','ptlOrigin_x'),
        ('i','ptlOrigin_y'),
        ]

    def __init__(self,x=0,y=0):
        _EMR_UNKNOWN.__init__(self)
        self.ptlOrigin_x=x
        self.ptlOrigin_y=y

@register
class _SETVIEWPORTEXTEX(_SETWINDOWEXTEX):
    emr_id=11

@register
class _SETVIEWPORTORGEX(_SETWINDOWORGEX):
    emr_id=12

@register
class _SETBRUSHORGEX(_SETWINDOWORGEX):
    emr_id=13

@register
class _EOF(_EMR_UNKNOWN):
    """End of file marker.  Usually 20 bytes long, but I have a
    Windows generated .emf file that only has a 12 byte long EOF
    record.  I don't know if that's a broken example or what, but
    both Windows progs and OpenOffice seem to handle it."""
    emr_id=14
    typedef=[
        ('i','nPalEntries',0),
        ('i','offPalEntries',0),
        ('i','nSizeLast',0)
        ]

    def __init__(self):
        _EMR_UNKNOWN.__init__(self)

@register
class _SETPIXELV(_EMR_UNKNOWN):
    emr_id=15
    typedef=[
        ('i','ptlPixel_x'),
        ('i','ptlPixel_y'),
        ('i','crColor')
        ]

    def __init__(self,x=0,y=0,color=0):
        _EMR_UNKNOWN.__init__(self)
        self.ptlPixel_x=x
        self.ptlPixel_y=y
        self.crColor=color

@register
class _SETMAPPERFLAGS(_EMR_UNKNOWN):
    emr_id=16
    emr_format=[('i','dwFlags',0)]

    def __init__(self):
        _EMR_UNKNOWN.__init__(self)

@register
class _SETMAPMODE(_EMR_UNKNOWN):
    emr_id=17
    typedef=[('i','iMode',MM_ANISOTROPIC)]

    def __init__(self,mode=MM_ANISOTROPIC,first=0,last=MM_MAX):
        _EMR_UNKNOWN.__init__(self)
        if mode<first or mode>last:
            self.error=1
        else:
            self.iMode=mode

@register
class _SETBKMODE(_SETMAPMODE):
    emr_id=18
    def __init__(self,mode=OPAQUE):
        _SETMAPMODE.__init__(self,mode,last=BKMODE_LAST)

@register
class _SETPOLYFILLMODE(_SETMAPMODE):
    emr_id=19
    def __init__(self,mode=ALTERNATE):
        _SETMAPMODE.__init__(self,mode,last=POLYFILL_LAST)

@register
class _SETROP2(_SETMAPMODE):
    emr_id=20

@register
class _SETSTRETCHBLTMODE(_SETMAPMODE):
    emr_id=21

@register
class _SETTEXTALIGN(_SETMAPMODE):
    emr_id=22
    def __init__(self,mode=TA_BASELINE):
        _SETMAPMODE.__init__(self,mode,last=TA_MASK)

#define EMR_SETCOLORADJUSTMENT	23

@register
class _SETTEXTCOLOR(_EMR_UNKNOWN):
    emr_id=24
    typedef=[('i','crColor',0)]

    def __init__(self,color=0):
        _EMR_UNKNOWN.__init__(self)
        self.crColor=color

@register
class _SETBKCOLOR(_SETTEXTCOLOR):
    emr_id=25

#define EMR_OFFSETCLIPRGN	26

@register
class _MOVETOEX(_EMR_UNKNOWN):
    emr_id=27
    typedef=[
        ('i','ptl_x'),
        ('i','ptl_y'),
        ]

    def __init__(self,x=0,y=0):
        _EMR_UNKNOWN.__init__(self)
        self.ptl_x=x
        self.ptl_y=y

    def getBounds(self):
        return ((self.ptl_x,self.ptl_y),(self.ptl_x,self.ptl_y))

#define EMR_SETMETARGN	28
#define EMR_EXCLUDECLIPRECT	29
#define EMR_INTERSECTCLIPRECT	30

@register
class _SCALEVIEWPORTEXTEX(_EMR_UNKNOWN):
    emr_id=31
    typedef=[
        ('i','xNum',1),
        ('i','xDenom',1),
        ('i','yNum',1),
        ('i','yDenom',1),
        ]

    def __init__(self,xn=1,xd=1,yn=1,yd=1):
        _EMR_UNKNOWN.__init__(self)
        self.xNum=xn
        self.xDenom=xd
        self.yNum=yn
        self.yDenom=yd

@register
class _SCALEWINDOWEXTEX(_SCALEVIEWPORTEXTEX):
    emr_id=32

@register
class _SAVEDC(_EMR_UNKNOWN):
    emr_id=33

@register
class _RESTOREDC(_EMR_UNKNOWN):
    emr_id=34
    typedef=[('i','iRelative')]

    def __init__(self,rel=-1):
        _EMR_UNKNOWN.__init__(self)
        self.iRelative=rel

@register
class _SETWORLDTRANSFORM(_EMR_UNKNOWN):
    emr_id=35
    typedef=[
        ('f','eM11'),
        ('f','eM12'),
        ('f','eM21'),
        ('f','eM22'),
        ('f','eDx'),
        ('f','eDy'),
        ]

    def __init__(self,em11=1.0,em12=0.0,em21=0.0,em22=1.0,edx=0.0,edy=0.0):
        _EMR_UNKNOWN.__init__(self)
        self.eM11=em11
        self.eM12=em12
        self.eM21=em21
        self.eM22=em22
        self.eDx=edx
        self.eDy=edy

@register
class _MODIFYWORLDTRANSFORM(_EMR_UNKNOWN):
    emr_id=36
    typedef=[
        ('f','eM11'),
        ('f','eM12'),
        ('f','eM21'),
        ('f','eM22'),
        ('f','eDx'),
        ('f','eDy'),
        ('i','iMode'),
        ]

    def __init__(self,em11=1.0,em12=0.0,em21=0.0,em22=1.0,edx=0.0,edy=0.0,mode=MWT_IDENTITY):
        _EMR_UNKNOWN.__init__(self)
        self.eM11=em11
        self.eM12=em12
        self.eM21=em21
        self.eM22=em22
        self.eDx=edx
        self.eDy=edy
        self.iMode=mode

@register
class _SELECTOBJECT(_EMR_UNKNOWN):
    """Select a brush, pen, font (or bitmap or region but there is
    no current user interface for those) object to be current and
    replace the previous item of that class.  Note that stock
    objects have their high order bit set, so the handle must be
    an unsigned int."""
    emr_id=37
    typedef=[('I','handle')]

    def __init__(self,dc=None,handle=0):
        _EMR_UNKNOWN.__init__(self)
        self.handle=handle

# Note: a line will still be drawn when the linewidth==0.  To force an
# invisible line, use style=PS_NULL
@register
class _CREATEPEN(_EMR_UNKNOWN):
    emr_id=38
    typedef=[
        ('i','handle',0),
        ('i','lopn_style'),
        ('i','lopn_width'),
        ('i','lopn_unused',0),
        ('i','lopn_color'),
        ]

    def __init__(self,style=PS_SOLID,width=1,color=0):
        _EMR_UNKNOWN.__init__(self)
        self.lopn_style=style
        self.lopn_width=width
        self.lopn_color=color

    def hasHandle(self):
        return True

@register
class _CREATEBRUSHINDIRECT(_EMR_UNKNOWN):
    emr_id=39
    typedef=[
        ('i','handle',0),
        ('I','lbStyle'),
        ('i','lbColor'),
        ('I','lbHatch'),
        ]

    def __init__(self,style=BS_SOLID,hatch=HS_HORIZONTAL,color=0):
        _EMR_UNKNOWN.__init__(self)
        self.lbStyle = style
        self.lbColor = color
        self.lbHatch = hatch

    def hasHandle(self):
        return True

@register
class _DELETEOBJECT(_SELECTOBJECT):
    emr_id=40

@register
class _ANGLEARC(_EMR_UNKNOWN):
    emr_id=41
    typedef=[
        ('i','ptlCenter_x'),
        ('i','ptlCenter_y'),
        ('i','nRadius'),
        ('f','eStartAngle'),
        ('f','eSweepAngle'),
        ]

    def __init__(self):
        _EMR_UNKNOWN.__init__(self)

@register
class _ELLIPSE(_EMR_UNKNOWN):
    emr_id=42
    typedef=[
        (Points(num=2),'rclBox'),
        ]

    def __init__(self,box=((0,0),(0,0))):
        _EMR_UNKNOWN.__init__(self)
        self.rclBox=[[box[0][0],box[0][1]],[box[1][0],box[1][1]]]

@register
class _RECTANGLE(_ELLIPSE):
    emr_id=43

@register
class _ROUNDRECT(_EMR_UNKNOWN):
    emr_id=44
    typedef=[
        (Points(num=2),'rclBox'),
        ('i','szlCorner_cx'),
        ('i','szlCorner_cy')
        ]

    def __init__(self,box=((0,0),(0,0)),cx=0,cy=0):
        _EMR_UNKNOWN.__init__(self)
        self.rclBox=[[box[0][0],box[0][1]],[box[1][0],box[1][1]]]
        self.szlCorner_cx=cx
        self.szlCorner_cy=cy

@register
class _ARC(_EMR_UNKNOWN):
    emr_id=45
    typedef=[
        (Points(num=2),'rclBox'),
        ('i','ptlStart_x'),
        ('i','ptlStart_y'),
        ('i','ptlEnd_x'),
        ('i','ptlEnd_y')]

    def __init__(self,box=((0,0),(0,0)),
                 xstart=0,ystart=0,xend=0,yend=0):
        _EMR_UNKNOWN.__init__(self)
        self.rclBox=[[box[0][0],box[0][1]],[box[1][0],box[1][1]]]
        self.ptlStart_x=xstart
        self.ptlStart_y=ystart
        self.ptlEnd_x=xend
        self.ptlEnd_y=yend

@register
class _CHORD(_ARC):
    emr_id=46

@register
class _PIE(_ARC):
    emr_id=47

@register
class _SELECTPALETTE(_EMR_UNKNOWN):
    emr_id=48
    typedef=[('i','handle')]

    def __init__(self):
        _EMR_UNKNOWN.__init__(self)

# Stub class for palette
@register
class _CREATEPALETTE(_EMR_UNKNOWN):
    emr_id=49
    typedef=[('i','handle',0)]

    def __init__(self):
        _EMR_UNKNOWN.__init__(self)

    def hasHandle(self):
        return True

#define EMR_SETPALETTEENTRIES	50
#define EMR_RESIZEPALETTE	51
#define EMR_REALIZEPALETTE	52
#define EMR_EXTFLOODFILL	53

@register
class _LINETO(_MOVETOEX):
    emr_id=54

@register
class _ARCTO(_ARC):
    emr_id=55

    def getBounds(self):
        # not exactly the bounds, because the arc may actually use
        # less of the ellipse than is specified by the bounds.
        # But at least the actual bounds aren't outside these
        # bounds.
        return self.rclBox

#define EMR_POLYDRAW	56

@register
class _SETARCDIRECTION(_EMR_UNKNOWN):
    emr_id=57
    typedef=[('i','iArcDirection')]
    def __init__(self):
        _EMR_UNKNOWN.__init__(self)

#define EMR_SETMITERLIMIT	58

@register
class _BEGINPATH(_EMR_UNKNOWN):
    emr_id=59

@register
class _ENDPATH(_EMR_UNKNOWN):
    emr_id=60

@register
class _CLOSEFIGURE(_EMR_UNKNOWN):
    emr_id=61

@register
class _FILLPATH(_EMR_UNKNOWN):
    emr_id=62
    typedef=[(Points(num=2),'rclBounds')]

    def __init__(self,bounds=((0,0),(0,0))):
        _EMR_UNKNOWN.__init__(self)
        self.setBounds(bounds)

@register
class _STROKEANDFILLPATH(_FILLPATH):
    emr_id=63

@register
class _STROKEPATH(_FILLPATH):
    emr_id=64

@register
class _FLATTENPATH(_EMR_UNKNOWN):
    emr_id=65

@register
class _WIDENPATH(_EMR_UNKNOWN):
    emr_id=66

@register
class _SELECTCLIPPATH(_SETMAPMODE):
    """Select the current path and make it the clipping region.
    Must be a closed path.

    @gdi: SelectClipPath
    """
    emr_id=67
    def __init__(self,mode=RGN_COPY):
        _SETMAPMODE.__init__(self,mode,first=RGN_MIN,last=RGN_MAX)

@register
class _ABORTPATH(_EMR_UNKNOWN):
    """Discards any current path, whether open or closed.

    @gdi: AbortPath"""
    emr_id=68

#define EMR_GDICOMMENT	70
#define EMR_FILLRGN	71
#define EMR_FRAMERGN	72
#define EMR_INVERTRGN	73
#define EMR_PAINTRGN	74
#define EMR_EXTSELECTCLIPRGN	75
#define EMR_BITBLT	76
#define EMR_STRETCHBLT	77
#define EMR_MASKBLT	78
#define EMR_PLGBLT	79
#define EMR_SETDIBITSTODEVICE	80

@register
class _STRETCHDIBITS(_EMR_UNKNOWN):
    """Copies the image from the source image to the destination
    image.  DIB is currently an opaque format to me, but
    apparently it has been extented recently to allow JPG and PNG
    images...

    @gdi: StretchDIBits
    """
    emr_id=81
    typedef=[
        (Points(num=2),'rclBounds'),
        ('i','xDest'),
        ('i','yDest'),
        ('i','xSrc'),
        ('i','ySrc'),
        ('i','cxSrc'),
        ('i','cySrc'),
        ('i','offBmiSrc'),
        ('i','cbBmiSrc'),
        ('i','offBitsSrc'),
        ('i','cbBitsSrc'),
        ('i','iUsageSrc'),
        ('i','dwRop'),
        ('i','cxDest'),
        ('i','cyDest')]

    def __init__(self):
        _EMR_UNKNOWN.__init__(self)

@register
class _EXTCREATEFONTINDIRECTW(_EMR_UNKNOWN):
    # Note: all the strings here (font names, etc.) are unicode
    # strings.

    emr_id=82
    typedef=[
        ('i','handle'),
        ('i','lfHeight'),
        ('i','lfWidth'),
        ('i','lfEscapement'),
        ('i','lfOrientation'),
        ('i','lfWeight'),
        ('B','lfItalic'),
        ('B','lfUnderline'),
        ('B','lfStrikeOut'),
        ('B','lfCharSet'),
        ('B','lfOutPrecision'),
        ('B','lfClipPrecision'),
        ('B','lfQuality'),
        ('B','lfPitchAndFamily'),
        (EMFString(num=32,size=2),'lfFaceName'),
        #            ('64s','lfFaceName',), # really a 32 char unicode string
        (EMFString(num=64,size=2),'elfFullName'),
        #            ('128s','elfFullName','\0'*128), # really 64 char unicode str
        (EMFString(num=32,size=2),'elfStyle'),
        #            ('64s','elfStyle','\0'*64), # really 32 char unicode str
        ('i','elfVersion',0),
        ('i','elfStyleSize',0),
        ('i','elfMatch',0),
        ('i','elfReserved',0),
        ('i','elfVendorId',0),
        ('i','elfCulture',0),
        ('B','elfPanose_bFamilyType',1),
        ('B','elfPanose_bSerifStyle',1),
        ('B','elfPanose_bWeight',1),
        ('B','elfPanose_bProportion',1),
        ('B','elfPanose_bContrast',1),
        ('B','elfPanose_bStrokeVariation',1),
        ('B','elfPanose_bArmStyle',1),
        ('B','elfPanose_bLetterform',1),
        ('B','elfPanose_bMidline',1),
        ('B','elfPanose_bXHeight',1)]

    def __init__(self,height=0,width=0,escapement=0,orientation=0,
                 weight=FW_NORMAL,italic=0,underline=0,strike_out=0,
                 charset=ANSI_CHARSET,out_precision=OUT_DEFAULT_PRECIS,
                 clip_precision=CLIP_DEFAULT_PRECIS,
                 quality=DEFAULT_QUALITY,
                 pitch_family=DEFAULT_PITCH|FF_DONTCARE,name='Times New Roman'):
        _EMR_UNKNOWN.__init__(self)
        self.lfHeight=height
        self.lfWidth=width
        self.lfEscapement=escapement
        self.lfOrientation=orientation
        self.lfWeight=weight
        self.lfItalic=italic
        self.lfUnderline=underline
        self.lfStrikeOut=strike_out
        self.lfCharSet=charset
        self.lfOutPrecision=out_precision
        self.lfClipPrecision=clip_precision
        self.lfQuality=quality
        self.lfPitchAndFamily=pitch_family

        # pad the structure out to 4 byte boundary
        self.unhandleddata=_EMR_UNKNOWN.twobytepadding

        # truncate or pad to exactly 32 characters
        if len(name)>32:
            name=name[0:32]
        else:
            name+='\0'*(32-len(name))
        self.lfFaceName=name.encode('utf-16le')
        # print "lfFaceName=%s" % self.lfFaceName

    def hasHandle(self):
        return True

@register
class _EXTTEXTOUTA(_EMR_UNKNOWN):
    emr_id=83
    typedef=[
        (Points(num=2),'rclBounds',[[0,0],[-1,-1]]),
        ('i','iGraphicsMode',GM_COMPATIBLE),
        ('f','exScale',1.0),
        ('f','eyScale',1.0),
        ('i','ptlReference_x'),
        ('i','ptlReference_y'),
        ('i','nChars'),
        ('i','offString',0),
        ('i','fOptions',0),
        (Points(num=2),'rcl',[[0,0],[-1,-1]]),
        ('i','offDx',0),
        (List(num='nChars',fmt='i',offset='offDx'),'dx'),
        (EMFString(num='nChars',size=1,offset='offString'),'string'),
        ]
    def __init__(self,x=0,y=0,txt=""):
        _EMR_UNKNOWN.__init__(self)
        self.ptlReference_x=x
        self.ptlReference_y=y
        if isinstance(txt,cunicode):
            self.string=txt.encode('utf-16le')
        else:
            self.string=txt
        self.charsize=1
        self.dx=[]

@register
class _EXTTEXTOUTW(_EXTTEXTOUTA):
    emr_id=84
    typedef=[
        (Points(num=2),'rclBounds',[[0,0],[-1,-1]]),
        ('i','iGraphicsMode',GM_COMPATIBLE),
        ('f','exScale',1.0),
        ('f','eyScale',1.0),
        ('i','ptlReference_x'),
        ('i','ptlReference_y'),
        ('i','nChars'),
        ('i','offString',0),
        ('i','fOptions',0),
        (Points(num=2),'rcl',[[0,0],[-1,-1]]),
        ('i','offDx',0),
        (List(num='nChars',fmt='i',offset='offDx'),'dx'),
        (EMFString(num='nChars',size=2,offset='offString'),'string'),
        ]

    def __init__(self,x=0,y=0,txt=u''):
        _EXTTEXTOUTA.__init__(self,x,y,txt)
        self.charsize=2

@register
class _POLYBEZIER16(_POLYBEZIER):
    emr_id=85
    typedef=[
        (Points(num=2),'rclBounds'),
        ('i','cptl'),
        (Points(num='cptl',fmt='h'),'aptl'),
        ]

@register
class _POLYGON16(_POLYBEZIER16):
    emr_id=86

@register
class _POLYLINE16(_POLYBEZIER16):
    emr_id=87

@register
class _POLYBEZIERTO16(_POLYBEZIERTO):
    emr_id=88
    typedef=[
        (Points(num=2),'rclBounds'),
        ('i','cptl'),
        (Points(num='cptl',fmt='h'),'aptl'),
        ]

@register
class _POLYLINETO16(_POLYBEZIERTO16):
    emr_id=89

@register
class _POLYPOLYLINE16(_POLYPOLYLINE):
    emr_id=90
    typedef=[
        (Points(num=2),'rclBounds'),
        ('i','nPolys'),
        ('i','cptl'),
        (List(num='nPolys',fmt='i'),'aPolyCounts'),
        (Points(num='cptl',fmt='h'),'aptl'),
        ]

@register
class _POLYPOLYGON16(_POLYPOLYLINE16):
    emr_id=91

#define EMR_POLYDRAW16	92

# Stub class for storage of brush with monochrome bitmap or DIB
@register
class _CREATEMONOBRUSH(_CREATEPALETTE):
    emr_id=93

# Stub class for device independent bitmap brush
@register
class _CREATEDIBPATTERNBRUSHPT(_CREATEPALETTE):
    emr_id=94

# Stub class for extended pen
@register
class _EXTCREATEPEN(_CREATEPALETTE):
    emr_id=95

#define EMR_POLYTEXTOUTA	96
#define EMR_POLYTEXTOUTW	97

@register
class _SETICMMODE(_SETMAPMODE):
    """Set or query the current color management mode.

    @gdi: SetICMMode
    """
    emr_id=98
    def __init__(self,mode=ICM_OFF):
        _SETMAPMODE.__init__(self,mode,first=ICM_MIN,last=ICM_MAX)

#define EMR_CREATECOLORSPACE	99
#define EMR_SETCOLORSPACE	100
#define EMR_DELETECOLORSPACE	101
#define EMR_GLSRECORD	102
#define EMR_GLSBOUNDEDRECORD	103
#define EMR_PIXELFORMAT 104
#define EMR_DRAWESCAPE    105
#define EMR_EXTESCAPE     106
#define EMR_STARTDOC      107
#define EMR_SMALLTEXTOUT  108
#define EMR_FORCEUFIMAPPING       109
#define EMR_NAMEDESCAPE   110
#define EMR_COLORCORRECTPALETTE   111
#define EMR_SETICMPROFILEA        112
#define EMR_SETICMPROFILEW        113
#define EMR_ALPHABLEND    114
#define EMR_SETLAYOUT     115
#define EMR_TRANSPARENTBLT        116
#define EMR_RESERVED_117  117
#define EMR_GRADIENTFILL  118
#define EMR_SETLINKEDUFI  119
#define EMR_SETTEXTJUSTIFICATION  120
#define EMR_COLORMATCHTOTARGETW   121
#define EMR_CREATECOLORSPACEW     122
