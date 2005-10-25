#!/usr/bin/env python

"""

Pure Python bindings for an
U{ECMA-234<http://www.ecma-international.org/publications/standards/Ecma-234.htm
>} compliant vector graphics library.  ECMA-234 is the published
interface for the Windows GDI used in the Microsoft windows
environment and, more importantly, natively supported by the
U{OpenOffice<http://www.openoffice.org>} suite of tools.


@author: Rob McMullen
@version: 2.0.0b1


"""

import os,sys,re
import struct
from cStringIO import StringIO
import copy


__version__ = "2.0.0b1"
__author__ = "Rob McMullen <robm@users.sourceforge.net>"
__url__ = "http://pyemf.sourceforge.net"

# Reference: libemf.h
# and also wine: http://cvs.winehq.org/cvsweb/wine/include/wingdi.h

emrmap={}

# Brush styles
BS_SOLID	    = 0
BS_NULL		    = 1
BS_HOLLOW	    = 1
BS_HATCHED	    = 2
BS_PATTERN	    = 3
BS_INDEXED	    = 4
BS_DIBPATTERN	    = 5
BS_DIBPATTERNPT	    = 6
BS_PATTERN8X8	    = 7
BS_DIBPATTERN8X8    = 8
BS_MONOPATTERN      = 9

# Hatch styles
HS_HORIZONTAL       = 0
HS_VERTICAL         = 1
HS_FDIAGONAL        = 2
HS_BDIAGONAL        = 3
HS_CROSS            = 4
HS_DIAGCROSS        = 5

# mapping modes
MM_TEXT = 1
MM_LOMETRIC = 2
MM_HIMETRIC = 3
MM_LOENGLISH = 4
MM_HIENGLISH = 5
MM_TWIPS = 6
MM_ISOTROPIC = 7
MM_ANISOTROPIC = 8
MM_MAX = MM_ANISOTROPIC

# background modes
TRANSPARENT = 1
OPAQUE = 2
BKMODE_LAST = 2

# polyfill modes
ALTERNATE = 1
WINDING = 2
POLYFILL_LAST = 2

# line styles and options
PS_SOLID         = 0x00000000
PS_DASH          = 0x00000001
PS_DOT           = 0x00000002
PS_DASHDOT       = 0x00000003
PS_DASHDOTDOT    = 0x00000004
PS_NULL          = 0x00000005
PS_INSIDEFRAME   = 0x00000006
PS_USERSTYLE     = 0x00000007
PS_ALTERNATE     = 0x00000008
PS_STYLE_MASK    = 0x0000000f

PS_ENDCAP_ROUND  = 0x00000000
PS_ENDCAP_SQUARE = 0x00000100
PS_ENDCAP_FLAT   = 0x00000200
PS_ENDCAP_MASK   = 0x00000f00

PS_JOIN_ROUND    = 0x00000000
PS_JOIN_BEVEL    = 0x00001000
PS_JOIN_MITER    = 0x00002000
PS_JOIN_MASK     = 0x0000f000

PS_COSMETIC      = 0x00000000
PS_GEOMETRIC     = 0x00010000
PS_TYPE_MASK     = 0x000f0000
 
# Stock GDI objects for GetStockObject()
WHITE_BRUSH         = 0
LTGRAY_BRUSH        = 1
GRAY_BRUSH          = 2
DKGRAY_BRUSH        = 3
BLACK_BRUSH         = 4
NULL_BRUSH          = 5
HOLLOW_BRUSH        = 5
WHITE_PEN           = 6
BLACK_PEN           = 7
NULL_PEN            = 8
OEM_FIXED_FONT      = 10
ANSI_FIXED_FONT     = 11
ANSI_VAR_FONT       = 12
SYSTEM_FONT         = 13
DEVICE_DEFAULT_FONT = 14
DEFAULT_PALETTE     = 15
SYSTEM_FIXED_FONT   = 16
DEFAULT_GUI_FONT    = 17

STOCK_LAST          = 17

# Text alignment
TA_NOUPDATECP       = 0x00
TA_UPDATECP         = 0x01
TA_LEFT             = 0x00
TA_RIGHT            = 0x02
TA_CENTER           = 0x06
TA_TOP              = 0x00
TA_BOTTOM           = 0x08
TA_BASELINE         = 0x18
TA_RTLREADING       = 0x100
TA_MASK             = TA_BASELINE+TA_CENTER+TA_UPDATECP+TA_RTLREADING

# lfWeight values
FW_DONTCARE         = 0
FW_THIN             = 100
FW_EXTRALIGHT       = 200
FW_ULTRALIGHT       = 200
FW_LIGHT            = 300
FW_NORMAL           = 400
FW_REGULAR          = 400
FW_MEDIUM           = 500
FW_SEMIBOLD         = 600
FW_DEMIBOLD         = 600
FW_BOLD             = 700
FW_EXTRABOLD        = 800
FW_ULTRABOLD        = 800
FW_HEAVY            = 900
FW_BLACK            = 900

# lfCharSet values
ANSI_CHARSET          = 0   # CP1252, ansi-0, iso8859-{1,15}
DEFAULT_CHARSET       = 1
SYMBOL_CHARSET        = 2
SHIFTJIS_CHARSET      = 128 # CP932
HANGEUL_CHARSET       = 129 # CP949, ksc5601.1987-0
HANGUL_CHARSET        = HANGEUL_CHARSET
GB2312_CHARSET        = 134 # CP936, gb2312.1980-0
CHINESEBIG5_CHARSET   = 136 # CP950, big5.et-0
GREEK_CHARSET         = 161 # CP1253
TURKISH_CHARSET       = 162 # CP1254, -iso8859-9
HEBREW_CHARSET        = 177 # CP1255, -iso8859-8
ARABIC_CHARSET        = 178 # CP1256, -iso8859-6
BALTIC_CHARSET        = 186 # CP1257, -iso8859-13
RUSSIAN_CHARSET       = 204 # CP1251, -iso8859-5
EE_CHARSET            = 238 # CP1250, -iso8859-2
EASTEUROPE_CHARSET    = EE_CHARSET
THAI_CHARSET          = 222 # CP874, iso8859-11, tis620
JOHAB_CHARSET         = 130 # korean (johab) CP1361
MAC_CHARSET           = 77
OEM_CHARSET           = 255

VISCII_CHARSET        = 240 # viscii1.1-1
TCVN_CHARSET          = 241 # tcvn-0
KOI8_CHARSET          = 242 # koi8-{r,u,ru}
ISO3_CHARSET          = 243 # iso8859-3
ISO4_CHARSET          = 244 # iso8859-4
ISO10_CHARSET         = 245 # iso8859-10
CELTIC_CHARSET        = 246 # iso8859-14

FS_LATIN1              = 0x00000001L
FS_LATIN2              = 0x00000002L
FS_CYRILLIC            = 0x00000004L
FS_GREEK               = 0x00000008L
FS_TURKISH             = 0x00000010L
FS_HEBREW              = 0x00000020L
FS_ARABIC              = 0x00000040L
FS_BALTIC              = 0x00000080L
FS_VIETNAMESE          = 0x00000100L
FS_THAI                = 0x00010000L
FS_JISJAPAN            = 0x00020000L
FS_CHINESESIMP         = 0x00040000L
FS_WANSUNG             = 0x00080000L
FS_CHINESETRAD         = 0x00100000L
FS_JOHAB               = 0x00200000L
FS_SYMBOL              = 0x80000000L

# lfOutPrecision values
OUT_DEFAULT_PRECIS      = 0
OUT_STRING_PRECIS       = 1
OUT_CHARACTER_PRECIS    = 2
OUT_STROKE_PRECIS       = 3
OUT_TT_PRECIS           = 4
OUT_DEVICE_PRECIS       = 5
OUT_RASTER_PRECIS       = 6
OUT_TT_ONLY_PRECIS      = 7
OUT_OUTLINE_PRECIS      = 8

# lfClipPrecision values
CLIP_DEFAULT_PRECIS     = 0x00
CLIP_CHARACTER_PRECIS   = 0x01
CLIP_STROKE_PRECIS      = 0x02
CLIP_MASK               = 0x0F
CLIP_LH_ANGLES          = 0x10
CLIP_TT_ALWAYS          = 0x20
CLIP_EMBEDDED           = 0x80

# lfQuality values
DEFAULT_QUALITY        = 0
DRAFT_QUALITY          = 1
PROOF_QUALITY          = 2
NONANTIALIASED_QUALITY = 3
ANTIALIASED_QUALITY    = 4

# lfPitchAndFamily pitch values
DEFAULT_PITCH       = 0x00
FIXED_PITCH         = 0x01
VARIABLE_PITCH      = 0x02
MONO_FONT           = 0x08

FF_DONTCARE         = 0x00
FF_ROMAN            = 0x10
FF_SWISS            = 0x20
FF_MODERN           = 0x30
FF_SCRIPT           = 0x40
FF_DECORATIVE       = 0x50

# Graphics Modes
GM_COMPATIBLE     = 1
GM_ADVANCED       = 2
GM_LAST           = 2

# Arc direction modes
AD_COUNTERCLOCKWISE = 1
AD_CLOCKWISE        = 2


def _round4(num):
    """Round to the nearest multiple of 4 greater than or equal to the
    given number.  EMF records are required to be aligned to 4 byte
    boundaries."""
    return ((num+3)/4)*4

def RGB(r,g,b):
    """
Pack integer color values into a 32-bit integer format.

@param r: 0 - 255 or 0.0 - 1.0 specifying red
@param g: 0 - 255 or 0.0 - 1.0 specifying green
@param b: 0 - 255 or 0.0 - 1.0 specifying blue
@return: single integer that should be used when any function needs a color value
@rtype: int
@type r: int or float
@type g: int or float
@type b: int or float

"""
    if isinstance(r,float):
        r=int(255*r)
    if r>255: r=255
    elif r<0: r=0

    if isinstance(g,float):
        g=int(255*g)
    if g>255: g=255
    elif g<0: g=0

    if isinstance(b,float):
        b=int(255*b)
    if b>255: b=255
    elif b<0: b=0

    return ((b<<16)|(g<<8)|r)

def _normalizeColor(c):
    if isinstance(c,int):
        return c
    if isinstance(c,tuple) or isinstance(c,list):
        return RGB(*c)
    raise TypeError("Color must be specified as packed integer or 3-tuple (r,g,b)")



class _DC:
    def __init__(self,width='6.0',height='4.0',density='72',units='in'):
        self.x=0
        self.y=0

        # list of objects that can be referenced by their index
        # number, called "handle"
        self.objects=[]
        self.objects.append(None) # handle 0 is reserved

        # Reference sizes
        self.ref_dev_width=1024
        self.ref_dev_height=768
        self.ref_mm_width=320
        self.ref_mm_height=240

        # physical dimensions are in .01 mm units
        if units=='mm':
            self.width=int(width*100)
            self.height=int(height*100)
        else:
            self.width=int(width*2540)
            self.height=int(height*2540)

        # addressable pixel sizes
        self.devwidth=int(width*density)
        self.devheight=int(height*density)
            
        #self.text_alignment = TA_BASELINE;
        self.text_color = RGB(0,0,0);

        #self.bk_mode = OPAQUE;
        #self.polyfill_mode = ALTERNATE;
        #self.map_mode = MM_TEXT;

    def addObject(self,emr):
        i=len(self.objects)
        self.objects.append(emr)
        return i

    def popObject(self):
        """Remove last object.  Used mainly in case of error."""
        self.objects.pop()



class _EMR_FORMAT:
    def __init__(self,emr_id,typedef):
        self.typedef=typedef
        self.id=emr_id
        self.fmtlist=[] # list of typecodes
        self.defaults=[] # list of default values
        self.fmt="<" # string for pack/unpack.  little endian
        self.structsize=0

        self.names=[]
        self.namepos={}
        
        self.debug=0

        self.setFormat(typedef)

    def setFormat(self,typedef,default=None):
        if self.debug: print "typedef=%s" % str(typedef)
        if isinstance(typedef,list) or isinstance(typedef,tuple):
            for item in typedef:
                if len(item)==3:
                    typecode,name,default=item
                else:
                    typecode,name=item
                self.appendFormat(typecode,name,default)
        elif typedef:
            raise AttributeError("format must be a list")
        self.structsize=struct.calcsize(self.fmt)
        if self.debug: print "current struct=%s size=%d\n  names=%s" % (self.fmt,self.structsize,self.names)

    def appendFormat(self,typecode,name,default):
        self.fmt+=typecode
        self.fmtlist.append(typecode)
        self.defaults.append(default)
        self.namepos[name]=len(self.names)
        self.names.append(name)





class _EMR_UNKNOWN(object): # extend from new-style class, or __getattr__ doesn't work
    """baseclass for EMR objects"""
    emr_id=0
    emr_typedef=()
    format=None

    twobytepadding='\0'*2
    
    def __init__(self):
        self.iType=self.__class__.emr_id
        self.nSize=0
        
        self.datasize=0
        self.data=None
        self.unhandleddata=None

        # number of padding zeros we had to add because the format was
        # expecting more data
        self.zerofill=0

        # if we've never seen this class before, create a new format.
        # Note that subclasses of classes that we have already seen
        # pick up any undefined class attributes from their
        # superclasses, so we have to check if this is a subclass with
        # a different typedef
        if self.__class__.format==None or self.__class__.emr_typedef != self.format.typedef:
            print "creating format for %d" % self.__class__.emr_id
            self.__class__.format=_EMR_FORMAT(self.__class__.emr_id,self.__class__.emr_typedef)

        # list of values parsed from the input stream
        self.values=copy.copy(self.__class__.format.defaults)

        # error code.  Currently just used as a boolean
        self.error=0


    def __getattr__(self,name):
        """Return EMR attribute if the name exists in the typedef list
        of the object.  This is only called when the standard
        attribute lookup fails on this object, so we don't have to
        handle the case where name is an actual attribute of self."""
        f=_EMR_UNKNOWN.__getattribute__(self,'format')
        try:
            if name in f.names:
                v=_EMR_UNKNOWN.__getattribute__(self,'values')
                index=f.namepos[name]
                return v[index]
        except IndexError:
            raise IndexError("name=%s index=%d values=%s" % (name,index,str(v)))
        raise AttributeError("%s not defined in EMR object" % name)

    def __setattr__(self,name,value):
        """Set a value in the object, propagating through to
        self.values[] if the name is in the typedef list."""
        f=_EMR_UNKNOWN.__getattribute__(self,'format')
        try:
            if f and name in f.names:
                v=_EMR_UNKNOWN.__getattribute__(self,'values')
                index=f.namepos[name]
                v[index]=value
            else:
                # it's not an automatically serializable item, so store it.
                self.__dict__[name]=value
        except IndexError:
            raise IndexError("name=%s index=%d values=%s" % (name,index,str(v)))

    def setBounds(self,bounds):
        """Set bounds of object.  Depends on naming convention always
        defining the bounding rectangle as
        rclBounds_[left|top|right|bottom]."""
        self.rclBounds_left=bounds[0]
        self.rclBounds_top=bounds[1]
        self.rclBounds_right=bounds[2]
        self.rclBounds_bottom=bounds[3]

    def unserialize(self,fh,itype=-1,nsize=-1):
        """Read data from the file object and, using the format
        structure defined by the subclass, parse the data and store it
        in self.values[] list."""
        if itype>0:
            self.iType=itype
            self.nSize=nsize
        else:
            (self.iType,self.nSize)=struct.unpack("<ii",8)
        if self.nSize>8:
            self.datasize=self.nSize-8
            self.data=fh.read(self.datasize)
            if self.format.structsize>0:
                if self.format.structsize>len(self.data):
                    # we have a problem.  More stuff to unparse than
                    # we have data.  Hmmm.  Fill with binary zeros
                    # till I think of a better idea.
                    self.zerofill=self.format.structsize-len(self.data)
                    self.data+="\0"*self.zerofill
                self.values=list(struct.unpack(self.format.fmt,self.data[0:self.format.structsize]))
            if self.datasize>self.format.structsize:
                self.unserializeExtra(self.data[self.format.structsize:])

    def unserializeOffset(self,offset):
        """Adjust offset to point to correct location in extra data.
        Offsets in the EMR record are from the start of the record, so
        we must subtract 8 bytes for iType and nSize, and also
        subtract the size of the format structure."""
        return offset-8-self.format.structsize-self.zerofill

    def unserializeExtra(self,data):
        """Hook for subclasses to handle extra data in the record that
        isn't specified by the format statement."""
        self.unhandleddata=data
        pass

    def unserializeList(self,fmt,count,data,start):
        fmt="<%d%s" % (count,fmt)
        size=struct.calcsize(fmt)
        vals=list(struct.unpack(fmt,data[start:start+size]))
        #print "vals fmt=%s size=%d: %s" % (fmt,len(vals),str(vals))
        start+=size
        return (start,vals)

    def unserializePoints(self,fmt,count,data,start):
        fmt="<%d%s" % ((2*count),fmt)
        size=struct.calcsize(fmt)
        vals=struct.unpack(fmt,data[start:start+size])
        pairs=[(vals[i],vals[i+1]) for i in range(0,len(vals),2)]
        #print "points size=%d: %s" % (len(pairs),pairs)
        start+=size
        return (start,pairs)
            
    def serialize(self,fh):
        fh.write(struct.pack("<ii",self.iType,self.nSize))
        try:
            fh.write(struct.pack(self.format.fmt,*self.values))
        except struct.error:
            print "!!!!!Struct error:",
            print self
            raise
        self.serializeExtra(fh)

    def serializeOffset(self):
        """Return the initial offset for any extra data that must be
        written to the record.  See L{unserializeOffset}."""
        return 8+self.format.structsize

    def serializeExtra(self,fh):
        """This is for special cases, like writing text or lists.  If
        this is not overridden by a subclass method, it will write out
        anything in the self.unhandleddata string."""
        if self.unhandleddata:
            fh.write(self.unhandleddata)
            

    def serializeList(self,fh,fmt,vals):
        fmt="<%s" % fmt
        for val in vals:
            fh.write(struct.pack(fmt,val))

    def serializePoints(self,fh,fmt,pairs):
        fmt="<2%s" % fmt
        for pair in pairs:
            fh.write(struct.pack(fmt,pair[0],pair[1]))

    def serializeString(self,fh,txt):
        if isinstance(txt,unicode):
            # convert to unicode and throw away first two byte
            # signature.  FIXME: need to check if we're on a
            # big-endian machine.
            txt=txt.encode('utf-16')[2:]
        fh.write(txt)
        extra=_round4(len(txt))-len(txt)
        if extra>0:
            fh.write('\0'*extra)

    def resize(self):
        before=self.nSize
        self.nSize=8+self.format.structsize+self.sizeExtra()
        if before!=self.nSize:
            print "resize: before=%d after=%d" % (before,self.nSize),
            print self
        if self.nSize%4 != 0:
            print "size error.  Must be divisible by 4"
            print self
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

    def str_extra(self):
        """Hook to print out extra data that isn't in the format"""
        return ""

    def str_color(self,val):
        return "red=0x%02x green=0x%02x blue=0x%02x" % ((val&0xff),((val&0xff00)>>8),((val&0xff0000)>>16))

    def str_decode(self,typecode,name):
        val=_EMR_UNKNOWN.__getattr__(self,name)
        if name.endswith("olor"):
            val=self.str_color(val)
        elif typecode.endswith("s"):
            val=val.decode('utf-16')
        return val
    
    def str_details(self):
        txt=StringIO()

        # _EMR_UNKNOWN objects don't have a typedef, so only process
        # those that do
        if self.format.typedef:
            #print "typedef=%s" % str(self.format.typedef)
            for item in self.format.typedef:
                typecode=item[0]
                name=item[1]
                val=self.str_decode(typecode,name)
                txt.write("\t%-20s: %s\n" % (name,val))
        txt.write(self.str_extra())
        return txt.getvalue()

    def __str__(self):
        ret=""
        details=self.str_details()
        if details:
            ret=os.linesep
        return "**%s: iType=%s nSize=%s  struct='%s' size=%d\n%s%s" % (self.__class__.__name__.lstrip('_'),self.iType,self.nSize,self.format.fmt,self.format.structsize,details,ret)
        return 


# Collection of classes

class _EMR:

    class _HEADER(_EMR_UNKNOWN):
        """Header has different fields depending on the version of
        windows.  Also note that if offDescription==0, there is no
        description string."""

        emr_id=1
        emr_typedef=[('i','rclBounds_left'),
                     ('i','rclBounds_top'),
                     ('i','rclBounds_right'),
                     ('i','rclBounds_bottom'),
                     ('i','rclFrame_left'),
                     ('i','rclFrame_top'),
                     ('i','rclFrame_right'),
                     ('i','rclFrame_bottom'),
                     ('i','dSignature',1179469088),
                     ('i','nVersion',0x10000),
                     ('i','nBytes',0),
                     ('i','nRecords',0),
                     ('h','nHandles',0),
                     ('h','sReserved',0),
                     ('i','nDescription',0),
                     ('i','offDescription',0),
                     ('i','nPalEntries',0),
                     ('i','szlDevice_cx',1024),
                     ('i','szlDevice_cy',768),
                     ('i','szlMillimeters_cx',320),
                     ('i','szlMillimeters_cy',240),
                     ('i','cbPixelFormat',0),
                     ('i','offPixelFormat',0),
                     ('i','bOpenGL',0),
                     ('i','szlMicrometers_cx'),
                     ('i','szlMicrometers_cy')]
        
        def __init__(self,description=''):
            _EMR_UNKNOWN.__init__(self)

            # NOTE: rclBounds and rclFrame will be determined at
            # serialize time

            if isinstance(description,str):
                # turn it into a unicode string
                # print "description=%s" % description
                self.description=description.decode('utf-8')
                # print "self.description=%s" % self.description
                # print isinstance(self.description,unicode)
            if len(description)>0:
                self.description=u'pyemf '+__version__.decode('utf-8')+u'\0'+description+u'\0\0'
            self.nDescription=len(self.description)

        def unserializeExtra(self,data):
            print "found %d extra bytes." % len(data)

            # FIXME: descriptionStart could potentially be negative if
            # we have an old format metafile without stuff after
            # szlMillimeters AND we have a description.
            if self.offDescription>0:
                start=self.unserializeOffset(self.offDescription)
                txt=data[start:start+(2*self.nDescription)]
                self.description=txt.decode('utf-16')
                print "str: %s" % self.description

        def str_extra(self):
            txt=StringIO()
            txt.write("\tunicode string: %s\n" % str(self.description))
            txt.write("%s\n" % (struct.pack('16s',self.description.encode('utf-16'))))
            return txt.getvalue()

        def setBounds(self,dc):
            self.rclBounds_left=0
            self.rclBounds_top=0
            self.rclBounds_right=int(dc.width/100.0*dc.ref_dev_width/dc.ref_mm_width)
            self.rclBounds_bottom=int(dc.height/100.0*dc.ref_dev_height/dc.ref_mm_height)
            self.rclFrame_left=0
            self.rclFrame_top=0
            self.rclFrame_right=dc.width
            self.rclFrame_bottom=dc.height


        def sizeExtra(self):
            self.szlMicrometers_cx=self.szlMillimeters_cx*1000
            self.szlMicrometers_cy=self.szlMillimeters_cy*1000

            self.nDescription=len(self.description)
            if self.nDescription>0:
                self.offDescription=self.serializeOffset()
            else:
                self.offDescription=0
            sizestring=_round4(self.nDescription*2) # always unicode
            
            return sizestring

        def serializeExtra(self,fh):
            self.serializeString(fh,self.description)



    class _POLYBEZIER(_EMR_UNKNOWN):
        emr_id=2
        emr_typedef=[('i','rclBounds_left'),
                     ('i','rclBounds_top'),
                     ('i','rclBounds_right'),
                     ('i','rclBounds_bottom'),
                     ('i','cptl')]
        
        def __init__(self,points=[],bounds=(0,0,0,0)):
            _EMR_UNKNOWN.__init__(self)
            self.setBounds(bounds)
            self.cptl=len(points)
            self.aptl=points

        def unserializeExtra(self,data):
            print "found %d extra bytes." % len(data)

            start=0
            start,self.aptl=self.unserializePoints("i",self.cptl,data,start)
            #print "apts size=%d: %s" % (len(self.apts),self.apts)

        def sizeExtra(self):
            return struct.calcsize("i")*2*self.cptl

        def serializeExtra(self,fh):
            self.serializePoints(fh,"i",self.aptl)

        def str_extra(self):
            txt=StringIO()
            start=0
            txt.write("\tpoints: %s\n" % str(self.aptl))
                    
            return txt.getvalue()

    class _POLYGON(_POLYBEZIER):
        emr_id=3
        pass

    class _POLYLINE(_POLYBEZIER):
        emr_id=4
        pass

    class _POLYBEZIERTO(_POLYBEZIER):
        emr_id=5
        pass

    class _POLYLINETO(_POLYBEZIER):
        emr_id=6
        pass
    


    class _POLYPOLYLINE(_EMR_UNKNOWN):
        emr_id=7
        emr_typedef=[('i','rclBounds_left'),
                     ('i','rclBounds_top'),
                     ('i','rclBounds_right'),
                     ('i','rclBounds_bottom'),
                     ('i','nPolys'),
                     ('i','cptl')]
        
        def __init__(self):
            _EMR_UNKNOWN.__init__(self)

        def unserializeExtra(self,data):
            print "found %d extra bytes." % len(data)

            start=0
            start,self.aPolyCounts=self.unserializeList("i",self.nPolys,data,start)
            #print "aPolyCounts start=%d size=%d: %s" % (start,len(self.aPolyCounts),str(self.aPolyCounts))

            start,self.aptl=self.unserializePoints("i",self.cptl,data,start)
            #print "apts size=%d: %s" % (len(self.apts),self.apts)

        def sizeExtra(self):
            return (struct.calcsize("i")*self.nPolys +
                    struct.calcsize("i")*2*self.cptl)

        def serializeExtra(self,fh):
            self.serializeList(fh,"i",self.aPolyCounts)
            self.serializePoints(fh,"i",self.aptl)

        def str_extra(self):
            txt=StringIO()
            start=0
            for n in range(self.nPolys):
                txt.write("\tPolygon %d: %d points\n" % (n,self.aPolyCounts[n]))
                txt.write("\t\t%s\n" % str(self.aptl[start:start+self.aPolyCounts[n]]))
                start+=self.aPolyCounts[n]
                    
            return txt.getvalue()

    class _POLYPOLYGON(_POLYPOLYLINE):
        emr_id=8
        pass




    class _SETWINDOWEXTEX(_EMR_UNKNOWN):
        emr_id=9
        emr_typedef=[('i','szlExtent_cx'),
                     ('i','szlExtent_cy')]
        
        def __init__(self,cx=0,cy=0):
            _EMR_UNKNOWN.__init__(self)
            self.szlExtent_cx=cx
            self.szlExtent_cy=cy


    class _SETWINDOWORGEX(_EMR_UNKNOWN):
        emr_id=10
        emr_typedef=[('i','ptlOrigin_x'),
                     ('i','ptlOrigin_y')]
        
        def __init__(self):
            _EMR_UNKNOWN.__init__(self)


    class _SETVIEWPORTEXTEX(_SETWINDOWEXTEX):
        emr_id=11
        pass


    class _SETVIEWPORTORGEX(_SETWINDOWORGEX):
        emr_id=12
        pass


    class _SETBRUSHORGEX(_SETWINDOWORGEX):
        emr_id=13
        pass


    class _EOF(_EMR_UNKNOWN):
        emr_id=14
        emr_typedef=[
                ('i','nPalEntries',0),
                ('i','offPalEntries',0),
                ('i','nSizeLast',0)]
        
        def __init__(self):
            _EMR_UNKNOWN.__init__(self)
            # I don't know if I have a broken example or what, but
            # features.emf file only has a 12 byte long EOF record.
            # OpenOffice seems to handle it, though.


    class _SETPIXELV(_EMR_UNKNOWN):
        emr_id=15
        emr_typedef=[
                ('i','ptlPixel_x'),
                ('i','ptlPixel_y'),
                ('i','crColor')]
        
        def __init__(self,x=0,y=0,color=0):
            _EMR_UNKNOWN.__init__(self)
            self.ptlPixel_x=x
            self.ptlPixel_y=y
            self.crColor=color


    class _SETMAPPERFLAGS(_EMR_UNKNOWN):
        emr_id=16
        emr_format=[('i','dwFlags',0)]
        
        def __init__(self):
            _EMR_UNKNOWN.__init__(self)


    class _SETMAPMODE(_EMR_UNKNOWN):
        emr_id=17
        emr_typedef=[('i','iMode',MM_ANISOTROPIC)]
        
        def __init__(self,mode=MM_ANISOTROPIC,last=MM_MAX):
            _EMR_UNKNOWN.__init__(self)
            if mode<0 or mode>last:
                self.error=1
            else:
                self.iMode=mode
            
    class _SETBKMODE(_SETMAPMODE):
        emr_id=18
        def __init__(self,mode=OPAQUE):
            _EMR._SETMAPMODE.__init__(self,mode,last=BKMODE_LAST)


    class _SETPOLYFILLMODE(_SETMAPMODE):
        emr_id=19
        def __init__(self,mode=ALTERNATE):
            _EMR._SETMAPMODE.__init__(self,mode,last=POLYFILL_LAST)

            
    class _SETROP2(_SETMAPMODE):
        emr_id=20
        pass

            
    class _SETSTRETCHBLTMODE(_SETMAPMODE):
        emr_id=21
        pass

            
    class _SETTEXTALIGN(_SETMAPMODE):
        emr_id=22
        def __init__(self,mode=TA_BASELINE):
            _EMR._SETMAPMODE.__init__(self,mode,last=TA_MASK)

            
#define EMR_SETCOLORADJUSTMENT	23

    class _SETTEXTCOLOR(_EMR_UNKNOWN):
        emr_id=24
        emr_typedef=[('i','crColor',0)]
        
        def __init__(self,color=0):
            _EMR_UNKNOWN.__init__(self)
            self.crColor=color


    class _SETBKCOLOR(_SETTEXTCOLOR):
        emr_id=25
        pass


#define EMR_OFFSETCLIPRGN	26


    class _MOVETOEX(_EMR_UNKNOWN):
        emr_id=27
        emr_typedef=[
                ('i','ptl_x'),
                ('i','ptl_y')]
        
        def __init__(self,x=0,y=0):
            _EMR_UNKNOWN.__init__(self)
            self.ptl_x=x
            self.ptl_y=y
            

#define EMR_SETMETARGN	28
#define EMR_EXCLUDECLIPRECT	29
#define EMR_INTERSECTCLIPRECT	30

    class _SCALEVIEWPORTEXTEX(_EMR_UNKNOWN):
        emr_id=31
        emr_typedef=[
                ('i','xNum',1),
                ('i','xDenom',1),
                ('i','yNum',1),
                ('i','yDenom',1)]
        
        def __init__(self):
            _EMR_UNKNOWN.__init__(self)

    class _SCALEWINDOWEXTEX(_SCALEVIEWPORTEXTEX):
        emr_id=32
        pass


    class _SAVEDC(_EMR_UNKNOWN):
        emr_id=33
        pass

    class _RESTOREDC(_EMR_UNKNOWN):
        emr_id=34
        emr_typedef=[('i','iRelative')]
        
        def __init__(self):
            _EMR_UNKNOWN.__init__(self)


    class _SETWORLDTRANSFORM(_EMR_UNKNOWN):
        emr_id=35
        emr_typedef=[
                ('f','eM11'),
                ('f','eM12'),
                ('f','eM21'),
                ('f','eM22'),
                ('f','eDx'),
                ('f','eDy')]
        
        def __init__(self):
            _EMR_UNKNOWN.__init__(self)

    class _MODIFYWORLDTRANSFORM(_EMR_UNKNOWN):
        emr_id=36
        emr_typedef=[
                ('f','eM11'),
                ('f','eM12'),
                ('f','eM21'),
                ('f','eM22'),
                ('f','eDx'),
                ('f','eDy'),
                ('i','iMode')]
        
        def __init__(self):
            _EMR_UNKNOWN.__init__(self)


    class _SELECTOBJECT(_EMR_UNKNOWN):
        emr_id=37

        # handle must be unsigned to handle stock objects, which have
        # their high order bit set.
        emr_typedef=[('I','handle')]
        
        def __init__(self,dc=None,handle=0):
            _EMR_UNKNOWN.__init__(self)
            self.handle=handle


    # Note: a line will still be drawn when the linewidth==0.  To force an
    # invisible line, use style=PS_NULL
    class _CREATEPEN(_EMR_UNKNOWN):
        emr_id=38
        emr_typedef=[
                ('i','handle',0),
                ('i','lopn_style'),
                ('i','lopn_width'),
                ('i','lopn_unused',0),
                ('i','lopn_color')]
        
        def __init__(self,style=PS_SOLID,width=1,color=0):
            _EMR_UNKNOWN.__init__(self)
            self.lopn_style=style
            self.lopn_width=width
            self.lopn_color=color


    class _CREATEBRUSHINDIRECT(_EMR_UNKNOWN):
        emr_id=39
        emr_typedef=[
                ('i','handle',0),
                ('I','lbStyle'),
                ('i','lbColor'),
                ('I','lbHatch')]
        
        def __init__(self,style=BS_SOLID,hatch=HS_HORIZONTAL,color=0):
            _EMR_UNKNOWN.__init__(self)
            self.lbStyle = style
            self.lbColor = color
            self.lbHatch = hatch


    class _DELETEOBJECT(_SELECTOBJECT):
        emr_id=40
        pass


    class _ANGLEARC(_EMR_UNKNOWN):
        emr_id=41
        emr_typedef=[
                ('i','ptlCenter_x'),
                ('i','ptlCenter_y'),
                ('i','nRadius'),
                ('f','eStartAngle'),
                ('f','eSweepAngle')]
        
        def __init__(self):
            _EMR_UNKNOWN.__init__(self)


    class _ELLIPSE(_EMR_UNKNOWN):
        emr_id=42
        emr_typedef=[
                ('i','rclBox_left'),
                ('i','rclBox_top'),
                ('i','rclBox_right'),
                ('i','rclBox_bottom')]
        
        def __init__(self,box=(0,0,0,0)):
            _EMR_UNKNOWN.__init__(self)
            self.rclBox_left=box[0]
            self.rclBox_top=box[1]
            self.rclBox_right=box[2]
            self.rclBox_bottom=box[3]


    class _RECTANGLE(_ELLIPSE):
        emr_id=43
        pass


    class _ROUNDRECT(_EMR_UNKNOWN):
        emr_id=44
        emr_typedef=[
                ('i','rclBox_left'),
                ('i','rclBox_top'),
                ('i','rclBox_right'),
                ('i','rclBox_bottom'),
                ('i','szlCorner_cx'),
                ('i','szlCorner_cy')]
        
        def __init__(self,box=(0,0,0,0),cx=0,cy=0):
            _EMR_UNKNOWN.__init__(self)
            self.rclBox_left=box[0]
            self.rclBox_top=box[1]
            self.rclBox_right=box[2]
            self.rclBox_bottom=box[3]
            self.szlCorner_cx=cx
            self.szlCorner_cy=cy


    class _ARC(_EMR_UNKNOWN):
        emr_id=45
        emr_typedef=[
                ('i','rclBox_left'),
                ('i','rclBox_top'),
                ('i','rclBox_right'),
                ('i','rclBox_bottom'),
                ('i','ptlStart_x'),
                ('i','ptlStart_y'),
                ('i','ptlEnd_x'),
                ('i','ptlEnd_y')]
        
        def __init__(self,left=0,top=0,right=0,bottom=0,
                     xstart=0,ystart=0,xend=0,yend=0):
            _EMR_UNKNOWN.__init__(self)
            self.rclBox_left=left
            self.rclBox_top=top
            self.rclBox_right=right
            self.rclBox_bottom=bottom
            self.ptlStart_x=xstart
            self.ptlStart_y=ystart
            self.ptlEnd_x=xend
            self.ptlEnd_y=yend
            

    class _CHORD(_ARC):
        emr_id=46
        pass


    class _PIE(_ARC):
        emr_id=47
        pass


    class _SELECTPALLETE(_EMR_UNKNOWN):
        emr_id=48
        emr_typedef=[('i','ihPal')]
        
        def __init__(self):
            _EMR_UNKNOWN.__init__(self)
        

#define EMR_CREATEPALETTE	49
#define EMR_SETPALETTEENTRIES	50
#define EMR_RESIZEPALETTE	51
#define EMR_REALIZEPALETTE	52
#define EMR_EXTFLOODFILL	53


    class _LINETO(_MOVETOEX):
        emr_id=54
        pass


    class _ARCTO(_ARC):
        emr_id=55
        pass


#define EMR_POLYDRAW	56


    class _SETARCDIRECTION(_EMR_UNKNOWN):
        emr_id=57
        emr_typedef=[('i','iArcDirection')]
        def __init__(self):
            _EMR_UNKNOWN.__init__(self)
        


#define EMR_SETMITERLIMIT	58


    class _BEGINPATH(_EMR_UNKNOWN):
        emr_id=59
        pass


    class _ENDPATH(_EMR_UNKNOWN):
        emr_id=60
        pass


    class _CLOSEFIGURE(_EMR_UNKNOWN):
        emr_id=61
        pass


    class _FILLPATH(_EMR_UNKNOWN):
        emr_id=62
        emr_typedef=[
                ('i','rclBounds_left'),
                ('i','rclBounds_top'),
                ('i','rclBounds_right'),
                ('i','rclBounds_bottom')]
        def __init__(self,bounds=(0,0,0,0)):
            _EMR_UNKNOWN.__init__(self)
            self.setBounds(bounds)

    class _STROKEANDFILLPATH(_FILLPATH):
        emr_id=63
        pass


    class _STROKEPATH(_FILLPATH):
        emr_id=64
        pass


    class _FLATTENPATH(_EMR_UNKNOWN):
        emr_id=65
        pass


    class _WIDENPATH(_EMR_UNKNOWN):
        emr_id=66
        pass


#define EMR_SELECTCLIPPATH	67


    class _ABORTPATH(_EMR_UNKNOWN):
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
#define EMR_STRETCHDIBITS	81



    class _EXTCREATEFONTINDIRECTW(_EMR_UNKNOWN):
        # Note: all the strings here (font names, etc.) are unicode
        # strings.
        
        emr_id=82
        emr_typedef=[
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
                ('64s','lfFaceName',), # really a 32 char unicode string
                ('128s','elfFullName','\0'*128), # really 64 char unicode str
                ('64s','elfStyle','\0'*64), # really 32 char unicode str
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
            self.lfFaceName=name.decode('utf-8').encode('utf-16')[2:]
            # print "lfFaceName=%s" % self.lfFaceName



    class _EXTTEXTOUTA(_EMR_UNKNOWN):
        emr_id=83
        emr_typedef=[
                ('i','rclBounds_left',0),
                ('i','rclBounds_top',0),
                ('i','rclBounds_right',-1),
                ('i','rclBounds_bottom',-1),
                ('i','iGraphicsMode',GM_COMPATIBLE),
                ('f','exScale',1.0),
                ('f','eyScale',1.0),
                ('i','ptlReference_x'),
                ('i','ptlReference_y'),
                ('i','nChars'),
                ('i','offString'),
                ('i','fOptions',0),
                ('i','rcl_left',0),
                ('i','rcl_top',0),
                ('i','rcl_right',-1),
                ('i','rcl_bottom',-1),
                ('i','offDx',0)]
        def __init__(self,x=0,y=0,txt=""):
            _EMR_UNKNOWN.__init__(self)
            self.ptlReference_x=x
            self.ptlReference_y=y
            if isinstance(txt,unicode):
                self.string=txt.encode('utf-16')[2:]
            else:
                self.string=txt
            self.charsize=1
            self.dx=[]

        def unserializeExtra(self,data):
            print "found %d extra bytes.  nChars=%d" % (len(data),self.nChars)

            start=0
            print "offDx=%d offString=%d" % (self.offDx,self.offString)

            # Note: offsets may appear before OR after string.  Don't
            # assume they will appear first.
            if self.offDx>0:
                start=self.unserializeOffset(self.offDx)
                start,self.dx=self.unserializeList("i",self.nChars,data,start)
            else:
                self.dx=[]
                
            if self.offString>0:
                start=self.unserializeOffset(self.offString)
                self.string=data[start:start+(self.charsize*self.nChars)]
            else:
                self.string=""

        def sizeExtra(self):
            offset=self.serializeOffset()
            sizedx=0
            sizestring=0

            if len(self.dx)>0:
                self.offDx=offset
                sizedx=struct.calcsize("i")*self.nChars
                offset+=sizedx
            if len(self.string)>0:
                self.nChars=len(self.string)/self.charsize
                self.offString=offset
                sizestring=_round4(self.charsize*self.nChars)
                
            return (sizedx+sizestring)

        def serializeExtra(self,fh):
            if self.offDx>0:
                self.serializeList(fh,"i",self.dx)
            if self.offString>0:
                self.serializeString(fh,self.string)

        def str_extra(self):
            txt=StringIO()
            txt.write("\tdx: %s\n" % str(self.dx))
            if self.charsize==2:
                txt.write("\tunicode string: %s\n" % str(self.string.decode('utf-16')))
            else:
                txt.write("\tascii string: %s\n" % str(self.string))
                    
            return txt.getvalue()


    class _EXTTEXTOUTW(_EXTTEXTOUTA):
        emr_id=84

        def __init__(self,x=0,y=0,txt=u''):
            _EMR._EXTTEXTOUTA.__init__(self,x,y,txt)
            self.charsize=2




    class _POLYBEZIER16(_EMR_UNKNOWN):
        # FIXME: subclass from POLYBEZIER
        emr_id=85
        emr_typedef=[
                ('i','rclBounds_left'),
                ('i','rclBounds_top'),
                ('i','rclBounds_right'),
                ('i','rclBounds_bottom'),
                ('i','cpts')]
        def __init__(self,points=[],bounds=(0,0,0,0)):
            _EMR_UNKNOWN.__init__(self)
            self.setBounds(bounds)
            self.cpts=len(points)
            self.apts=points

        def unserializeExtra(self,data):
            print "found %d extra bytes." % len(data)

            start=0
            start,self.apts=self.unserializePoints("h",self.cpts,data,start)
            #print "apts size=%d: %s" % (len(self.apts),self.apts)

        def sizeExtra(self):
            return (struct.calcsize("h")*2*self.cpts)

        def serializeExtra(self,fh):
            self.serializePoints(fh,"h",self.apts)

        def str_extra(self):
            txt=StringIO()
            start=0
            txt.write("\tpoints: %s\n" % str(self.apts))
                    
            return txt.getvalue()

    class _POLYGON16(_POLYBEZIER16):
        emr_id=86
        pass

    class _POLYLINE16(_POLYBEZIER16):
        emr_id=87
        pass

    class _POLYBEZIERTO16(_POLYBEZIER16):
        emr_id=88
        pass

    class _POLYLINETO16(_POLYBEZIER16):
        emr_id=89
        pass
    


    class _POLYPOLYLINE16(_EMR_UNKNOWN):
        emr_id=90
        emr_typedef=[
                ('i','rclBounds_left'),
                ('i','rclBounds_top'),
                ('i','rclBounds_right'),
                ('i','rclBounds_bottom'),
                ('i','nPolys'),
                ('i','cpts')]
        def __init__(self):
            _EMR_UNKNOWN.__init__(self)

        def unserializeExtra(self,data):
            print "found %d extra bytes." % len(data)

            start=0
            start,self.aPolyCounts=self.unserializeList("i",self.nPolys,data,start)
            #print "aPolyCounts start=%d size=%d: %s" % (start,len(self.aPolyCounts),str(self.aPolyCounts))

            start,self.apts=self.unserializePoints("h",self.cpts,data,start)
            #print "apts size=%d: %s" % (len(self.apts),self.apts)

        def sizeExtra(self):
            return (struct.calcsize("i")*self.nPolys +
                    struct.calcsize("h")*2*self.cpts)

        def serializeExtra(self,fh):
            self.serializeList(fh,"i",self.aPolyCounts)
            self.serializePoints(fh,"h",self.apts)

        def str_extra(self):
            txt=StringIO()
            start=0
            for n in range(self.nPolys):
                txt.write("\tPolygon %d: %d points\n" % (n,self.aPolyCounts[n]))
                txt.write("\t\t%s\n" % str(self.apts[start:start+self.aPolyCounts[n]]))
                start+=self.aPolyCounts[n]
                    
            return txt.getvalue()

    class _POLYPOLYGON16(_POLYPOLYLINE16):
        emr_id=91
        pass

#define EMR_POLYDRAW16	92
#define EMR_CREATEMONOBRUSH	93
#define EMR_CREATEDIBPATTERNBRUSHPT	94
#define EMR_EXTCREATEPEN	95
#define EMR_POLYTEXTOUTA	96
#define EMR_POLYTEXTOUTW	97
#define EMR_SETICMMODE	98
#define EMR_CREATECOLORSPACE	99
#define EMR_SETCOLORSPACE	100
#define EMR_DELETECOLORSPACE	101
#define EMR_GLSRECORD	102
#define EMR_GLSBOUNDEDRECORD	103
#define EMR_PIXELFORMAT 104


# Set up the mapping of ids to classes for all of the record types in
# the EMR class.
for name in dir(_EMR):
    #print name
    cls=getattr(_EMR,name,None)
    if cls and callable(cls) and issubclass(cls,_EMR_UNKNOWN):
        #print "subclass! id=%d %s" % (cls.emr_id,str(cls))
        emrmap[cls.emr_id]=cls



class EMF:
    """

User interface to EMF creation.

@group Creating Metafiles: __init__, load, save
@group Drawing Parameters: GetStockObject, SelectObject, DeleteObject, CreatePen, CreateSolidBrush, CreateHatchBrush, SetBkColor, SetBkMode, SetPolyFillMode
@group Drawing Primitives: SetPixel, Polyline, Polygon, Rectangle, RoundRect, Ellipse, Arc, Chord, Pie, PolyBezier
@group Path Primatives: BeginPath, EndPath, MoveTo, LineTo, PolylineTo, ArcTo,
 PolyBezierTo, CloseFigure, FillPath, StrokePath, StrokeAndFillPath
@group Text: CreateFont, SetTextAlign, SetTextColor, TextOut
@group Viewport Manipulation: SetViewportOrgEx, GetViewportOrgEx, SetWindowOrgEx, GetWindowOrgEx, SetViewportExtEx, ScaleViewportExtEx, GetViewportExtEx, SetWindowExtEx, ScaleWindowExtEx, GetWindowExtEx 
@group Misc: GetLastError, GetDeviceCaps, SetMapMode

"""

    def __init__(self,width=6.0,height=4.0,density=300,units="in",
                 description="pyemf.sf.net",verbose=False):
        """
Create an EMF structure in memory.  The size of the resulting image is
specified in either inches or millimeters depending on the value of
L{units}.  Width and height are floating point values, but density
must be an integer because this becomes the basis for the coordinate
system in the image.  Density is the number of individually
addressible pixels per unit measurement (dots per inch or dots per
millimeter, depending on the units system) in the image.  A
consequence of this is that each pixel is specified by a pair of
integer coordinates.

@param width: width of EMF image in inches or millimeters
@param height: height of EMF image in inches or millimeters
@param density: dots (pixels) per unit measurement
@param units: string indicating the unit measurement, one of:
 - 'in'
 - 'mm'
@type width: float
@type height: float
@type density: int
@type units: string
@param description: optional string to specify a description of the image
@type description: string

"""
        self.filename=None
        self.dc=_DC(width,height,density,units)
        self.records=[]

        # path recordkeeping
        self.pathstart=0

        self.verbose=verbose

        emr=_EMR._HEADER(description)
        self._append(emr)
        self.SetMapMode(MM_ANISOTROPIC)
        self.SetWindowExtEx(self.dc.devwidth,self.dc.devheight)
        self.SetViewportExtEx(
            int(self.dc.width/100.0*self.dc.ref_dev_width/self.dc.ref_mm_width),
            int(self.dc.height/100.0*self.dc.ref_dev_height/self.dc.ref_mm_height))


    def load(self,filename=None):
        """
Read an existing EMF file.  If any records exist in the current
object, they will be overwritten by the records from this file.

@param filename: filename to load
@type filename: string
@returns: True for success, False for failure.
@rtype: Boolean
        """
        if filename:
            self.filename=filename

        if self.filename:
            fh=open(self.filename)
            self.records=[]
            self._unserialize(fh)


    def _unserialize(self,fh):
        try:
            count=1
            while count>0:
                data=fh.read(8)
                count=len(data)
                if count>0:
                    (iType,nSize)=struct.unpack("<ii",data)
                    if self.verbose: print "EMF:  iType=%d nSize=%d" % (iType,nSize)

                    if iType in emrmap:
                        e=emrmap[iType]()
                    else:
                        e=_EMR_UNKNOWN()

                    e.unserialize(fh,iType,nSize)
                    self.records.append(e)
                    if self.verbose:
                        print "Unserializing: ",
                        print e
                
        except EOFError:
            pass

    def _append(self,e):
        """Append an EMR to the record list, unless the record has
        been flagged as having an error."""
        if not e.error:
            if self.verbose:
                print "Appending: ",
                print e
            self.records.append(e)
            return 1
        return 0

    def _end(self):
        """
Append an EOF record and compute header information.  The header needs
to know the number of records, number of handles, bounds, and size of
the entire metafile before it can be written out, so we have to march
through all the records and gather info.
        """
        
        end=self.records[-1]
        if not isinstance(end,_EMR._EOF):
            if self.verbose: print "adding EOF record"
            e=_EMR._EOF()
            self._append(e)
        header=self.records[0]
        header.setBounds(self.dc)
        header.nRecords=len(self.records)
        header.nHandles=len(self.dc.objects)
        size=0
        for e in self.records:
            e.resize()
            size+=e.nSize
        header.nBytes=size
        
    def save(self,filename=None):
        """
Write the EMF to disk.

@param filename: filename to write
@type filename: string
@returns: True for success, False for failure.
@rtype: Boolean
        """

        self._end()
    
        if filename:
            self.filename=filename
            
        if self.filename:
            try:
                fh=open(self.filename,"wb")
                self._serialize(fh)
                fh.close()
                return True
            except:
                raise
                return False
        return False
        
    def _serialize(self,fh):
        for e in self.records:
            if self.verbose: print e
            e.serialize(fh)

    def _create(self,width,height,dots_per_unit,units):
        pass

    def _getBounds(self,points):
        """Get the bounding rectangle for this list of 2-tuples."""
        left=points[0][0]
        right=left
        top=points[0][1]
        bottom=top
        for x,y in points[1:]:
            if x<left:
                left=x
            elif x>right:
                right=x
            if y<top:
                top=y
            elif y>bottom:
                bottom=y
        return (left,top,right,bottom)

    def _getPathBounds(self):
        """Get the bounding rectangle for the list of EMR records
        starting from the last saved path start to the current record."""
        for i in range(self.pathstart,len(self.records)):
            print "checking record %d" % i
        return (0,0,-1,-1)

    def _useShort(self,bounds):
        """Determine if we can use the shorter 16-bit EMR structures.
        If all the numbers can fit within 16 bit integers, return
        true.  The bounds 4-tuple is (left,top,right,bottom)."""

        SHRT_MIN=-32768
        SHRT_MAX=32767
        if bounds[0]>=SHRT_MIN and bounds[1]>=SHRT_MIN and bounds[2]<=SHRT_MAX and bounds[3]<=SHRT_MAX:
            return True
        return False

    def _appendOptimize16(self,points,cls16,cls):
        bounds=self._getBounds(points)
        if self._useShort(bounds):
            e=cls16(points,bounds)
        else:
            e=cls(points,bounds)
        if not self._append(e):
            return 0
        return 1

    def _appendHandle(self,e):
        handle=self.dc.addObject(e)
        if not self._append(e):
            self.dc.popObject()
            return 0
        e.handle=handle
        return handle

    def GetStockObject(self,obj):
        """

Retrieve the handle for a predefined graphics object. Stock objects
include (at least) the following:

 - WHITE_BRUSH
 - LTGRAY_BRUSH
 - GRAY_BRUSH
 - DKGRAY_BRUSH
 - BLACK_BRUSH
 - NULL_BRUSH
 - HOLLOW_BRUSH
 - WHITE_PEN
 - BLACK_PEN
 - NULL_PEN
 - OEM_FIXED_FONT
 - ANSI_FIXED_FONT
 - ANSI_VAR_FONT
 - SYSTEM_FONT
 - DEVICE_DEFAULT_FONT
 - DEFAULT_PALETTE
 - SYSTEM_FIXED_FONT
 - DEFAULT_GUI_FONT

@param    obj:  	number of stock object.

@return:    handle of stock graphics object.
@rtype: int
@type obj: int

        """
        if obj>=0 and obj<=STOCK_LAST:
            return obj|0x80000000
        raise IndexError("Undefined stock object.")

    def SelectObject(self,handle):
        """

Make the given graphics object current.

@param handle: handle of graphics object to make current.

@return:
    the handle of the current graphics object which obj replaces.

@rtype: int
@type handle: int

        """
        return self._append(_EMR._SELECTOBJECT(self.dc,handle))

    def DeleteObject(self,obj):
        """

Delete the given graphics object. Note that, now, only those contexts
into which the object has been selected get a delete object
records.

@param    obj:  	handle of graphics object to delete.

@return:    true if the object was successfully deleted.
@rtype: int
@type obj: int

        """
        pass
    def CreatePen(self,style,width,color):
        """

Create a pen, used to draw lines and path outlines.


@param    style:  	the style of the new pen, one of:
 - PS_SOLID
 - PS_DASH
 - PS_DOT
 - PS_DASHDOT
 - PS_DASHDOTDOT
 - PS_NULL
 - PS_INSIDEFRAME
 - PS_USERSTYLE
 - PS_ALTERNATE
@param    width:  	the width of the new pen.
@param    color:  	(r,g,b) tuple or the packed integer L{color<RGB>} of the new pen.

@return:    handle to the new pen graphics object.
@rtype: int
@type style: int
@type width: int
@type color: int

        """
        return self._appendHandle(_EMR._CREATEPEN(style,width,_normalizeColor(color)))
        
    def CreateSolidBrush(self,color):
        """

Create a solid brush used to fill polygons.
@param color: the L{color<RGB>} of the solid brush.
@return: handle to brush graphics object.

@rtype: int
@type color: int

        """
        return self._appendHandle(_EMR._CREATEBRUSHINDIRECT(color=_normalizeColor(color)))

    def CreateHatchBrush(self,hatch,color):
        """

Create a hatched brush used to fill polygons.

B{Note:} Currently appears unsupported in OpenOffice.

@param hatch: integer representing type of fill:
 - HS_HORIZONTAL
 - HS_VERTICAL  
 - HS_FDIAGONAL 
 - HS_BDIAGONAL 
 - HS_CROSS     
 - HS_DIAGCROSS 
@type hatch: int
@param color: the L{color<RGB>} of the 'on' pixels of the brush.
@return: handle to brush graphics object.

@rtype: int
@type color: int

        """
        return self._appendHandle(_EMR._CREATEBRUSHINDIRECT(hatch=hatch,color=_normalizeColor(color)))

    def SetBkColor(self,color):
        """

Set the background color. (self,As near as I can tell, StarOffice only uses
this for text background.)
@param color: background L{color<RGB>}.
@return: previous background L{color<RGB>}.
@rtype: int
@type color: int

        """
        e=_EMR._SETBKCOLOR(_normalizeColor(color))
        if not self._append(e):
            return 0
        return 1

    def SetBkMode(self,mode):
        """

Set the background mode. (StarOffice 1.1 seems to ignore this value, but Windows uses it.)
The choices for mode are:
 - TRANSPARENT
 - OPAQUE
@param mode: background mode.
@return: previous background mode.
@rtype: int
@type mode: int

        """
        e=_EMR._SETBKMODE(mode)
        if not self._append(e):
            return 0
        return 1

    def SetPolyFillMode(self,mode):
        """

Set the polygon fill mode.  Generally these modes produce
different results only when the edges of the polygons overlap
other edges.

@param mode: fill mode with the following options:
 - ALTERNATE - fills area between odd and even numbered sides
 - WINDING - fills all area as long as a point is between any two sides
@return: previous fill mode.
@rtype: int
@type mode: int

        """
        e=_EMR._SETPOLYFILLMODE(mode)
        if not self._append(e):
            return 0
        return 1

    def GetDeviceCaps(self):
        """

Return various information about the "capabilities" of the device
context. This is wholly fabricated for the metafile (i.e., there is
no real device to which these attributes relate).

@return: Capability dictionary; note that to conform with ECMA documentation, the key names are in upper case:
 - B{DRIVERVERSION} - Device driver version number.  Value is always 1.
 - B{TECHNOLOGY} - Device technology available.  Always returns DT_METAFILE
 - B{HORZSIZE} - Horizontal size of reference device in millimeters.
 - B{VERTSIZE} - Vertical size in millimeters.
 - B{HORZRES} - Horizontal size in device units (pixels).
 - B{VERTRES} - Vertical size in device units (pixels).
 - B{LOGPIXELSX} - Number of horizontal pixels per inch.
 - B{LOGPIXELSY} - Number of vertical pixels per inch.
 
@rtype: C{dict}

        """
        pass
    def SetMapMode(self,mode):
        """

Set the window mapping mode. (OpenOffice supports at least MM_ANISOTROPIC.)
 - MM_TEXT
 - MM_LOMETRIC
 - MM_HIMETRIC
 - MM_LOENGLISH
 - MM_HIENGLISH
 - MM_TWIPS
 - MM_ISOTROPIC
 - MM_ANISOTROPIC
@param mode: window mapping mode.
@return: previous window mapping mode, or zero if error.
@rtype: int
@type mode: int
        """
        e=_EMR._SETMAPMODE(mode)
        if not self._append(e):
            return 0
        return 1
        
    def SetViewportOrgEx(self,x,y):
        """

Set the origin of the viewport. (Not entirely sure if this is honored
by StarOffice.)
@param x: new x position of the viewport origin.
@param y: new y position of the viewport origin.
@return: previous viewport origin
@rtype: 2-tuple (x,y) if successful, or None if unsuccessful
@type x: int
@type y: int
        """
        e=_EMR._SETVIEWPORTORGEX(cx,cy)
        if not self._append(e):
            return 0
        return 1

    def GetViewportOrgEx(self):
        """

Get the origin of the viewport.
@return: returns the current viewport origin.
@rtype: 2-tuple (x,y)
        """
        pass
    def SetWindowOrgEx(self,x,y):
        """

Set the origin of the window. Evidently, this means that a point drawn
at the given coordinates will appear at the Viewport origin.
@param x: new x position of the window origin.
@param y: new y position of the window origin.
@return: previous window origin
@rtype: 2-tuple (x,y) if successful, or None if unsuccessful
@type x: int
@type y: int
        """
        pass
    def GetWindowOrgEx(self):
        """

Get the origin of the window.
@return: returns the current window  origin.
@rtype: 2-tuple (x,y)

        """
        pass
    def SetViewportExtEx(self,cx,cy):
        """
Set the dimensions of the viewport in device units.  Device units are
based on the dimensions returned by the GetDeviceCaps calls.  So, each
pixel of a device unit is sized xmm/xpixels by ymm/ypixels in
millimeters.

@param cx: new width of the viewport.
@param cy: new height of the viewport.
@return: returns the previous size of the viewport.
@rtype: 2-tuple (width,height) if successful, or None if unsuccessful
@type cx: int
@type cy: int
        """
        e=_EMR._SETVIEWPORTEXTEX(cx,cy)
        if not self._append(e):
            return 0
        return 1

    def ScaleViewportExtEx(self,x_num,x_den,y_num,y_den):
        """

Scale the dimensions of the viewport.
@param x_num: numerator of x scale
@param x_den: denominator of x scale
@param y_num: numerator of y scale
@param y_den: denominator of y scale
@return: returns the previous size of the viewport.
@rtype: 2-tuple (width,height) if successful, or None if unsuccessful
@type x_num: int
@type x_den: int
@type y_num: int
@type y_den: int
        """
        pass
    def GetViewportExtEx(self):
        """

Get the dimensions of the viewport.
@return: returns the size of the viewport.
@rtype: 2-tuple (width,height)

        """
        pass
    def SetWindowExtEx(self,cx,cy):
        """

Set the dimensions of the window. (OpenOffice honors this at least when map mode is MM_ANISOTROPIC.)
@param cx: new width of the window.
@param cy: new height of the window.
@return: returns the previous size of the window.
@rtype: 2-tuple (width,height) if successful, or None if unsuccessful
@type cx: int
@type cy: int
        """
        e=_EMR._SETWINDOWEXTEX(cx,cy)
        if not self._append(e):
            return 0
        return 1

    def ScaleWindowExtEx(self,x_num,x_den,y_num,y_den):
        """

Scale the dimensions of the window.
@param x_num: numerator of x scale
@param x_den: denominator of x scale
@param y_num: numerator of y scale
@param y_den: denominator of y scale
@return: returns the previous size of the window.
@rtype: 2-tuple (width,height) if successful, or None if unsuccessful
@type x_num: int
@type x_den: int
@type y_num: int
@type y_den: int
        """
        pass
    def GetWindowExtEx(self):
        """

Get the dimensions of the window.
@return: returns the size of the window.
@rtype: 2-tuple (width,height)
        """
        pass
    def SetPixel(self,x,y,color):
        """

Set the pixel to the given color.
@param x: the horizontal position.
@param y: the vertical position.
@param color: the L{color<RGB>} to set the pixel.
@type x: int
@type y: int
@type color: int

        """
        return self._append(_EMR._SETPIXELV(x,y,_normalizeColor(color)))

    def Polyline(self,points):
        """

Draw a sequence of connected lines.
@param points: list of x,y tuples
@return: true if polyline is successfully rendered.
@rtype: int
@type points: tuple

        """
        return self._appendOptimize16(points,_EMR._POLYLINE16,_EMR._POLYLINE)
    

    def Polygon(self,points):
        """

Draw a sequence of connected straight line segments where the end
of the last line segment is connected to the beginning of the first
line segment.
@param points: list of x,y tuples
@return: true if polygon is successfully rendered.
@rtype: int
@type points: tuple

        """
        if len(points)==4:
            if points[0][0]==points[1][0] and points[2][0]==points[3][0] and points[0][1]==points[3][1] and points[1][1]==points[2][1]:
                if self.verbose: print "converting to rectangle, option 1:"
                return self.Rectangle(points[0][0],points[0][1],points[2][0],points[2][1])
            elif points[0][1]==points[1][1] and points[2][1]==points[3][1] and points[0][0]==points[3][0] and points[1][0]==points[2][0]:
                if self.verbose: print "converting to rectangle, option 2:"
                return self.Rectangle(points[0][0],points[0][1],points[2][0],points[2][1])
        return self._appendOptimize16(points,_EMR._POLYGON16,_EMR._POLYGON)

    def Ellipse(self,left,top,right,bottom):
        """

Draw an ellipse using the current pen.
@param left: x position of left side of ellipse bounding box.
@param top: y position of top side of ellipse bounding box.
@param right: x position of right edge of ellipse bounding box.
@param bottom: y position of bottom edge of ellipse bounding box.
@return: true if rectangle was successfully rendered.
@rtype: int
@type left: int
@type top: int
@type right: int
@type bottom: int

        """
        return self._append(_EMR._ELLIPSE((left,top,right,bottom)))
        
    def Rectangle(self,left,top,right,bottom):
        """

Draw a rectangle using the current pen.
@param left: x position of left side of ellipse bounding box.
@param top: y position of top side of ellipse bounding box.
@param right: x position of right edge of ellipse bounding box.
@param bottom: y position of bottom edge of ellipse bounding box.
@return: true if rectangle was successfully rendered.
@rtype: int
@type left: int
@type top: int
@type right: int
@type bottom: int

        """
        return self._append(_EMR._RECTANGLE((left,top,right,bottom)))

    def RoundRect(self,left,top,right,bottom,cornerwidth,cornerheight):
        """

Draw a rectangle with rounded corners using the current pen.
@param left: x position of left side of ellipse bounding box.
@param top: y position of top side of ellipse bounding box.
@param right: x position of right edge of ellipse bounding box.
@param bottom: y position of bottom edge of ellipse bounding box.
@param cornerwidth: width of the ellipse that defines the roundness of the corner.
@param cornerheight: height of ellipse
@return: true if rectangle was successfully rendered.
@rtype: int
@type left: int
@type top: int
@type right: int
@type bottom: int
@type cornerwidth: int
@type cornerheight: int

        """
        return self._append(_EMR._ROUNDRECT((left,top,right,bottom,
                                           cornerwidth,cornerheight)))

    def Arc(self,left,top,right,bottom,xstart,ystart,xend,yend):
        """

Draw an arc of an ellipse.  The ellipse is specified by its bounding
rectange and two lines from its center to indicate the start and end
angles.  left, top, right, bottom describe the bounding rectangle of
the ellipse.  The start point given by xstart,ystert defines a ray
from the center of the ellipse through the point and out to infinity.
The point at which this ray intersects the ellipse is the starting
point of the arc.  Similarly, the infinite radial ray from the center
through the end point defines the end point of the ellipse.  The arc
is drawn in a counterclockwise direction, and if the start and end
rays are coincident, a complete ellipse is drawn.

@param left: x position of left edge of arc box.
@param top: y position of top edge of arc box.
@param right: x position of right edge of arc box.
@param bottom: y position bottom edge of arc box.
@param xstart: x position of arc start.
@param ystart: y position of arc start.
@param xend: x position of arc end.
@param yend: y position of arc end.
@return: true if arc was successfully rendered.
@rtype: int
@type left: int
@type top: int
@type right: int
@type bottom: int
@type xstart: int
@type ystart: int
@type xend: int
@type yend: int

        """
        return self._append(_EMR._ARC(left,top,right,bottom,
                                    xstart,ystart,xend,yend))

    def Chord(self,left,top,right,bottom,xstart,ystart,xend,yend):
        """

Draw a chord of an ellipse.  A chord is a closed region bounded by an
arc and the [straight] line between the two points that define the arc
start and end.  The arc start and end points are defined as in L{Arc}.

@param left: x position of left edge of arc box.
@param top: y position of top edge of arc box.
@param right: x position of right edge of arc box.
@param bottom: y position bottom edge of arc box.
@param xstart: x position of arc start.
@param ystart: y position of arc start.
@param xend: x position of arc end.
@param yend: y position of arc end.
@return: true if arc was successfully rendered.
@rtype: int
@type left: int
@type top: int
@type right: int
@type bottom: int
@type xstart: int
@type ystart: int
@type xend: int
@type yend: int

        """
        return self._append(_EMR._CHORD(left,top,right,bottom,
                                    xstart,ystart,xend,yend))

    def Pie(self,left,top,right,bottom,xstart,ystart,xend,yend):
        """

Draw a pie slice of an ellipse.  The ellipse is specified as in
L{Arc}, and it is filled with the current brush.

@param left: x position of left edge of arc box.
@param top: y position of top edge of arc box.
@param right: x position of right edge of arc box.
@param bottom: y position bottom edge of arc box.
@param xstart: x position of arc start.
@param ystart: y position of arc start.
@param xend: x position of arc end.
@param yend: y position of arc end.
@return: true if arc was successfully rendered.
@rtype: int
@type left: int
@type top: int
@type right: int
@type bottom: int
@type xstart: int
@type ystart: int
@type xend: int
@type yend: int

        """
        return self._append(_EMR._PIE(left,top,right,bottom,
                                    xstart,ystart,xend,yend))

    def PolyBezier(self,points):
        """

Draw cubic Bezier curves using the list of points as both endpoints
and control points.  The first point is used as the starting point,
the second and thrird points are control points, and the fourth point
is the end point of the first curve.  Subsequent curves need three
points each: two control points and an end point, as the ending point
of the previous curve is used as the starting point for the next
curve.

@param points: list of x,y tuples that are either end points or control points
@return: true if bezier curve was successfully rendered.
@rtype: int
@type points: tuple

        """
        return self._appendOptimize16(points,_EMR._POLYBEZIER16,_EMR._POLYBEZIER)

    def BeginPath(self):
        """

Begin defining a path.  Any previous unclosed paths are discarded.
@return: true if successful.
@rtype: int

        """
        # record next record number as first item in path
        self.pathstart=len(self.records)
        return self._append(_EMR._BEGINPATH())

    def EndPath(self):
        """

End the path definition.
@return: true if successful.
@rtype: int

        """
        return self._append(_EMR._ENDPATH())

    def MoveTo(self,x,y):
        """

Move the current point to the given position and implicitly begin a
new figure or path.

@param x: new x position.
@param y: new y position.
@return: true if position successfully changed (can this fail?)
@rtype: int
@type x: int
@type y: int
        """
        return self._append(_EMR._MOVETOEX(x,y))

    def LineTo(self,x,y):
        """

Draw a straight line using the current pen from the current point to
the given position.

@param x: x position of line end.
@param y: y position of line end.
@return: true if line is drawn (can this fail?)
@rtype: int
@type x: int
@type y: int

        """
        return self._append(_EMR._LINETO(x,y))

    def PolylineTo(self,points):
        """

Draw a sequence of connected lines starting from the current
position and update the position to the final point in the list.

@param points: list of x,y tuples
@return: true if polyline is successfully rendered.
@rtype: int
@type points: tuple

        """
        return self._appendOptimize16(points,_EMR._POLYLINETO16,_EMR._POLYLINETO)

    def ArcTo(self,left,top,right,bottom,xstart,ystart,xend,yend):
        """

Draw an arc and update the current position.  The arc is drawn as
described in L{Arc}, but in addition the start of the arc will be
connected to the previous position and the current position is updated
to the end of the arc so subsequent path operations such as L{LineTo},
L{PolylineTo}, etc. will connect to the end.

B{Note:} Currently appears unsupported in OpenOffice.

@param left: x position of left edge of arc box.
@param top: y position of top edge of arc box.
@param right: x position of right edge of arc box.
@param bottom: y position bottom edge of arc box.
@param xstart: x position of arc start.
@param ystart: y position of arc start.
@param xend: x position of arc end.
@param yend: y position of arc end.
@return: true if arc was successfully rendered.
@rtype: int
@type left: int
@type top: int
@type right: int
@type bottom: int
@type xstart: int
@type ystart: int
@type xend: int
@type yend: int

        """
        return self._append(_EMR._ARCTO(left,top,right,bottom,
                                    xstart,ystart,xend,yend))

    def PolyBezierTo(self,points):
        """

Draw cubic Bezier curves, as described in L{PolyBezier}, but in
addition draw a line from the previous position to the start of the
curve.  If the arc is successfully rendered, the current position is
updated so that subsequent path operations such as L{LineTo},
L{PolylineTo}, etc. will follow from the end of the curve.

@param points: list of x,y tuples that are either end points or control points
@return: true if bezier curve was successfully rendered.
@rtype: int
@type points: tuple

        """
        return self._appendOptimize16(points,_EMR._POLYBEZIERTO16,_EMR._POLYBEZIERTO)

    def CloseFigure(self):
        """

Close a currently open path, which connects the current position to the starting position of a figure.  Usually the starting position is the most recent call to L{MoveTo} after L{BeginPath}.

@return: true if successful

@rtype: int

        """
        return self._append(_EMR._CLOSEFIGURE())

    def FillPath(self):
        """

Close any currently open path and fills it using the currently
selected brush and polygon fill mode.

@return: true if successful.
@rtype: int

        """
        return self._append(_EMR._FILLPATH())

    def StrokePath(self):
        """

Close any currently open path and outlines it using the currently
selected pen.

@return: true if successful.
@rtype: int

        """
        bounds=self._getPathBounds()
        return self._append(_EMR._STROKEPATH(bounds))

    def StrokeAndFillPath(self):
        """

Close any currently open path, outlines it using the currently
selected pen, and fills it using the current brush.  Same as stroking
and filling using both the L{FillPath} and L{StrokePath} options,
except that the pixels that would be in the overlap region to be both
stroked and filled are optimized to be only stroked.

B{Note:} Supported in OpenOffice 2.*, unsupported in OpenOffice 1.*.

@return: true if successful.
@rtype: int

        """
        bounds=self._getPathBounds()
        return self._append(_EMR._STROKEANDFILLPATH(bounds))

    def SetTextAlign(self,alignment):
        """

Set the subsequent alignment of drawn text. You can also pass a flag
indicating whether or not to update the current point to the end of the
text. Alignment may have the (sum of) values:
 - TA_NOUPDATECP
 - TA_UPDATECP
 - TA_LEFT
 - TA_RIGHT
 - TA_CENTER
 - TA_TOP
 - TA_BOTTOM
 - TA_BASELINE
 - TA_RTLREADING
@param alignment: new text alignment.
@return: previous text alignment value.
@rtype: int
@type alignment: int

        """
        return self._append(_EMR._SETTEXTALIGN(alignment))

    def SetTextColor(self,color):
        """

Set the text foreground color.
@param color: text foreground L{color<RGB>}.
@return: previous text foreground L{color<RGB>}.
@rtype: int
@type color: int

        """
        e=_EMR._SETTEXTCOLOR(_normalizeColor(color))
        if not self._append(e):
            return 0
        return 1

    def CreateFont(self,height,width=0,escapement=0,orientation=0,weight=FW_NORMAL,italic=0,underline=0,strike_out=0,charset=ANSI_CHARSET,out_precision=OUT_DEFAULT_PRECIS,clip_precision=CLIP_DEFAULT_PRECIS,quality=DEFAULT_QUALITY,pitch_family='DEFAULT_PITCH|FF_DONTCARE',name='Times New Roman'):
        """

Create a new font object. Presumably, when rendering the EMF the
system tries to find a reasonable approximation to all the requested
attributes.

@param height:
 - if height>0: locate the font using the specified height as the typical cell height
 - if height<0: use the absolute value of the height as the typical glyph height.
@param width: typical glyph width.  If zero, the typical aspect ratio of the font is used.
@param escapement: angle, in degrees*10, of rendered string rotation.  Note that escapement and orientation must be the same.
@param orientation: angle, in degrees*10, of rendered string rotation.  Note that escapement and orientation must be the same.
@param weight: weight has (at least) the following values:
 - FW_DONTCARE
 - FW_THIN
 - FW_EXTRALIGHT
 - FW_ULTRALIGHT
 - FW_LIGHT
 - FW_NORMAL
 - FW_REGULAR
 - FW_MEDIUM
 - FW_SEMIBOLD
 - FW_DEMIBOLD
 - FW_BOLD
 - FW_EXTRABOLD
 - FW_ULTRABOLD
 - FW_HEAVY
 - FW_BLACK
@param italic: non-zero means try to find an italic version of the face.
@param underline: non-zero means to underline the glyphs.
@param strike_out: non-zero means to strike-out the glyphs.
@param charset: select the character set from the following list:
 - ANSI_CHARSET
 - DEFAULT_CHARSET
 - SYMBOL_CHARSET
 - SHIFTJIS_CHARSET
 - HANGEUL_CHARSET
 - HANGUL_CHARSET
 - GB2312_CHARSET
 - CHINESEBIG5_CHARSET
 - GREEK_CHARSET
 - TURKISH_CHARSET
 - HEBREW_CHARSET
 - ARABIC_CHARSET
 - BALTIC_CHARSET
 - RUSSIAN_CHARSET
 - EE_CHARSET
 - EASTEUROPE_CHARSET
 - THAI_CHARSET
 - JOHAB_CHARSET
 - MAC_CHARSET
 - OEM_CHARSET
@param out_precision: the precision of the face may have on of the
following values:
 - OUT_DEFAULT_PRECIS
 - OUT_STRING_PRECIS
 - OUT_CHARACTER_PRECIS
 - OUT_STROKE_PRECIS
 - OUT_TT_PRECIS
 - OUT_DEVICE_PRECIS
 - OUT_RASTER_PRECIS
 - OUT_TT_ONLY_PRECIS
 - OUT_OUTLINE_PRECIS
@param clip_precision: the precision of glyph clipping may have one of the
following values:
 - CLIP_DEFAULT_PRECIS
 - CLIP_CHARACTER_PRECIS
 - CLIP_STROKE_PRECIS
 - CLIP_MASK
 - CLIP_LH_ANGLES
 - CLIP_TT_ALWAYS
 - CLIP_EMBEDDED
@param quality: (subjective) quality of the font. Choose from the following
values:
 - DEFAULT_QUALITY
 - DRAFT_QUALITY
 - PROOF_QUALITY
 - NONANTIALIASED_QUALITY
 - ANTIALIASED_QUALITY
@param pitch_family: the pitch and family of the font face if the named font can't be found. Combine the pitch and style using a binary or.
 - Pitch:
   - DEFAULT_PITCH
   - FIXED_PITCH
   - VARIABLE_PITCH
   - MONO_FONT
 - Style:
   - FF_DONTCARE
   - FF_ROMAN
   - FF_SWISS
   - FF_MODERN
   - FF_SCRIPT
   - FF_DECORATIVE
@param name: ASCII string containing the name of the font face.
@return: handle of font.
@rtype: int
@type height: int
@type width: int
@type escapement: int
@type orientation: int
@type weight: int
@type italic: int
@type underline: int
@type strike_out: int
@type charset: int
@type out_precision: int
@type clip_precision: int
@type quality: int
@type pitch_family: int
@type name: string

        """
        return self._appendHandle(_EMR._EXTCREATEFONTINDIRECTW(height,width,escapement,orientation,weight,italic,underline,strike_out,charset,out_precision,clip_precision,quality,pitch_family,name))

    def TextOut(self,x,y,text):
        """

Draw a string of text at the given position using the current FONT and
other text attributes.
@param x: x position of text.
@param y: y position of text.
@param text: ASCII text string to render.
@return: true of string successfully drawn.

@rtype: int
@type x: int
@type y: int
@type text: string

        """
        e=_EMR._EXTTEXTOUTA(x,y,text)
        if not self._append(e):
            return 0
        return 1
 




if __name__ == "__main__":
    try:
        from optparse import OptionParser

        parser=OptionParser(usage="usage: %prog [options] emf-files...")
        parser.add_option("-v", action="store_true", dest="verbose", default=False)
        (options, args) = parser.parse_args()
    except:
        # hackola to work with Python 2.2, but this shouldn't be a
        # factor when imported in normal programs because __name__
        # will never equal "__main__", so this will never get called.
        class data:
            verbose=True

        options=data()
        args=sys.argv[1:]

    if len(args)>0:
        for filename in args:
            e=EMF(verbose=options.verbose)
            e.load(filename)
            print "Saving %s..." % (filename+".out")
            e.save(filename+".out")
            print "%s saved successfully." % (filename+".out")
    else:
        e=EMF(verbose=options.verbose)
        e.save("new.emf")
