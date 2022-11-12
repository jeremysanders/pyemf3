import os
import struct

from . import const
from .field import Record, EMFString, List, Tuples, Points

emrmap={}
def register_emr(klass):
    emrmap[klass.emr_id] = klass
    return klass

class EMR_UNKNOWN(Record): # extend from new-style class, or __getattr__ doesn't work
    """baseclass for EMR objects"""
    emr_id=0

    twobytepadding=b'\0'*2

    def __init__(self):
        Record.__init__(self)
        self.nSize=0
        self.iType=self.__class__.emr_id

        self.verbose=False

        self.datasize=0
        self.data=None
        self.unhandleddata=None

        # error code.  Currently just used as a boolean
        self.error=0

    def hasHandle(self):
        """Return true if this object has a handle that needs to be
        saved in the object array for later recall by SelectObject."""
        return False

    def setBounds(self,bounds):
        """Set bounds of object.  Depends on naming convention always
        defining the bounding rectangle as
        rclBounds_[left|top|right|bottom]."""
        self.rclBounds=[[bounds[0][0],bounds[0][1]],[bounds[1][0],bounds[1][1]]]

    def getBounds(self):
        """Return bounds of object, or None if not applicable."""
        if 'rclBounds' in self.values:
            return self.rclBounds
        return None

    def unserialize(self,fh,already_read,itype=-1,nsize=-1):
        """Read data from the file object and, using the format
        structure defined by the subclass, parse the data and store it
        in self.values[] list."""
        prevlen=len(already_read)

        if itype>0:
            self.iType=itype
            self.nSize=nsize
        else:
            (self.iType,self.nSize)=struct.unpack("<ii",already_read)
        if self.nSize>prevlen:
            self.data=already_read+fh.read(self.nSize-prevlen)
            last=self.format.unpack(self.data,self,prevlen)
            if self.nSize>last:
                self.unserializeExtra(self.data[last:])

    def unserializeExtra(self,data):
        """Hook for subclasses to handle extra data in the record that
        isn't specified by the format statement."""
        self.unhandleddata=data
        pass

    def serialize(self,fh):
        try:
            #print "packing!"
            bytestr=self.format.pack(self.values,self,8)
            #fh.write(struct.pack(self.format.fmt,*self.values))
        except struct.error:
            print("!!!!!Struct error:", end=' ')
            print(self)
            raise
        before=self.nSize
        self.nSize=8+len(bytestr)+self.sizeExtra()
        if self.verbose and before!=self.nSize:
            print("resize: before=%d after=%d" % (before,self.nSize), end=' ')
            print(self)
        if self.nSize%4 != 0:
            print("size error--must be divisible by 4. before=%d after=%d calcNumBytes=%d extra=%d" % (before,self.nSize,len(bytestr),self.sizeExtra()))
            for name in self.format.names:
                fmt=self.format.fmtmap[name]
                size=fmt.calcNumBytes(self,name)
                print("  name=%s size=%s" % (name,size))
            print(self)
            raise TypeError
        fh.write(struct.pack("<ii",self.iType,self.nSize))
        fh.write(bytestr)
        self.serializeExtra(fh)

    def serializeExtra(self,fh):
        """This is for special cases, like writing text or lists.  If
        this is not overridden by a subclass method, it will write out
        anything in the self.unhandleddata string."""
        if self.unhandleddata:
            fh.write(self.unhandleddata)

    def resize(self):
        before=self.nSize
        self.nSize=8+self.format.calcNumBytes(self)+self.sizeExtra()
        if self.verbose and before!=self.nSize:
            print("resize: before=%d after=%d" % (before,self.nSize), end=' ')
            print(self)
        if self.nSize%4 != 0:
            print("size error--must be divisible by 4. before=%d after=%d calcNumBytes=%d extra=%d" % (before,self.nSize,self.format.calcNumBytes(self),self.sizeExtra()))
            for name in self.format.names:
                fmt=self.format.fmtmap[name]
                size=fmt.calcNumBytes(self,name)
                print("  name=%s size=%s" % (name,size))
            print(self)
            raise TypeError

    def sizeExtra(self):
        """Hook for subclasses before anything is serialized.  This is
        used to return the size of any extra components not in the
        format string, and also provide the opportunity to recalculate
        any changes in size that should be reflected in self.nSize
        before the record is written out."""
        if self.unhandleddata:
            return len(self.unhandleddata)
        return 0

    def __str__(self):
        ret=""
        details=self.format.getString(self)
        if details:
            ret=os.linesep
        return "**%s: iType=%s nSize=%s  struct='%s' size=%d extra=%d\n%s%s" % (self.__class__.__name__.lstrip('_'),self.iType,self.nSize,self.format.fmt,self.format.minstructsize,self.sizeExtra(),details,ret)
        return

@register_emr
class HEADER(EMR_UNKNOWN):
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
        EMR_UNKNOWN.__init__(self)
        #print(self)
        #print(self.__class__.format.default)
        # NOTE: rclBounds and rclFrame will be determined at
        # serialize time

        self.description = description
        if len(description)>0:
            self.description='pyemf 2.0.0\0'+description+'\0\0'
        self.nDescription=len(self.description)

    def setBounds(self,dc,scaleheader):
        self.rclBounds=[
            [dc.bounds_left,dc.bounds_top],
            [dc.bounds_right,dc.bounds_bottom]
        ]
        self.rclFrame=[
            [dc.frame_left,dc.frame_top],
            [dc.frame_right,dc.frame_bottom]
        ]

        #print(self)
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


@register_emr
class POLYBEZIER(EMR_UNKNOWN):
    emr_id=2
    typedef=[
        (Points(num=2),'rclBounds'),
        ('i','cptl'),
        (Points(num='cptl',fmt='i'),'aptl'),
        ]

    def __init__(self,points=[],bounds=((0,0),(0,0))):
        EMR_UNKNOWN.__init__(self)
        self.setBounds(bounds)
        self.cptl=len(points)
        self.aptl=points


@register_emr
class POLYGON(POLYBEZIER):
    emr_id=3
    pass

@register_emr
class POLYLINE(POLYBEZIER):
    emr_id=4
    pass

@register_emr
class POLYBEZIERTO(POLYBEZIER):
    emr_id=5
    pass

@register_emr
class POLYLINETO(POLYBEZIERTO):
    emr_id=6
    pass



@register_emr
class POLYPOLYLINE(EMR_UNKNOWN):
    emr_id=7
    typedef=[
        (Points(num=2),'rclBounds'),
        ('i','nPolys'),
        ('i','cptl'),
        (List(num='nPolys',fmt='i'),'aPolyCounts'),
        (Points(num='cptl',fmt='i'),'aptl'),
        ]

    def __init__(self,points=[],polycounts=[],bounds=((0,0),(0,0))):
        EMR_UNKNOWN.__init__(self)
        self.setBounds(bounds)
        self.cptl=len(points)
        self.aptl=points
        self.nPolys=len(polycounts)
        self.aPolyCounts=polycounts


@register_emr
class POLYPOLYGON(POLYPOLYLINE):
    emr_id=8
    pass

@register_emr
class SETWINDOWEXTEX(EMR_UNKNOWN):
    emr_id=9
    typedef=[
        ('i','szlExtent_cx'),
        ('i','szlExtent_cy'),
        ]

    def __init__(self,cx=0,cy=0):
        EMR_UNKNOWN.__init__(self)
        self.szlExtent_cx=cx
        self.szlExtent_cy=cy

@register_emr
class SETWINDOWORGEX(EMR_UNKNOWN):
    emr_id=10
    typedef=[
        ('i','ptlOrigin_x'),
        ('i','ptlOrigin_y'),
        ]

    def __init__(self,x=0,y=0):
        EMR_UNKNOWN.__init__(self)
        self.ptlOrigin_x=x
        self.ptlOrigin_y=y

@register_emr
class SETVIEWPORTEXTEX(SETWINDOWEXTEX):
    emr_id=11
    pass

@register_emr
class SETVIEWPORTORGEX(SETWINDOWORGEX):
    emr_id=12
    pass

@register_emr
class SETBRUSHORGEX(SETWINDOWORGEX):
    emr_id=13
    pass

@register_emr
class EOF(EMR_UNKNOWN):
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
        EMR_UNKNOWN.__init__(self)

@register_emr
class SETPIXELV(EMR_UNKNOWN):
    emr_id=15
    typedef=[
        ('i','ptlPixel_x'),
        ('i','ptlPixel_y'),
        ('i','crColor')
        ]

    def __init__(self,x=0,y=0,color=0):
        EMR_UNKNOWN.__init__(self)
        self.ptlPixel_x=x
        self.ptlPixel_y=y
        self.crColor=color

@register_emr
class SETMAPPERFLAGS(EMR_UNKNOWN):
    emr_id=16
    emr_format=[('i','dwFlags',0)]

    def __init__(self):
        EMR_UNKNOWN.__init__(self)

@register_emr
class SETMAPMODE(EMR_UNKNOWN):
    emr_id=17
    typedef=[('i','iMode',const.MM_ANISOTROPIC)]

    def __init__(self,mode=const.MM_ANISOTROPIC,first=0,last=const.MM_MAX):
        EMR_UNKNOWN.__init__(self)
        if mode<first or mode>last:
            self.error=1
        else:
            self.iMode=mode

@register_emr
class SETBKMODE(SETMAPMODE):
    emr_id=18
    def __init__(self,mode=const.OPAQUE):
        SETMAPMODE.__init__(self,mode,last=const.BKMODE_LAST)

@register_emr
class SETPOLYFILLMODE(SETMAPMODE):
    emr_id=19
    def __init__(self,mode=const.ALTERNATE):
        SETMAPMODE.__init__(self,mode,last=const.POLYFILL_LAST)

@register_emr
class SETROP2(SETMAPMODE):
    emr_id=20
    pass

@register_emr
class SETSTRETCHBLTMODE(SETMAPMODE):
    emr_id=21
    pass

@register_emr
class SETTEXTALIGN(SETMAPMODE):
    emr_id=22
    def __init__(self,mode=const.TA_BASELINE):
        SETMAPMODE.__init__(self,mode,last=const.TA_MASK)


#define EMR_SETCOLORADJUSTMENT	23

@register_emr
class SETTEXTCOLOR(EMR_UNKNOWN):
    emr_id=24
    typedef=[('i','crColor',0)]

    def __init__(self,color=0):
        EMR_UNKNOWN.__init__(self)
        self.crColor=color

@register_emr
class SETBKCOLOR(SETTEXTCOLOR):
    emr_id=25
    pass


#define EMR_OFFSETCLIPRGN	26

@register_emr
class MOVETOEX(EMR_UNKNOWN):
    emr_id=27
    typedef=[
        ('i','ptl_x'),
        ('i','ptl_y'),
        ]

    def __init__(self,x=0,y=0):
        EMR_UNKNOWN.__init__(self)
        self.ptl_x=x
        self.ptl_y=y

    def getBounds(self):
        return ((self.ptl_x,self.ptl_y),(self.ptl_x,self.ptl_y))


#define EMR_SETMETARGN	28
#define EMR_EXCLUDECLIPRECT	29
#define EMR_INTERSECTCLIPRECT	30

@register_emr
class SCALEVIEWPORTEXTEX(EMR_UNKNOWN):
    emr_id=31
    typedef=[
        ('i','xNum',1),
        ('i','xDenom',1),
        ('i','yNum',1),
        ('i','yDenom',1),
        ]

    def __init__(self,xn=1,xd=1,yn=1,yd=1):
        EMR_UNKNOWN.__init__(self)
        self.xNum=xn
        self.xDenom=xd
        self.yNum=yn
        self.yDenom=yd

@register_emr
class SCALEWINDOWEXTEX(SCALEVIEWPORTEXTEX):
    emr_id=32

@register_emr
class SAVEDC(EMR_UNKNOWN):
    emr_id=33

@register_emr
class RESTOREDC(EMR_UNKNOWN):
    emr_id=34
    typedef=[('i','iRelative')]

    def __init__(self,rel=-1):
        EMR_UNKNOWN.__init__(self)
        self.iRelative=rel

@register_emr
class SETWORLDTRANSFORM(EMR_UNKNOWN):
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
        EMR_UNKNOWN.__init__(self)
        self.eM11=em11
        self.eM12=em12
        self.eM21=em21
        self.eM22=em22
        self.eDx=edx
        self.eDy=edy

@register_emr
class MODIFYWORLDTRANSFORM(EMR_UNKNOWN):
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

    def __init__(self,em11=1.0,em12=0.0,em21=0.0,em22=1.0,edx=0.0,edy=0.0,mode=const.MWT_IDENTITY):
        EMR_UNKNOWN.__init__(self)
        self.eM11=em11
        self.eM12=em12
        self.eM21=em21
        self.eM22=em22
        self.eDx=edx
        self.eDy=edy
        self.iMode=mode

@register_emr
class SELECTOBJECT(EMR_UNKNOWN):
    """Select a brush, pen, font (or bitmap or region but there is
    no current user interface for those) object to be current and
    replace the previous item of that class.  Note that stock
    objects have their high order bit set, so the handle must be
    an unsigned int."""
    emr_id=37
    typedef=[('I','handle')]

    def __init__(self,dc=None,handle=0):
        EMR_UNKNOWN.__init__(self)
        self.handle=handle


# Note: a line will still be drawn when the linewidth==0.  To force an
# invisible line, use style=PS_NULL
@register_emr
class CREATEPEN(EMR_UNKNOWN):
    emr_id=38
    typedef=[
        ('i','handle',0),
        ('i','lopn_style'),
        ('i','lopn_width'),
        ('i','lopn_unused',0),
        ('i','lopn_color'),
        ]

    def __init__(self,style=const.PS_SOLID,width=1,color=0):
        EMR_UNKNOWN.__init__(self)
        self.lopn_style=style
        self.lopn_width=width
        self.lopn_color=color

    def hasHandle(self):
        return True

@register_emr
class CREATEBRUSHINDIRECT(EMR_UNKNOWN):
    emr_id=39
    typedef=[
        ('i','handle',0),
        ('I','lbStyle'),
        ('i','lbColor'),
        ('I','lbHatch'),
        ]

    def __init__(self,style=const.BS_SOLID,hatch=const.HS_HORIZONTAL,color=0):
        EMR_UNKNOWN.__init__(self)
        self.lbStyle = style
        self.lbColor = color
        self.lbHatch = hatch

    def hasHandle(self):
        return True

@register_emr
class DELETEOBJECT(SELECTOBJECT):
    emr_id=40
    pass

@register_emr
class ANGLEARC(EMR_UNKNOWN):
    emr_id=41
    typedef=[
        ('i','ptlCenter_x'),
        ('i','ptlCenter_y'),
        ('i','nRadius'),
        ('f','eStartAngle'),
        ('f','eSweepAngle'),
        ]

    def __init__(self):
        EMR_UNKNOWN.__init__(self)

@register_emr
class ELLIPSE(EMR_UNKNOWN):
    emr_id=42
    typedef=[
        (Points(num=2),'rclBox'),
        ]

    def __init__(self,box=((0,0),(0,0))):
        EMR_UNKNOWN.__init__(self)
        self.rclBox=[[box[0][0],box[0][1]],[box[1][0],box[1][1]]]

@register_emr
class RECTANGLE(ELLIPSE):
    emr_id=43

@register_emr
class ROUNDRECT(EMR_UNKNOWN):
    emr_id=44
    typedef=[
        (Points(num=2),'rclBox'),
        ('i','szlCorner_cx'),
        ('i','szlCorner_cy')
        ]

    def __init__(self,box=((0,0),(0,0)),cx=0,cy=0):
        EMR_UNKNOWN.__init__(self)
        self.rclBox=[[box[0][0],box[0][1]],[box[1][0],box[1][1]]]
        self.szlCorner_cx=cx
        self.szlCorner_cy=cy

@register_emr
class ARC(EMR_UNKNOWN):
    emr_id=45
    typedef=[
        (Points(num=2),'rclBox'),
        ('i','ptlStart_x'),
        ('i','ptlStart_y'),
        ('i','ptlEnd_x'),
        ('i','ptlEnd_y')]

    def __init__(self,box=((0,0),(0,0)),
                 xstart=0,ystart=0,xend=0,yend=0):
        EMR_UNKNOWN.__init__(self)
        self.rclBox=[[box[0][0],box[0][1]],[box[1][0],box[1][1]]]
        self.ptlStart_x=xstart
        self.ptlStart_y=ystart
        self.ptlEnd_x=xend
        self.ptlEnd_y=yend

@register_emr
class CHORD(ARC):
    emr_id=46


@register_emr
class PIE(ARC):
    emr_id=47


@register_emr
class SELECTPALETTE(EMR_UNKNOWN):
    emr_id=48
    typedef=[('i','handle')]

    def __init__(self):
        EMR_UNKNOWN.__init__(self)


# Stub class for palette
@register_emr
class CREATEPALETTE(EMR_UNKNOWN):
    emr_id=49
    typedef=[('i','handle',0)]

    def __init__(self):
        EMR_UNKNOWN.__init__(self)

    def hasHandle(self):
        return True


#define EMR_SETPALETTEENTRIES	50
#define EMR_RESIZEPALETTE	51
#define EMR_REALIZEPALETTE	52
#define EMR_EXTFLOODFILL	53


@register_emr
class LINETO(MOVETOEX):
    emr_id=54
    pass


@register_emr
class ARCTO(ARC):
    emr_id=55

    def getBounds(self):
        # not exactly the bounds, because the arc may actually use
        # less of the ellipse than is specified by the bounds.
        # But at least the actual bounds aren't outside these
        # bounds.
        return self.rclBox



#define EMR_POLYDRAW	56


@register_emr
class SETARCDIRECTION(EMR_UNKNOWN):
    emr_id=57
    typedef=[('i','iArcDirection')]
    def __init__(self):
        EMR_UNKNOWN.__init__(self)



#define EMR_SETMITERLIMIT	58


@register_emr
class BEGINPATH(EMR_UNKNOWN):
    emr_id=59
    pass


@register_emr
class ENDPATH(EMR_UNKNOWN):
    emr_id=60
    pass


@register_emr
class CLOSEFIGURE(EMR_UNKNOWN):
    emr_id=61
    pass


@register_emr
class FILLPATH(EMR_UNKNOWN):
    emr_id=62
    typedef=[(Points(num=2),'rclBounds')]

    def __init__(self,bounds=((0,0),(0,0))):
        EMR_UNKNOWN.__init__(self)
        self.setBounds(bounds)


@register_emr
class STROKEANDFILLPATH(FILLPATH):
    emr_id=63
    pass


@register_emr
class STROKEPATH(FILLPATH):
    emr_id=64
    pass


@register_emr
class FLATTENPATH(EMR_UNKNOWN):
    emr_id=65
    pass


@register_emr
class WIDENPATH(EMR_UNKNOWN):
    emr_id=66
    pass


@register_emr
class SELECTCLIPPATH(SETMAPMODE):
    """Select the current path and make it the clipping region.
    Must be a closed path.

    @gdi: SelectClipPath
    """
    emr_id=67
    def __init__(self,mode=const.RGN_COPY):
        SETMAPMODE.__init__(self,mode,first=const.RGN_MIN,last=const.RGN_MAX)


@register_emr
class ABORTPATH(EMR_UNKNOWN):
    """Discards any current path, whether open or closed.

    @gdi: AbortPath"""
    emr_id=68
    pass


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

@register_emr
class STRETCHDIBITS(EMR_UNKNOWN):
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
        EMR_UNKNOWN.__init__(self)


@register_emr
class EXTCREATEFONTINDIRECTW(EMR_UNKNOWN):
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
                 weight=const.FW_NORMAL,italic=0,underline=0,strike_out=0,
                 charset=const.ANSI_CHARSET,out_precision=const.OUT_DEFAULT_PRECIS,
                 clip_precision=const.CLIP_DEFAULT_PRECIS,
                 quality=const.DEFAULT_QUALITY,
                 pitch_family=const.DEFAULT_PITCH|const.FF_DONTCARE,name='Times New Roman'):
        EMR_UNKNOWN.__init__(self)
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
        self.unhandleddata=EMR_UNKNOWN.twobytepadding

        # truncate or pad to exactly 32 characters
        if len(name)>32:
            name=name[0:32]
        else:
            name+='\0'*(32-len(name))
        self.lfFaceName=name
        # print "lfFaceName=%s" % self.lfFaceName

    def hasHandle(self):
        return True


@register_emr
class EXTTEXTOUTA(EMR_UNKNOWN):
    """ASCII-encoded text."""
    emr_id=83
    typedef=[
        (Points(num=2),'rclBounds',[[0,0],[-1,-1]]),
        ('i','iGraphicsMode',const.GM_COMPATIBLE),
        ('f','exScale',1.0),
        ('f','eyScale',1.0),
        ('i','ptlReference_x',1),
        ('i','ptlReference_y',1),
        ('i','nChars',1),
        ('i','offString',0),
        ('i','fOptions',0),
        (Points(num=2),'rcl',[[0,0],[-1,-1]]),
        ('i','offDx',0),
        (List(num='nChars',fmt='i',offset='offDx'),'dx'),
        (EMFString(num='nChars',size=1,offset='offString'),'string'),
        ]
    def __init__(self,x=0,y=0,txt=""):
        EMR_UNKNOWN.__init__(self)
        self.ptlReference_x=x
        self.ptlReference_y=y
        self.string = txt
        self.charsize=1
        self.dx=[]


@register_emr
class EXTTEXTOUTW(EXTTEXTOUTA):
    """UTF-16le-encoded text."""
    emr_id=84
    typedef=[
        (Points(num=2),'rclBounds',[[0,0],[-1,-1]]),
        ('i','iGraphicsMode',const.GM_COMPATIBLE),
        ('f','exScale',1.0),
        ('f','eyScale',1.0),
        ('i','ptlReference_x'),
        ('i','ptlReference_y'),
        ('i','nChars',1),
        ('i','offString',0),
        ('i','fOptions',0),
        (Points(num=2),'rcl',[[0,0],[-1,-1]]),
        ('i','offDx',0),
        (List(num='nChars',fmt='i',offset='offDx'),'dx'),
        (EMFString(num='nChars',size=2,offset='offString'),'string'),
        ]

    def __init__(self,x=0,y=0,txt=''):
        EXTTEXTOUTA.__init__(self,x,y,txt)
        self.charsize=2


def EXTTEXTOUT_auto(x, y, txt):
    """Choose ascii or wide as appropriate."""
    try:
        temp = txt.encode('ascii')
        return EXTTEXTOUTA(x, y, txt)
    except UnicodeEncodeError:
        return EXTTEXTOUTW(x, y, txt)

@register_emr
class POLYBEZIER16(POLYBEZIER):
    emr_id=85
    typedef=[
        (Points(num=2),'rclBounds'),
        ('i','cptl'),
        (Points(num='cptl',fmt='h'),'aptl'),
        ]

@register_emr
class POLYGON16(POLYBEZIER16):
    emr_id=86
    pass

@register_emr
class POLYLINE16(POLYBEZIER16):
    emr_id=87
    pass

@register_emr
class POLYBEZIERTO16(POLYBEZIERTO):
    emr_id=88
    typedef=[
        (Points(num=2),'rclBounds'),
        ('i','cptl'),
        (Points(num='cptl',fmt='h'),'aptl'),
        ]
    pass

@register_emr
class POLYLINETO16(POLYBEZIERTO16):
    emr_id=89
    pass

@register_emr
class POLYPOLYLINE16(POLYPOLYLINE):
    emr_id=90
    typedef=[
        (Points(num=2),'rclBounds'),
        ('i','nPolys'),
        ('i','cptl'),
        (List(num='nPolys',fmt='i'),'aPolyCounts'),
        (Points(num='cptl',fmt='h'),'aptl'),
        ]
    pass

@register_emr
class POLYPOLYGON16(POLYPOLYLINE16):
    emr_id=91
    pass

#define EMR_POLYDRAW16	92

# Stub class for storage of brush with monochrome bitmap or DIB
@register_emr
class CREATEMONOBRUSH(CREATEPALETTE):
    emr_id=93
    pass

# Stub class for device independent bitmap brush
@register_emr
class CREATEDIBPATTERNBRUSHPT(CREATEPALETTE):
    emr_id=94
    pass

# Stub class for extended pen
@register_emr
class EXTCREATEPEN(CREATEPALETTE):
    emr_id=95

    typedef = [
        ('i','handle',0),
        ('i','offBmi',0),
        ('i','cbBmi',0),
        ('i','offBits',0),
        ('i','cbBits',0),
        ('i','style'),
        ('i','penwidth'),
        ('i','brushstyle'),
        ('i','color'),
        ('i','brushhatch',0),
        ('i','numstyleentries')
    ]

    def __init__(self, style=const.PS_SOLID, width=1, color=0,
                 styleentries=[]):
        """Create pen.
        styleentries is a list of dash and space lengths."""

        CREATEPALETTE.__init__(self)

        self.style = style
        self.penwidth = width
        self.color = color
        self.brushstyle = 0x0  # solid

        if style & const.PS_STYLE_MASK != const.PS_USERSTYLE:
            styleentries = []

        self.numstyleentries = len(styleentries)
        if styleentries:
            self.unhandleddata = struct.pack(
                "i"*self.numstyleentries, *styleentries)

    def hasHandle(self):
        return True


#define EMR_POLYTEXTOUTA	96
#define EMR_POLYTEXTOUTW	97


@register_emr
class SETICMMODE(SETMAPMODE):
    """Set or query the current color management mode.

    @gdi: SetICMMode
    """
    emr_id=98
    def __init__(self,mode=const.ICM_OFF):
        SETMAPMODE.__init__(self,mode,first=const.ICM_MIN,last=const.ICM_MAX)


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
