#!/usr/bin/env python

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

GDI_typedefs={
    'SIZES':   (('h','cx'),('h','cy')),
    'SIZEL':   (('i','cx'),('i','cy')),
    'POINTS':  (('h','x'),('h','y')),
    'POINTL':  (('i','x'),('i','y')),
    'RECTL':   (('i','left'),('i','top'),('i','right'),('i','bottom')),
    'LOGPEN':  (('i','style'),('POINTL','width'),('i','color')),
    'XFORM':   (('f','eM11'),('f','eM12'),
                ('f','eM21'),('f','eM22'),
                ('f','eDx'),('f','eDy')),
    'EMRTEXT': (('POINTL','ptlReference'),('i','nChars'),('i','offString'),
                ('i','fOptions'),('RECTL','rcl'),('i','offDx')),
    'LOGFONTW':(('i','lfHeight'),('i','lfWidth'),
                ('i','lfEscapement'),('i','lfOrientation'),('i','lfWeight'),
                ('B','lfItalic'),('B','lfUnderline'),
                ('B','lfStrikeOut'),('B','lfCharSet'),
                ('B','lfOutPrecision'),('B','lfClipPrecision'),
                ('B','lfQuality'),
                ('B','lfPitchAndFamily'),('64s','lfFaceName')),
    'PANOSE':  (('B','bFamilyType'),('B','bSerifStyle'),('B','bWeight'),
                ('B','bProportion'),('B','bContrast'),
                ('B','bStrokeVariation'),('B','bArmStyle'),
                ('B','bLetterform'),('B','bMidline'),('B','bXHeight')),
    'EXTLOGFONTW': (('LOGFONTW','elfLogFont'),
                    ('128s','elfFullName'),('64s','elfStyle'),
                    ('i','elfVersion'),('i','elfStyleSize'),
                    ('i','elfMatch'),('i','elfReserved'),('i','elfVendorId'),
                    ('i','elfCulture'),('PANOSE','elfPanose')),
}


def round4(num):
    """Round to the nearest multiple of 4 greater than or equal to the
    given number.  EMF records are required to be aligned to 4 byte
    boundaries."""
    return ((num+3)/4)*4


class DC:
    def __init__(self):
        self.x=0
        self.y=0
        self.objects=[]


format_cache={} # dict mapping emr_id to class

def getFormat(typeid,typedef):
    if typeid in format_cache:
        return format_cache[typeid]
    format=EMR_FORMAT(typeid,typedef)
    format_cache[typeid]=format
    return format

class EMR_FORMAT:
    def __init__(self,emr_id,typedef):
        self.typedef=typedef
        self.id=emr_id
        self.fmtlist=[] # list of typecodes
        self.fmt="<" # string for pack/unpack.  little endian
        self.structsize=0

        self.names=[]
        self.namepos={}
        
        self.debug=0

        self.setFormat(typedef)

    def mangle(self,typecode,prefix,mangled=None):
        """return a list of names that can be used to retrieve values
        from the containing object.  Recursive.  Illustrates the
        problem of a default argument being an empty list.  The
        default argument is actually a reference, and it is the same
        reference each time.  So, if you call this multiple times with
        a default argument, the same list gets appended to."""
        if typecode in GDI_typedefs:
            for subtype,name in GDI_typedefs[typecode]:
                if self.debug: print "  found subtype=%s prefix=%s name=%s" % (subtype,prefix,name)
                mangled=self.mangle(subtype,prefix+"_"+name,mangled)
        else:
            #print mangled
            if mangled == None: mangled=[]
            mangled.append(prefix)
        return mangled
        

    def setFormat(self,typedef,prefix=""):
        if self.debug: print "typedef=%s" % str(typedef)
        if isinstance(typedef,list) or isinstance(typedef,tuple):
            for typecode,name in typedef:
                self.setFormatItem(typecode,prefix+name)
        elif typedef:
            raise AttributeError("format must be a list")

    def setFormatItem(self,typecode,name):
        if typecode in GDI_typedefs:
            self.setFormat(GDI_typedefs[typecode],name+"_")
        else:
            self.appendFormat(typecode,name)

    def appendFormat(self,typecode,name):
        self.fmt+=typecode
        self.fmtlist.append(typecode)
        self.namepos[name]=len(self.names)
        self.names.append(name)
        self.structsize=struct.calcsize(self.fmt)
        if self.debug: print "current struct=%s size=%d\n  names=%s" % (self.fmt,self.structsize,self.names)

    def extend(self,other):
        """Append another format object onto this one.  Probably
        should operate on a copy of the object so that the
        format_cache isn't altered."""
        for typecode,name in zip(other.fmtlist,other.names):
            self.appendFormat(typecode,name)
        self.typedef.extend(other.typedef)





class EMR_UNKNOWN(object): # extend from new-style class, or __getattr__ doesn't work
    """baseclass for EMR objects"""
    
    def __init__(self,typeid=0,typedef=None):
        self.iType=typeid
        self.nSize=0
        self.values=[] # list of values parsed from the input stream
        
        self.datasize=0
        self.data=None
        self.unhandleddata=None

        self.format=getFormat(typeid,typedef)


    def __getattr__(self,name):
        """Return EMR attribute if the name exists in the typedef list
        of the object.  This is only called when the standard
        attribute lookup fails on this object, so we don't have to
        handle the case where name is an actual attribute of self."""
        f=EMR_UNKNOWN.__getattribute__(self,'format')
        try:
            if name in f.names:
                v=EMR_UNKNOWN.__getattribute__(self,'values')
                index=f.namepos[name]
                return v[index]
        except IndexError:
            raise IndexError("name=%s index=%d values=%s" % (name,index,str(v)))
        raise AttributeError("%s not defined in EMR object" % name)

    def __setattr__(self,name,value):
        """Set a value in the object, propagating through to
        self.values[] if the name is in the typedef list."""
        if hasattr(self,'format'):
            f=EMR_UNKNOWN.__getattribute__(self,'format')
            try:
                if name in f.names:
                    v=EMR_UNKNOWN.__getattribute__(self,'values')
                    index=f.namepos[name]
                    v[index]=value
                else:
                    # it's not an automatically serializable item, so store it.
                    self.__dict__[name]=value
            except IndexError:
                raise IndexError("name=%s index=%d values=%s" % (name,index,str(v)))
        else:
            # We are very early-on in the initialization of the object
            # if format doesn't exist yet.  So, just store it as a
            # regular attribute.
            self.__dict__[name]=value

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
                    self.data+="\0"*(self.format.structsize-len(self.data))
                self.values=list(struct.unpack(self.format.fmt,self.data[0:self.format.structsize]))
            if self.datasize>self.format.structsize:
                self.unserializeExtra(self.data[self.format.structsize:])

    def unserializeExtend(self,format,data):
        """Extend the format structure with the specified format
        string and add the new data to self.values[].  The new format
        structure is appended to the existing format structure so that
        serialization of this new data will happen automatically."""
        if format.structsize<=len(data):
            vals=struct.unpack(format.fmt,data[0:format.structsize])
            print "new vals=%s" % str(vals)
            self.values.extend(vals)

            # Don't just append to the existing format, because this
            # would mess up the caching of the format.  Copy it.
            newformat=copy.deepcopy(self.format)
            newformat.extend(format)
            self.format=newformat

    def unserializeOffset(self,offset):
        """Adjust offset to point to correct location in extra data.
        Offsets in the EMR record are from the start of the record, so
        we must subtract 8 bytes for iType and nSize, and also
        subtract the size of the format structure."""
        return offset-8-self.format.structsize

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
        self.resize()
        fh.write(struct.pack("<ii",self.iType,self.nSize))
        fh.write(struct.pack(self.format.fmt,*self.values))
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
        fh.write(txt)
        extra=round4(len(txt))-len(txt)
        if extra>0:
            fh.write('\0'*extra)

    def resize(self):
        before=self.nSize
        self.nSize=8+self.format.structsize+self.sizeExtra()
        if before!=self.nSize:
            print "resize: before=%d after=%d" % (before,self.nSize)
            print self

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
        return "red=0x%02x green=0x%02x blue=0x%02x" % ((val&0xff),((val&0xff00)>8),((val&0xff0000)>16))

    def str_decode(self,typecode,name):
        val=EMR_UNKNOWN.__getattr__(self,name)
        if name.endswith("Color"):
            val=self.str_color(val)
        elif typecode.endswith("s"):
            val=val.decode('utf-16')
        return val
    
    def str_details(self):
        txt=StringIO()

        # EMR_UNKNOWN objects don't have a typedef, so only process
        # those that do
        if self.format.typedef:
            #print "typedef=%s" % str(self.format.typedef)
            for typecode,name in self.format.typedef:
                names=self.format.mangle(typecode,name)
                if len(names)>1:
                    txt.write("\t%-20s: %s\n" % (name," ".join(["%s=%s" % (subname.replace(name+"_",''),EMR_UNKNOWN.__getattr__(self,subname)) for subname in names])))
                else:
                    val=self.str_decode(typecode,name)
                    txt.write("\t%-20s: %s\n" % (name,val))
        txt.write(self.str_extra())
        return txt.getvalue()

    def __str__(self):
        ret=""
        details=self.str_details()
        if details:
            ret=os.linesep
        return "**%s: iType=%s nSize=%s  struct='%s' size=%d\n%s%s" % (self.__class__.__name__,self.iType,self.nSize,self.format.fmt,self.format.structsize,details,ret)
        return 


# Collection of classes

class EMR:

    class HEADER(EMR_UNKNOWN):
        """Header has different fields depending on the version of
        windows.  Also note that if offDescription==0, there is no
        description string."""

        emr_id=1
        
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('RECTL','rclBounds'),('RECTL','rclFrame'),('i','dSignature'),('i','nVersion'),('i','nBytes'),('i','nRecords'),('h','nHandles'),('h','sReserved'),('i','nDescription'),('i','offDescription'),('i','nPalEntries'),('SIZEL','szlDevice'),('SIZEL','szlMillimeters')])
            self.description=''

        def unserializeExtra(self,data):
            print "found %d extra bytes." % len(data)

            # subtract 8 because iType and nSize are always read
            # separately
            descriptionStart=self.unserializeOffset(self.offDescription)

            dataend=descriptionStart
            if dataend<=0:
                dataend=len(data)
            count=dataend
            print "dataend=%d count=%d len=%d" % (dataend,count,len(data))

            start=0
            new_typedefs=[
                [('i','cbPixelFormat'),('i','offPixelFormat'),('i','bOpenGL')],
                [('SIZEL','szlMicrometers')]
                ]
            for typedef in new_typedefs:
                format=EMR_FORMAT(-1,typedef)
                print "start=%d dataend=%d count=%d" % (start,dataend,count)
                if start+format.structsize<=count:
                    self.unserializeExtend(format,data[start:start+format.structsize])
                    start+=format.structsize
            
            print "bOpenGL=%d" % self.bOpenGL
            print "szlMicrometers_cx=%d" % self.szlMicrometers_cx

            if descriptionStart>0:
                count=len(data)-descriptionStart
                print "remaining: start=%d count=%d" % (descriptionStart,count)
                txt=data[descriptionStart:descriptionStart+count]
                print "str: %s" % (txt.decode('utf-16'))
                self.description=txt

        def sizeExtra(self):
            return round4(len(self.description))

        def serializeExtra(self,fh):
            self.serializeString(fh,self.description)



    class POLYBEZIER(EMR_UNKNOWN):
        emr_id=2
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('RECTL','rclBounds'),('i','cptl')])

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

    class POLYGON(POLYBEZIER):
        emr_id=3
        pass

    class POLYLINE(POLYBEZIER):
        emr_id=4
        pass

    class POLYBEZIERTO(POLYBEZIER):
        emr_id=5
        pass

    class POLYLINETO(POLYBEZIER):
        emr_id=6
        pass
    


    class POLYPOLYLINE(EMR_UNKNOWN):
        emr_id=7
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('RECTL','rclBounds'),('i','nPolys'),('i','cptl')])

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

    class POLYPOLYGON(POLYPOLYLINE):
        emr_id=8
        pass




    class SETWINDOWEXTEX(EMR_UNKNOWN):
        emr_id=9
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('SIZEL','szlExtent')])


    class SETWINDOWORGEX(EMR_UNKNOWN):
        emr_id=10
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('POINTL','ptlOrigin')])


    class SETVIEWPORTEXTEX(SETWINDOWEXTEX):
        emr_id=11
        pass


    class SETVIEWPORTORGEX(SETWINDOWORGEX):
        emr_id=12
        pass


    class SETBRUSHORGEX(SETWINDOWORGEX):
        emr_id=13
        pass


    class EOF(EMR_UNKNOWN):
        emr_id=14
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('i','nPalEntries'),('i','offPalEntries'),('i','nSizeLast')])
            # I don't know if I have a broken example or what, but
            # features.emf file only has a 12 byte long EOF record.
            # OpenOffice seems to handle it, though.


    class SETPIXELV(EMR_UNKNOWN):
        emr_id=15
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('POINTL','ptlPixel'),('i','crColor')])


    class SETMAPPERFLAGS(EMR_UNKNOWN):
        emr_id=16
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('i','dwFlags')])


    class SETMAPMODE(EMR_UNKNOWN):
        emr_id=17
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('i','iMode')])

            
    class SETBKMODE(SETMAPMODE):
        emr_id=18
        pass

            
    class SETPOLYFILLMODE(SETMAPMODE):
        emr_id=19
        pass

            
    class SETROP2(SETMAPMODE):
        emr_id=20
        pass

            
    class SETSTRETCHBLTMODE(SETMAPMODE):
        emr_id=21
        pass

            
    class SETTEXTALIGN(SETMAPMODE):
        emr_id=22
        pass

            
#define EMR_SETCOLORADJUSTMENT	23

    class SETTEXTCOLOR(EMR_UNKNOWN):
        emr_id=24
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('i','crColor')])


    class SETBKCOLOR(SETTEXTCOLOR):
        emr_id=25
        pass


#define EMR_OFFSETCLIPRGN	26


    class MOVETOEX(EMR_UNKNOWN):
        emr_id=27
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('POINTL','ptl')])


#define EMR_SETMETARGN	28
#define EMR_EXCLUDECLIPRECT	29
#define EMR_INTERSECTCLIPRECT	30

    class SCALEVIEWPORTEXTEX(EMR_UNKNOWN):
        emr_id=31
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('i','xNum'),('i','xDenom'),('i','yNum'),('i','yDenom')])

    class SCALEWINDOWEXTEX(SCALEVIEWPORTEXTEX):
        emr_id=32
        pass


    class SAVEDC(EMR_UNKNOWN):
        emr_id=33
        pass

    class RESTOREDC(EMR_UNKNOWN):
        emr_id=34
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('i','iRelative')])


    class SETWORLDTRANSFORM(EMR_UNKNOWN):
        emr_id=35
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('XFORM','xform')])

    class MODIFYWORLDTRANSFORM(EMR_UNKNOWN):
        emr_id=36
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('XFORM','xform'),('i','iMode')])


    class SELECTOBJECT(EMR_UNKNOWN):
        emr_id=37
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('i','ihObject')])


    # Note: a line will still be drawn when the linewidth==0.  To force an
    # invisible line, use style=PS_NULL
    class CREATEPEN(EMR_UNKNOWN):
        emr_id=38
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('i','ihPen'),('LOGPEN','lopn')])


    class CREATEBRUSHINDIRECT(EMR_UNKNOWN):
        emr_id=39
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('i','ihBrush'),('I','lbStyle'),('i','lbColor'),('I','lbHatch')])


    class DELETEOBJECT(SELECTOBJECT):
        emr_id=40
        pass


    class ANGLEARC(EMR_UNKNOWN):
        emr_id=41
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('POINTL','ptlCenter'),('i','nRadius'),('f','eStartAngle'),('f','eSweepAngle')])


    class ELLIPSE(EMR_UNKNOWN):
        emr_id=42
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('RECTL','rclBox')])


    class RECTANGLE(ELLIPSE):
        emr_id=43
        pass


    class ROUNDRECT(EMR_UNKNOWN):
        emr_id=44
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('RECTL','rclBox'),('SIZEL','szlCorner')])


    class ARC(EMR_UNKNOWN):
        emr_id=45
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('RECTL','rclBox'),('POINTL','ptlStart'),('POINTL','ptlEnd')])

    class CHORD(ARC):
        emr_id=46
        pass


    class PIE(ARC):
        emr_id=47
        pass


    class SELECTPALLETE(EMR_UNKNOWN):
        emr_id=48
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('i','ihPal')])
        

#define EMR_CREATEPALETTE	49
#define EMR_SETPALETTEENTRIES	50
#define EMR_RESIZEPALETTE	51
#define EMR_REALIZEPALETTE	52
#define EMR_EXTFLOODFILL	53


    class LINETO(MOVETOEX):
        emr_id=54
        pass


    class ARCTO(ARC):
        emr_id=55
        pass


#define EMR_POLYDRAW	56


    class SETARCDIRECTION(EMR_UNKNOWN):
        emr_id=57
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('i','iArcDirection')])
        


#define EMR_SETMITERLIMIT	58


    class BEGINPATH(EMR_UNKNOWN):
        emr_id=59
        pass


    class ENDPATH(EMR_UNKNOWN):
        emr_id=60
        pass


    class CLOSEFIGURE(EMR_UNKNOWN):
        emr_id=61
        pass


    class FILLPATH(EMR_UNKNOWN):
        emr_id=62
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('RECTL','rclBounds')])
        

    class STROKEANDFILLPATH(FILLPATH):
        emr_id=63
        pass


    class STROKEPATH(FILLPATH):
        emr_id=64
        pass


    class FLATTENPATH(EMR_UNKNOWN):
        emr_id=65
        pass


    class WIDENPATH(EMR_UNKNOWN):
        emr_id=66
        pass


#define EMR_SELECTCLIPPATH	67


    class ABORTPATH(EMR_UNKNOWN):
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



    class EXTCREATEFONTINDIRECTW(EMR_UNKNOWN):
        emr_id=82

        # Note: all the strings here (font names, etc.) are unicode
        # strings.
        
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('i','ihFont'),('EXTLOGFONTW','elfw')])



    class EXTTEXTOUTA(EMR_UNKNOWN):
        emr_id=83
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('RECTL','rclBounds'),('i','iGraphicsMode'),('f','exScale'),('f','eyScale'),('EMRTEXT','emrtext')])
            self.string=""
            self.charsize=1

        def unserializeExtra(self,data):
            print "found %d extra bytes.  nChars=%d" % (len(data),self.emrtext_nChars)

            start=0
            print "offDx=%d offString=%d" % (self.emrtext_offDx,self.emrtext_offString)

            # Note: offsets may appear before OR after string.  Don't
            # assume they will appear first.
            if self.emrtext_offDx>0:
                start=self.unserializeOffset(self.emrtext_offDx)
                start,self.dx=self.unserializeList("i",self.emrtext_nChars,data,start)
            else:
                self.dx=[]
                
            if self.emrtext_offString>0:
                start=self.unserializeOffset(self.emrtext_offString)
                self.string=data[start:start+(self.charsize*self.emrtext_nChars)]
            else:
                self.string=""

        def sizeExtra(self):
            offset=self.serializeOffset()
            sizedx=0
            sizestring=0

            if len(self.dx)>0:
                self.emrtext_offDx=offset
                sizedx=struct.calcsize("i")*self.emrtext_nChars
                offset+=sizedx
            if len(self.string)>0:
                self.emrtext_nChars=len(self.string)/self.charsize
                self.emrtext_offString=offset
                sizestring=round4(self.charsize*self.emrtext_nChars)
                
            return (sizedx+sizestring)

        def serializeExtra(self,fh):
            if self.emrtext_offDx>0:
                self.serializeList(fh,"i",self.dx)
            if self.emrtext_offString>0:
                self.serializeString(fh,self.string)

        def str_extra(self):
            txt=StringIO()
            txt.write("\tdx: %s\n" % str(self.dx))
            txt.write("\tstring: %s\n" % str(self.string.decode('utf-16')))
                    
            return txt.getvalue()


    class EXTTEXTOUTW(EXTTEXTOUTA):
        emr_id=84

        def __init__(self):
            EMR.EXTTEXTOUTA.__init__(self)
            self.charsize=2




    class POLYBEZIER16(EMR_UNKNOWN):
        emr_id=85
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('RECTL','rclBounds'),('i','cpts')])

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

    class POLYGON16(POLYBEZIER16):
        emr_id=86
        pass

    class POLYLINE16(POLYBEZIER16):
        emr_id=87
        pass

    class POLYBEZIERTO16(POLYBEZIER16):
        emr_id=88
        pass

    class POLYLINETO16(POLYBEZIER16):
        emr_id=89
        pass
    


    class POLYPOLYLINE16(EMR_UNKNOWN):
        emr_id=90
        def __init__(self):
            EMR_UNKNOWN.__init__(self,self.emr_id,[('RECTL','rclBounds'),('i','nPolys'),('i','cpts')])

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

    class POLYPOLYGON16(POLYPOLYLINE16):
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
for name in dir(EMR):
    #print name
    cls=getattr(EMR,name,None)
    if cls and callable(cls) and issubclass(cls,EMR_UNKNOWN):
        #print "subclass! id=%d %s" % (cls.emr_id,str(cls))
        emrmap[cls.emr_id]=cls

class EMF:
    def __init__(self):
        self.filename=None
        self.dc=DC()
        self.record=[]

    def load(self,filename=None):
        if filename:
            self.filename=filename

        if self.filename:
            fh=open(self.filename)
            self.unserialize(fh)

    def unserialize(self,fh):
        try:
            count=1
            while count>0:
                data=fh.read(8)
                count=len(data)
                if count>0:
                    (iType,nSize)=struct.unpack("<ii",data)
                    print "EMF:  iType=%d nSize=%d" % (iType,nSize)

                    if iType in emrmap:
                        e=emrmap[iType]()
                    else:
                        e=EMR_UNKNOWN()

                    e.unserialize(fh,iType,nSize)
                    self.record.append(e)
                    print e
                
        except EOFError:
            pass

    def save(self,filename=None):
        if filename:
            self.filename=filename

        if self.filename:
            fh=open(self.filename,"wb")
            self.serialize(fh)
            fh.close()
                

    def serialize(self,fh):
        for e in self.record:
            #print e
            e.serialize(fh)



##    # Do some optimization here, like convert to 16 bit values if possible, and convert to a rectangle if it is a rectangle
##    def Polygon(self,points):
##        if len(points)==4:
##            if points[0][0]==points[1][0] and points[2][0]==points[3][0] and points[0][1]==points[3][1] and points[1][1]==points[2][1]:
##                print "converting to rectangle, option 1:"
##                pyemf.Rectangle(self.dc,points[0][0],points[0][1],points[2][0],points[2][1])
##                return
##            elif points[0][1]==points[1][1] and points[2][1]==points[3][1] and points[0][0]==points[3][0] and points[1][0]==points[2][0]:
##                print "converting to rectangle, option 2:"
##                pyemf.Rectangle(self.dc,points[0][0],points[0][1],points[2][0],points[2][1])
##                return

    


if __name__ == "__main__":
    from optparse import OptionParser

    parser=OptionParser(usage="usage: %prog [options] emf-files...")
    (options, args) = parser.parse_args()

    for filename in args:
        e=EMF()
        e.load(filename)
        e.save(filename+".out")
