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
from utils import RGB

class _DC:
    """Device Context state machine.  This is used to simulate the
    state of the GDI buffer so that some user commands can return
    information.  In a real GDI implementation, there'd be lots of
    error checking done, but here we can't do a whole bunch because
    we're outputting to a metafile.  So, in general, we assume
    success.

    Here's Microsoft's explanation of units:
    https://msdn.microsoft.com/en-us/library/dd145224.aspx

    Window <=> Logical units <=> page space or user addressable
    integer pixel units.

    Viewport <=> Physical units <=> device units and are measured in actual
    dimensions, like .01 mm units.

    There are four coordinate spaces used by GDI: world, page, device,
    and physical device.  World and page are the same, unless a world
    transform is used.  These are addressed by integer pixels.  Device
    coordinates are referenced by physical dimensions corresponding to
    the mapping mode currently used.

    """

    def __init__(self,width='6.0',height='4.0',density='72',units='in'):
        self.x=0
        self.y=0

        # list of objects that can be referenced by their index
        # number, called "handle"
        self.objects=[]
        self.objects.append(None) # handle 0 is reserved

        # Maintain a stack that contains list of empty slots in object
        # list resulting from deletes
        self.objectholes=[]

        # Reference device size in logical units (pixels)
        self.ref_pixelwidth=1024
        self.ref_pixelheight=768

        # Reference device size in mm
        self.ref_width=320
        self.ref_height=240

        # physical dimensions are in .01 mm units
        self.width=0
        self.height=0
        if units=='mm':
            self.setPhysicalSize([[0,0],[int(width*100),int(height*100)]])
        else:
            self.setPhysicalSize([[0,0],[int(width*2540),int(height*2540)]])

        # addressable pixel sizes
        self.pixelwidth=0
        self.pixelheight=0
        self.setPixelSize([[0,0],[int(width*density),int(height*density)]])

        #self.text_alignment = TA_BASELINE;
        self.text_color = RGB(0,0,0);

        #self.bk_mode = OPAQUE;
        #self.polyfill_mode = ALTERNATE;
        #self.map_mode = MM_TEXT;

        # Viewport origin.  A pixel drawn at (x,y) after the viewport
        # origin has been set to (xv,yv) will be displayed at
        # (x+xv,y+yv).
        self.viewport_x=0
        self.viewport_y=0

        # Viewport extents.  Should density be replaced by
        # self.ref_pixelwidth/self.ref_width?
        self.viewport_ext_x=self.width/100*density
        self.viewport_ext_y=self.height/100*density

        # Window origin.  A pixel drawn at (x,y) after the window
        # origin has been set to (xw,yw) will be displayed at
        # (x-xw,y-yw).

        # If both window and viewport origins are set, a pixel drawn
        # at (x,y) will be displayed at (x-xw+xv,y-yw+yv)
        self.window_x=0
        self.window_y=0

        # Window extents
        self.window_ext_x=self.pixelwidth
        self.window_ext_y=self.pixelheight



    def getBounds(self,header):
        """Extract the dimensions from an _EMR._HEADER record."""

        self.setPhysicalSize(header.rclFrame)
        if header.szlMicrometers[0]>0:
            self.ref_width=header.szlMicrometers[0]/10
            self.ref_height=header.szlMicrometers[1]/10
        else:
            self.ref_width=header.szlMillimeters[0]*100
            self.ref_height=header.szlMillimeters[1]*100

        self.setPixelSize(header.rclBounds)
        self.ref_pixelwidth=header.szlDevice[0]
        self.ref_pixelheight=header.szlDevice[1]

    def setPhysicalSize(self,points):
        """Set the physical (i.e. stuff you could measure with a
        meterstick) dimensions."""
        left=points[0][0]
        top=points[0][1]
        right=points[1][0]
        bottom=points[1][1]
        self.width=right-left
        self.height=bottom-top
        self.frame_left=left
        self.frame_top=top
        self.frame_right=right
        self.frame_bottom=bottom

    def setPixelSize(self,points):
        """Set the pixel-addressable dimensions."""
        left=points[0][0]
        top=points[0][1]
        right=points[1][0]
        bottom=points[1][1]
        self.pixelwidth=right-left
        self.pixelheight=bottom-top
        self.bounds_left=left
        self.bounds_top=top
        self.bounds_right=right
        self.bounds_bottom=bottom


    def addObject(self,emr,handle=-1):
        """Add an object to the handle list, so it can be retrieved
        later or deleted."""
        count=len(self.objects)
        if handle>0:
            # print "Adding handle %s (%s)" % (handle,emr.__class__.__name__.lstrip('_'))
            if handle>=count:
                self.objects+=[None]*(handle-count+1)
            self.objects[handle]=emr
        elif self.objectholes:
            handle=self.objectholes.pop()
            self.objects[handle]=emr
        else:
            handle=count
            self.objects.append(emr)
        return handle

    def removeObject(self,handle):
        """Remove an object by its handle.  Handles can be reused, and
        are reused from lowest available handle number."""
        if handle<1 or handle>=len(self.objects):
            raise IndexError("Invalid handle")
        # print "removing handle %d (%s)" % (handle,self.objects[handle].__class__.__name__.lstrip('_'))
        self.objects[handle]=None
        found=False

        # insert handle in objectholes list, but keep object holes
        # list in sorted order
        i=0
        while i<len(self.objectholes):
            if handle<self.objectholes[i]:
                self.objectholes.insert(i,handle)
                break
            i+=1
        else:
            self.objectholes.append(handle)
        # print self.objectholes

    def popObject(self):
        """Remove last object.  Used mainly in case of error."""
        self.objects.pop()

