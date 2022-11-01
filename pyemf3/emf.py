import struct
from io import BytesIO

from . import emr
from .dc import DC, RGB
from . import const

def _normalizeColor(c):
    """
Normalize the input into a packed integer.  If the input is a tuple,
pass it through L{RGB} to generate the color value.

@param c: color
@type c: int or (r,g,b) tuple
@return: packed integer color from L{RGB}
@rtype: int
"""
    if isinstance(c,int):
        return c
    if isinstance(c,tuple) or isinstance(c,list):
        return RGB(*c)
    raise TypeError("Color must be specified as packed integer or 3-tuple (r,g,b)")

class EMF:
    """
Reference page of the public API for enhanced metafile creation.  See
L{pyemf} for an overview / mini tutorial.

@group Creating Metafiles: __init__, load, save
@group Drawing Parameters: GetStockObject, SelectObject, DeleteObject, CreatePen, CreateSolidBrush, CreateHatchBrush, SetBkColor, SetBkMode, SetPolyFillMode
@group Drawing Primitives: SetPixel, Polyline, PolyPolyline, Polygon, PolyPolygon, Rectangle, RoundRect, Ellipse, Arc, Chord, Pie, PolyBezier
@group Path Primatives: BeginPath, EndPath, MoveTo, LineTo, PolylineTo, ArcTo,
 PolyBezierTo, CloseFigure, FillPath, StrokePath, StrokeAndFillPath
@group Clipping: SelectClipPath
@group Text: CreateFont, SetTextAlign, SetTextColor, TextOut
@group Coordinate System Transformation: SaveDC, RestoreDC, SetWorldTransform, ModifyWorldTransform
@group **Experimental** -- Viewport Manipulation: SetMapMode, SetViewportOrgEx, GetViewportOrgEx, SetWindowOrgEx, GetWindowOrgEx, SetViewportExtEx, ScaleViewportExtEx, GetViewportExtEx, SetWindowExtEx, ScaleWindowExtEx, GetWindowExtEx

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
        self.dc=DC(width,height,density,units)
        self.records=[]

        # path recordkeeping
        self.pathstart=0

        self.verbose=verbose

        # if True, scale the image using only the header, and not
        # using MapMode or SetWindow/SetViewport.
        self.scaleheader=True

        hdr=emr.HEADER(description)
        self._append(hdr)
        if not self.scaleheader:
            self.SetMapMode(MM_ANISOTROPIC)
            self.SetWindowExtEx(self.dc.pixelwidth,self.dc.pixelheight)
            self.SetViewportExtEx(
                int(self.dc.width/100.0*self.dc.ref_pixelwidth/self.dc.ref_width),
                int(self.dc.height/100.0*self.dc.ref_pixelheight/self.dc.ref_height))


    def loadmem(self,membuf=None):
        """
Read an existing buffer from a string of bytes.  If any records exist
in the current object, they will be overwritten by the records from
this buffer.

@param membuf: buffer to load
@type membuf: string
@returns: True for success, False for failure.
@rtype: Boolean
        """
        fh = BytesIO(membuf)
        self._load(fh)

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
            fh=open(self.filename,'rb')
            self._load(fh)

    def _load(self,fh):
        self.records=[]
        self._unserialize(fh)
        self.scaleheader=False
        # get DC from header record
        self.dc.getBounds(self.records[0])


    def _unserialize(self,fh):
        try:
            count=1
            while count>0:
                data=fh.read(8)
                count=len(data)
                if count>0:
                    (iType,nSize)=struct.unpack("<ii",data)
                    if self.verbose: print("EMF:  iType=%d nSize=%d" % (iType,nSize))

                    if iType in emr.emrmap:
                        e=emr.emrmap[iType]()
                    else:
                        e=emr.EMR_UNKNOWN()

                    e.unserialize(fh,data,iType,nSize)
                    self.records.append(e)

                    if e.hasHandle():
                        self.dc.addObject(e,e.handle)
                    elif isinstance(e,emr.DELETEOBJECT):
                        self.dc.removeObject(e.handle)

                    if self.verbose:
                        print("Unserializing: ", end=' ')
                        print(e)

        except EOFError:
            pass

    def _append(self,e):
        """Append an EMR to the record list, unless the record has
        been flagged as having an error."""
        if not e.error:
            if self.verbose:
                print("Appending: ", end=' ')
                print(e)
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
        if not isinstance(end,emr.EOF):
            if self.verbose: print("adding EOF record")
            e=emr.EOF()
            self._append(e)
        header=self.records[0]
        header.setBounds(self.dc,self.scaleheader)
        header.nRecords=len(self.records)
        header.nHandles=len(self.dc.objects)
        size=0
        for e in self.records:
            e.resize()
            size+=e.nSize
            if self.verbose: print("size=%d total=%d" % (e.nSize,size))
        if self.verbose: print("total: %s bytes" % size)
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
            if self.verbose: print(e)
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
        return ((left,top),(right,bottom))

    def _mergeBounds(self,bounds,itembounds):
        if itembounds:
            if itembounds[0][0]<bounds[0][0]: bounds[0][0]=itembounds[0][0]
            if itembounds[0][1]<bounds[0][1]: bounds[0][1]=itembounds[0][1]
            if itembounds[1][0]>bounds[1][0]: bounds[1][0]=itembounds[1][0]
            if itembounds[1][1]>bounds[1][1]: bounds[1][1]=itembounds[1][1]

    def _getPathBounds(self):
        """Get the bounding rectangle for the list of EMR records
        starting from the last saved path start to the current record."""
        # If there are no bounds supplied, default to the EMF standard
        # of ((0,0),(-1,-1)) which means that the bounds aren't
        # precomputed.
        bounds=[[0,0],[-1,-1]]

        # find the first bounds
        for i in range(self.pathstart,len(self.records)):
            #print "FIXME: checking initial bounds on record %d" % i
            e=self.records[i]
            # print e
            # print "bounds=%s" % str(e.getBounds())
            objbounds=e.getBounds()
            if objbounds:
                #print "bounds=%s" % str(objbounds)
                # have to copy the object manually because we don't
                # want to overwrite the object's bounds
                bounds=[[objbounds[0][0],objbounds[0][1]],
                        [objbounds[1][0],objbounds[1][1]]]
                break

        # if there are more records with bounds, merge them
        for j in range(i,len(self.records)):
            #print "FIXME: checking bounds for more records: %d" % j
            e=self.records[j]
            # print e
            # print "bounds=%s" % str(e.getBounds())
            self._mergeBounds(bounds,e.getBounds())

        return bounds

    def _useShort(self,bounds):
        """Determine if we can use the shorter 16-bit EMR structures.
        If all the numbers can fit within 16 bit integers, return
        true.  The bounds 4-tuple is (left,top,right,bottom)."""

        SHRT_MIN=-32768
        SHRT_MAX=32767
        if bounds[0][0]>=SHRT_MIN and bounds[0][1]>=SHRT_MIN and bounds[1][0]<=SHRT_MAX and bounds[1][1]<=SHRT_MAX:
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

    def _appendOptimizePoly16(self,polylist,cls16,cls):
        """polylist is a list of lists of points, where each inner
        list represents a single polygon or line.  The number of
        polygons is the size of the outer list."""
        points=[]
        polycounts=[]
        for polygon in polylist:
            count=0
            for point in polygon:
                points.append(point)
                count+=1
            polycounts.append(count)

        bounds=self._getBounds(points)
        if self._useShort(bounds):
            e=cls16(points,polycounts,bounds)
        else:
            e=cls(points,polycounts,bounds)
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
        if obj>=0 and obj<=const.STOCK_LAST:
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
        return self._append(emr.SELECTOBJECT(self.dc,handle))

    def DeleteObject(self,handle):
        """

Delete the given graphics object. Note that, now, only those contexts
into which the object has been selected get a delete object
records.

@param    handle:  	handle of graphics object to delete.

@return:    true if the object was successfully deleted.
@rtype: int
@type handle: int

        """
        e=emr.DELETEOBJECT(self.dc,handle)
        self.dc.removeObject(handle)
        return self._append(e)

    def CreatePen(self,style,width,color,styleentries=None):
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
@param    styleentries: optional list of dash codes for custom dash

@return:    handle to the new pen graphics object.
@rtype: int
@type style: int
@type width: int
@type color: int

        """

        if styleentries is None:
            handle = emr.CREATEPEN(style, width, _normalizeColor(color))
        else:
            handle = emr.EXTCREATEPEN(
                style=style, width=width, color=_normalizeColor(color),
                styleentries=styleentries)

        return self._appendHandle(handle)

    def CreateSolidBrush(self,color):
        """

Create a solid brush used to fill polygons.
@param color: the L{color<RGB>} of the solid brush.
@return: handle to brush graphics object.

@rtype: int
@type color: int

        """
        return self._appendHandle(emr.CREATEBRUSHINDIRECT(color=_normalizeColor(color)))

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
        return self._appendHandle(emr.CREATEBRUSHINDIRECT(hatch=hatch,color=_normalizeColor(color)))

    def SetBkColor(self,color):
        """

Set the background color used for any transparent regions in fills or
hatched brushes.

B{Note:} Currently appears sporadically supported in OpenOffice.

@param color: background L{color<RGB>}.
@return: previous background L{color<RGB>}.
@rtype: int
@type color: int

        """
        e=emr.SETBKCOLOR(_normalizeColor(color))
        if not self._append(e):
            return 0
        return 1

    def SetBkMode(self,mode):
        """

Set the background mode for interaction between transparent areas in
the region to be drawn and the existing background.

The choices for mode are:
 - TRANSPARENT
 - OPAQUE

B{Note:} Currently appears sporadically supported in OpenOffice.

@param mode: background mode.
@return: previous background mode.
@rtype: int
@type mode: int

        """
        e=emr.SETBKMODE(mode)
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
        e=emr.SETPOLYFILLMODE(mode)
        if not self._append(e):
            return 0
        return 1

    def SetMapMode(self,mode):
        """

Set the window mapping mode.  This is the mapping between pixels in page space to pixels in device space.  Page space is the coordinate system that is used for all the drawing commands -- it is how pixels are identified and figures are placed in the metafile.  They are integer units.

Device space is the coordinate system of the final output, measured in physical dimensions such as mm, inches, or twips.  It is this coordinate system that provides the scaling that makes metafiles into a scalable graphics format.
 - MM_TEXT: each unit in page space is mapped to one pixel
 - MM_LOMETRIC: 1 page unit = .1 mm in device space
 - MM_HIMETRIC: 1 page unit = .01 mm in device space
 - MM_LOENGLISH: 1 page unit = .01 inch in device space
 - MM_HIENGLISH: 1 page unit = .001 inch in device space
 - MM_TWIPS: 1 page unit = 1/20 point (or 1/1440 inch)
 - MM_ISOTROPIC: 1 page unit = user defined ratio, but axes equally scaled
 - MM_ANISOTROPIC: 1 page unit = user defined ratio, axes may be independently scaled
@param mode: window mapping mode.
@return: previous window mapping mode, or zero if error.
@rtype: int
@type mode: int
        """
        e=emr.SETMAPMODE(mode)
        if not self._append(e):
            return 0
        return 1

    def SetViewportOrgEx(self,xv,yv):
        """

Set the origin of the viewport, which translates the origin of the
coordinate system by (xv,yv).  A pixel drawn at (x,y) in the new
coordinate system will be displayed at (x+xv,y+yv) in terms of the
previous coordinate system.

Contrast this with L{SetWindowOrgEx}, which seems to be the opposite
translation.  So, if in addition, the window origin is set to (xw,yw)
using L{SetWindowOrgEx}, a pixel drawn at (x,y) will be displayed at
(x-xw+xv,y-yw+yv) in terms of the original coordinate system.


@param xv: new x position of the viewport origin.
@param yv: new y position of the viewport origin.
@return: previous viewport origin
@rtype: 2-tuple (x,y) if successful, or None if unsuccessful
@type xv: int
@type yv: int
        """
        e=emr.SETVIEWPORTORGEX(xv,yv)
        if not self._append(e):
            return None
        old=(self.dc.viewport_x,self.dc.viewport_y)
        self.dc.viewport_x=xv
        self.dc.viewport_y=yv
        return old

    def GetViewportOrgEx(self):
        """

Get the origin of the viewport.
@return: returns the current viewport origin.
@rtype: 2-tuple (x,y)
        """
        return (self.dc.viewport_x,self.dc.viewport_y)

    def SetWindowOrgEx(self,xw,yw):
        """

Set the origin of the window, which translates the origin of the
coordinate system by (-xw,-yw).  A pixel drawn at (x,y) in the new
coordinate system will be displayed at (x-xw,y-yw) in terms of the
previous coordinate system.

Contrast this with L{SetViewportOrgEx}, which seems to be the opposite
translation.  So, if in addition, the viewport origin is set to
(xv,yv) using L{SetViewportOrgEx}, a pixel drawn at (x,y) will be
displayed at (x-xw+xv,y-yw+yv) in terms of the original coordinate
system.

@param xw: new x position of the window origin.
@param yw: new y position of the window origin.
@return: previous window origin
@rtype: 2-tuple (x,y) if successful, or None if unsuccessful
@type xw: int
@type yw: int
        """
        e=emr.SETWINDOWORGEX(xw,yw)
        if not self._append(e):
            return None
        old=(self.dc.window_x,self.dc.window_y)
        self.dc.window_x=xw
        self.dc.window_y=yw
        return old

    def GetWindowOrgEx(self):
        """

Get the origin of the window.
@return: returns the current window  origin.
@rtype: 2-tuple (x,y)

        """
        return (self.dc.window_x,self.dc.window_y)

    def SetViewportExtEx(self,x,y):
        """
Set the dimensions of the viewport in device units.  Device units are
physical dimensions, in millimeters.  The total extent is equal to the
width is millimeters multiplied by the density of pixels per
millimeter in that dimension.

Note: this is only usable when L{SetMapMode} has been set to
MM_ISOTROPIC or MM_ANISOTROPIC.

@param x: new width of the viewport.
@param y: new height of the viewport.
@return: returns the previous size of the viewport.
@rtype: 2-tuple (width,height) if successful, or None if unsuccessful
@type x: int
@type y: int
        """
        e=emr.SETVIEWPORTEXTEX(x,y)
        if not self._append(e):
            return None
        old=(self.dc.viewport_ext_x,self.dc.viewport_ext_y)
        self.dc.viewport_ext_x=xv
        self.dc.viewport_ext_y=yv
        return old

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
        e=emr.EMR._SCALEVIEWPORTEXTEX(x_num,x_den,y_num,y_den)
        if not self._append(e):
            return None
        old=(self.dc.viewport_ext_x,self.dc.viewport_ext_y)
        self.dc.viewport_ext_x=old[0]*x_num/x_den
        self.dc.viewport_ext_y=old[1]*y_num/y_den
        return old

    def GetViewportExtEx(self):
        """

Get the dimensions of the viewport in device units (i.e. physical dimensions).
@return: returns the size of the viewport.
@rtype: 2-tuple (width,height)

        """
        old=(self.dc.viewport_ext_x,self.dc.viewport_ext_y)
        return old

    def SetWindowExtEx(self,x,y):
        """

Set the dimensions of the window.  Window size is measured in integer
numbers of pixels (logical units).

Note: this is only usable when L{SetMapMode} has been set to
MM_ISOTROPIC or MM_ANISOTROPIC.

@param x: new width of the window.
@param y: new height of the window.
@return: returns the previous size of the window.
@rtype: 2-tuple (width,height) if successful, or None if unsuccessful
@type x: int
@type y: int
        """
        e=emr.SETWINDOWEXTEX(x,y)
        if not self._append(e):
            return None
        old=(self.dc.window_ext_x,self.dc.window_ext_y)
        self.dc.window_ext_x=x
        self.dc.window_ext_y=y
        return old

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
        e=emr.SCALEWINDOWEXTEX(x_num,x_den,y_num,y_den)
        if not self._append(e):
            return None
        old=(self.dc.window_ext_x,self.dc.window_ext_y)
        self.dc.window_ext_x=old[0]*x_num/x_den
        self.dc.window_ext_y=old[1]*y_num/y_den
        return old

    def GetWindowExtEx(self):
        """

Get the dimensions of the window in logical units (integer numbers of pixels).
@return: returns the size of the window.
@rtype: 2-tuple (width,height)
        """
        old=(self.dc.window_ext_x,self.dc.window_ext_y)
        return old


    def SetWorldTransform(self,m11=1.0,m12=0.0,m21=0.0,m22=1.0,dx=0.0,dy=0.0):
        """
Set the world coordinate to logical coordinate linear transform for
subsequent operations.  With this matrix operation, you can translate,
rotate, scale, shear, or a combination of all four.  The matrix
operation is defined as follows where (x,y) are the original
coordinates and (x',y') are the transformed coordinates::

 | x |   | m11 m12 0 |   | x' |
 | y | * | m21 m22 0 | = | y' |
 | 0 |   | dx  dy  1 |   | 0  |

or, the same thing defined as a system of linear equations::

 x' = x*m11 + y*m21 + dx
 y' = x*m12 + y*m22 + dy

http://msdn.microsoft.com/library/en-us/gdi/cordspac_0inn.asp
says that the offsets are in device coordinates, not pixel
coordinates.

B{Note:} Currently partially supported in OpenOffice.

@param m11: matrix entry
@type m11: float
@param m12: matrix entry
@type m12: float
@param m21: matrix entry
@type m21: float
@param m22: matrix entry
@type m22: float
@param dx: x shift
@type dx: float
@param dy: y shift
@type dy: float
@return: status
@rtype: boolean

        """
        return self._append(emr.SETWORLDTRANSFORM(m11,m12,m21,m22,dx,dy))

    def ModifyWorldTransform(self,mode,m11=1.0,m12=0.0,m21=0.0,m22=1.0,dx=0.0,dy=0.0):
        """
Change the current linear transform.  See L{SetWorldTransform} for a
description of the matrix parameters.  The new transform may be
modified in one of three ways, set by the mode parameter:

 - MWT_IDENTITY: reset the transform to the identity matrix (the matrix parameters are ignored).
 - MWT_LEFTMULTIPLY: multiply the matrix represented by these parameters by the current world transform to get the new transform.
 - MWT_RIGHTMULTIPLY: multiply the current world tranform by the matrix represented here to get the new transform.

The reason that there are two different multiplication types is that
matrix multiplication is not commutative, which means the order of
multiplication makes a difference.

B{Note:} The parameter order was changed from GDI standard so that I
could make the matrix parameters optional in the case of MWT_IDENTITY.

B{Note:} Currently appears unsupported in OpenOffice.

@param mode: MWT_IDENTITY, MWT_LEFTMULTIPLY, or MWT_RIGHTMULTIPLY
@type mode: int
@param m11: matrix entry
@type m11: float
@param m12: matrix entry
@type m12: float
@param m21: matrix entry
@type m21: float
@param m22: matrix entry
@type m22: float
@param dx: x shift
@type dx: float
@param dy: y shift
@type dy: float
@return: status
@rtype: boolean

        """
        return self._append(emr.MODIFYWORLDTRANSFORM(m11,m12,m21,m22,dx,dy,mode))


    def SetPixel(self,x,y,color):
        """

Set the pixel to the given color.
@param x: the horizontal position.
@param y: the vertical position.
@param color: the L{color<RGB>} to set the pixel.
@type x: int
@type y: int
@type color: int or (r,g,b) tuple

        """
        return self._append(emr.SETPIXELV(x,y,_normalizeColor(color)))

    def Polyline(self,points):
        """

Draw a sequence of connected lines.
@param points: list of x,y tuples
@return: true if polyline is successfully rendered.
@rtype: int
@type points: tuple

        """
        return self._appendOptimize16(points,emr.POLYLINE16,emr.POLYLINE)


    def PolyPolyline(self,polylines):
        """

Draw multiple polylines.  The polylines argument is a list of lists,
where each inner list represents a single polyline.  Each polyline is
described by a list of x,y tuples as in L{Polyline}.  For example::

  lines=[[(100,100),(200,100)],
         [(300,100),(400,100)]]
  emf.PolyPolyline(lines)

draws two lines, one from 100,100 to 200,100, and another from 300,100
to 400,100.

@param polylines: list of lines, where each line is a list of x,y tuples
@type polylines: list
@return: true if polypolyline is successfully rendered.
@rtype: int

        """
        return self._appendOptimizePoly16(polylines,emr.POLYPOLYLINE16,emr.POLYPOLYLINE)


    def Polygon(self,points):
        """

Draw a closed figure bounded by straight line segments.  A polygon is
defined by a list of points that define the endpoints for a series of
connected straight line segments.  The end of the last line segment is
automatically connected to the beginning of the first line segment,
the border is drawn with the current pen, and the interior is filled
with the current brush.  See L{SetPolyFillMode} for the fill effects
when an overlapping polygon is defined.

@param points: list of x,y tuples
@return: true if polygon is successfully rendered.
@rtype: int
@type points: tuple

        """
        if len(points)==4:
            if points[0][0]==points[1][0] and points[2][0]==points[3][0] and points[0][1]==points[3][1] and points[1][1]==points[2][1]:
                if self.verbose: print("converting to rectangle, option 1:")
                return self.Rectangle(points[0][0],points[0][1],points[2][0],points[2][1])
            elif points[0][1]==points[1][1] and points[2][1]==points[3][1] and points[0][0]==points[3][0] and points[1][0]==points[2][0]:
                if self.verbose: print("converting to rectangle, option 2:")
                return self.Rectangle(points[0][0],points[0][1],points[2][0],points[2][1])
        return self._appendOptimize16(points,emr.POLYGON16,emr.POLYGON)


    def PolyPolygon(self,polygons):
        """

Draw multiple polygons.  The polygons argument is a list of lists,
where each inner list represents a single polygon.  Each polygon is
described by a list of x,y tuples as in L{Polygon}.  For example::

  lines=[[(100,100),(200,100),(200,200),(100,200)],
         [(300,100),(400,100),(400,200),(300,200)]]
  emf.PolyPolygon(lines)

draws two squares.

B{Note:} Currently partially supported in OpenOffice.  The line width
is ignored and the polygon border is not closed (the final point is
not connected to the starting point in each polygon).

@param polygons: list of polygons, where each polygon is a list of x,y tuples
@type polygons: list
@return: true if polypolygon is successfully rendered.
@rtype: int

        """
        return self._appendOptimizePoly16(polygons,emr.POLYPOLYGON16,emr.POLYPOLYGON)


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
        return self._append(emr.ELLIPSE(((left,top),(right,bottom))))

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
        return self._append(emr.RECTANGLE(((left,top),(right,bottom))))

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
        return self._append(emr.ROUNDRECT((((left,top),(right,bottom)),
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
        return self._append(emr.ARC(((left,top),(right,bottom)),
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
        return self._append(emr.CHORD(
            ((left,top),(right,bottom)),
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
        if xstart==xend and ystart==yend:
            # Fix for OpenOffice: doesn't render a full ellipse when
            # the start and end angles are the same
            e=emr.ELLIPSE(((left,top),(right,bottom)))
        else:
            e=emr.PIE(((left,top),(right,bottom)),xstart,ystart,xend,yend)
        return self._append(e)

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
        return self._appendOptimize16(points,emr.POLYBEZIER16,emr.POLYBEZIER)

    def BeginPath(self):
        """

Begin defining a path.  Any previous unclosed paths are discarded.
@return: true if successful.
@rtype: int

        """
        # record next record number as first item in path
        self.pathstart=len(self.records)
        return self._append(emr.BEGINPATH())

    def EndPath(self):
        """

End the path definition.
@return: true if successful.
@rtype: int

        """
        return self._append(emr.ENDPATH())

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
        return self._append(emr.MOVETOEX(x,y))

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
        return self._append(emr.LINETO(x,y))

    def PolylineTo(self,points):
        """

Draw a sequence of connected lines starting from the current
position and update the position to the final point in the list.

@param points: list of x,y tuples
@return: true if polyline is successfully rendered.
@rtype: int
@type points: tuple

        """
        return self._appendOptimize16(points,emr.POLYLINETO16,emr.POLYLINETO)

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
        return self._append(emr.ARCTO(
            ((left,top),(right,bottom)),
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
        return self._appendOptimize16(points,emr.POLYBEZIERTO16,emr.POLYBEZIERTO)

    def CloseFigure(self):
        """

Close a currently open path, which connects the current position to the starting position of a figure.  Usually the starting position is the most recent call to L{MoveTo} after L{BeginPath}.

@return: true if successful

@rtype: int

        """
        return self._append(emr.CLOSEFIGURE())

    def FillPath(self):
        """

Close any currently open path and fills it using the currently
selected brush and polygon fill mode.

@return: true if successful.
@rtype: int

        """
        bounds=self._getPathBounds()
        return self._append(emr.FILLPATH(bounds))

    def StrokePath(self):
        """

Close any currently open path and outlines it using the currently
selected pen.

@return: true if successful.
@rtype: int

        """
        bounds=self._getPathBounds()
        return self._append(emr.STROKEPATH(bounds))

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
        return self._append(emr.STROKEANDFILLPATH(bounds))

    def SelectClipPath(self,mode=const.RGN_COPY):
        """

Use the current path as the clipping path.  The current path must be a
closed path (i.e. with L{CloseFigure} and L{EndPath})

B{Note:} Currently unsupported in OpenOffice -- it apparently uses the
bounding rectangle of the path as the clip area, not the path itself.

@param mode: one of the following values that specifies how to modify the clipping path
 - RGN_AND: the new clipping path becomes the intersection of the old path and the current path
 - RGN_OR: the new clipping path becomes the union of the old path and the current path
 - RGN_XOR: the new clipping path becomes the union of the old path and the current path minus the intersection of the old and current path
 - RGN_DIFF: the new clipping path becomes the old path where any overlapping region of the current path is removed
 - RGN_COPY: the new clipping path is set to the current path and the old path is thrown away

@return: true if successful.
@rtype: int

        """
        return self._append(emr.SELECTCLIPPATH(mode))

    def SaveDC(self):
        """

Saves the current state of the graphics mode (such as line and fill
styles, font, clipping path, drawing mode and any transformations) to
a stack.  This state can be restored by L{RestoreDC}.

B{Note:} Currently unsupported in OpenOffice -- it apparently uses the
bounding rectangle of the path as the clip area, not the path itself.

@return: value of the saved state.
@rtype: int

        """
        return self._append(emr.SAVEDC())

    def RestoreDC(self,stackid):
        """

Restores the state of the graphics mode to a stack.  The L{stackid}
parameter is either a value returned by L{SaveDC}, or if negative, is
the number of states relative to the top of the save stack.  For
example, C{stackid == -1} is the most recently saved state.

B{Note:} If the retrieved state is not at the top of the stack, any
saved states above it are thrown away.

B{Note:} Currently unsupported in OpenOffice -- it apparently uses the
bounding rectangle of the path as the clip area, not the path itself.

@param stackid: stack id number from L{SaveDC} or negative number for relative stack location
@type stackid: int
@return: nonzero for success
@rtype: int

        """
        return self._append(emr.RESTOREDC(-1))

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
        return self._append(emr.SETTEXTALIGN(alignment))

    def SetTextColor(self,color):
        """

Set the text foreground color.
@param color: text foreground L{color<RGB>}.
@return: previous text foreground L{color<RGB>}.
@rtype: int
@type color: int

        """
        e=emr.SETTEXTCOLOR(_normalizeColor(color))
        if not self._append(e):
            return 0
        return 1

    def CreateFont(self,height,width=0,escapement=0,orientation=0,weight=const.FW_NORMAL,italic=0,underline=0,strike_out=0,charset=const.ANSI_CHARSET,out_precision=const.OUT_DEFAULT_PRECIS,clip_precision=const.CLIP_DEFAULT_PRECIS,quality=const.DEFAULT_QUALITY,pitch_family=const.DEFAULT_PITCH|const.FF_DONTCARE,name='Times New Roman'):
        """

Create a new font object. Presumably, when rendering the EMF the
system tries to find a reasonable approximation to all the requested
attributes.

@param height: specified one of two ways:
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
        return self._appendHandle(emr.EXTCREATEFONTINDIRECTW(
            height,width,escapement,orientation,weight,italic,underline,strike_out,charset,out_precision,clip_precision,quality,pitch_family,name))

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

        e = emr.EXTTEXTOUT_auto(x, y, text)

        if not self._append(e):
            return 0
        return 1

    def BitmapOut(self,dest_left,dest_top,dest_width,dest_height,
                  src_left,src_top,src_width,src_height,
                  bmp, rop=const.ROP_SRCCOPY):

        """

Draw a bitmap image on the output, given by the destination rectangle,
taking the data from the source rectangle. Data need to be in BMP format.
Currently assumes RGB colours.

@param dest_left: left x position of destination rectangle
@param dest_top: top y position of destination rectangle
@param dest_width: width of destination rectangle
@param dest_height: height of destination rectangle
@param src_left: left x position of source rectangle
@param src_top: top y position of source rectangle
@param src_width: width of source rectangle
@param src_height: height of source rectangle
@param bmp: bytes string containing BMP data
@param rop: operation to apply when drawing.
        """

        dib = bmp[0xe:]
        hdrsize, = struct.unpack('<i', bmp[0xe:0x12])
        dataindex, = struct.unpack('<i', bmp[0xa:0xe])
        datasize, = struct.unpack('<i', bmp[0x22:0x26])

        epix = emr.STRETCHDIBITS()
        epix.rclBounds_left = dest_left
        epix.rclBounds_top = dest_top
        epix.rclBounds_right = dest_left + dest_width
        epix.rclBounds_bottom = dest_top + dest_height
        epix.xDest = dest_left
        epix.yDest = dest_top
        epix.cxDest = dest_width
        epix.cyDest = dest_height
        epix.xSrc = src_left
        epix.ySrc = src_top
        epix.cxSrc = src_width
        epix.cySrc = src_height

        epix.dwRop = rop
        offset = epix.format.minstructsize + 8
        epix.offBmiSrc = offset
        epix.cbBmiSrc = hdrsize
        epix.offBitsSrc = offset + dataindex - 0xe
        epix.cbBitsSrc = datasize
        epix.iUsageSrc = 0x0 # DIB_RGB_COLORS

        epix.unhandleddata = dib

        e = self._append(epix)
        if not e:
            return 0
        return 1
