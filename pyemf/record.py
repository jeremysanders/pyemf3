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

import struct

from .field import Field, StructFormat
from .compat import StringIO, BytesIO

# Factory for a bunch of flyweight Struct objects
fmtfactory = {}


def FormatFactory(fmt):
    if fmt in fmtfactory:
        return fmtfactory[fmt]
    fmtobj = StructFormat(fmt)
    fmtfactory[fmt] = fmtobj
    return fmtobj


class RecordFormat:
    default_endian = "<"

    def __init__(self, typedef):
        self.typedef = typedef

        # minimum structure size (variable entries not counted)
        self.minstructsize = 0

        self.endian = self.default_endian
        # map of name to typecode object
        self.fmtmap = {}
        self.default = {}

        # order of names in record
        self.names = []

        self.debug = 0

        self.fmt = ''
        self.setFormat(typedef)

    def getDefaults(self):
        values = {}
        for name in self.names:
            fmt = self.fmtmap[name]
            values[name] = self.default[name]
        return values

    def setFormat(self, typedef, default=None):
        if self.debug:
            print("typedef=%s" % str(typedef))
        if isinstance(typedef, list) or isinstance(typedef, tuple):
            for item in typedef:
                if len(item) == 3:
                    typecode, name, default = item
                else:
                    typecode, name = item
                self.appendFormat(typecode, name, default)
        elif typedef:
            raise AttributeError("format must be a list")
        if self.debug:
            print(
                "current struct=%s size=%d\n  names=%s" % (
                    self.fmt, self.minstructsize, self.names))

    def appendFormat(self, typecode, name, defaultvalue):

        if isinstance(typecode, str):
            if typecode[0] not in "<>@!=":
                typecode = self.endian + typecode
            self.fmt += typecode
            fmtobj = FormatFactory(typecode)
            self.fmtmap[name] = fmtobj
            self.default[name] = defaultvalue

        elif isinstance(typecode, Field):
            self.fmt += '{' + typecode.__class__.__name__ + '}'
            if defaultvalue is not None:
                typecode.setDefault(defaultvalue)
            self.fmtmap[name] = typecode
            self.default[name] = self.fmtmap[name].getDefault()

        else:
            self.fmt += '{' + typecode.__class__.__name__ + '}'
            self.fmtmap[name] = typecode(defaultvalue)
            self.default[name] = self.fmtmap[name].getDefault()
        self.minstructsize += self.fmtmap[name].getNumBytes()
        self.names.append(name)

    def calcNumBytes(self, obj):
        size = 0
        for name in self.names:
            fmt = self.fmtmap[name]
            bytes = fmt.calcNumBytes(obj, name)
            if self.debug:
                print("calcNumBytes: %s=%d" % (name, bytes))
            size += bytes
        return size

    def unpack(self, data, obj, initptr=0):
        ptr = initptr
        obj.values = {}
        if self.minstructsize + ptr > 0:
            if self.minstructsize + ptr > len(data):
                # we have a problem.  More stuff to unparse than
                # we have data.  Hmmm.  Fill with binary zeros
                # till I think of a better idea.
                data += b"\0" * (self.minstructsize + ptr - len(data))
            for name in self.names:
                fmt = self.fmtmap[name]
                (value, size) = fmt.unpack(obj, name, data, ptr)
                # if fmt.fmt=="<i": value=0
                # if self.debug: print "name=%s fmt=%s value=%s" %
                # (name,fmt.fmt,str(value))
                obj.values[name] = value
                ptr += size
        return ptr

    def pack(self, values, obj, alreadypacked=0):
        fh = BytesIO()
        size = 0
        output = {}

        # First, create all the output bytes
        for name in self.names:
            fmt = self.fmtmap[name]
            try:
                output[name] = fmt.pack(obj, name, values[name])
            except:
                print("Exception while trying to pack %s for object:" % name)
                print(obj)
                raise

            # check if the offset to this parameter needs to be
            # adjusted.  This is assuming that the offset occurs
            # BEFORE the parameter, which isn't a bad assumption.
            refname = fmt.hasOffsetReference()
            # print output[name]
            if refname and output[name]:
                if self.debug:
                    print("pack: %s has offset %s, was=%d now=%d" %
                          (name, refname, values[refname], size + alreadypacked))
                values[refname] = size + alreadypacked
                output[refname] = self.fmtmap[refname].pack(
                    obj, refname, values[refname])

            # also need to check if a dependent length needs to be updated
            refname = fmt.hasNumReference()
            # if self.debug: print output[name]
            if refname and output[name]:
                newnum = fmt.calcNum(obj, name)
                if self.debug:
                    print("pack: %s has num %s, was=%d now=%d" %
                          (name, refname, values[refname], newnum))
                values[refname] = newnum
                output[refname] = self.fmtmap[refname].pack(
                    obj, refname, values[refname])

            size += len(output[name])

        # Finally, write all the output bytes to the filehandle
        for name in self.names:
            fh.write(output[name])
        return fh.getvalue()

    def getString(self, obj):
        txt = StringIO()

        for name in self.names:
            fmt = self.fmtmap[name]
            val = fmt.getString(name, obj.values[name])
            try:
                txt.write("\t%-20s: %s\n" % (name, val))
            except UnicodeEncodeError:
                txt.write("\t%-20s: <<<BAD UNICODE STRING>>> %s\n" %
                          (name, repr(val)))
        return txt.getvalue()


class Record(object):

    """baseclass for binary records"""

    format = None
    typedef = ()

    def __init__(self):
        # if we've never seen this class before, create a new format.
        # Note that subclasses of classes that we have already seen
        # pick up any undefined class attributes from their
        # superclasses, so we have to check if this is a subclass with
        # a different typedef
        if self.__class__.format == None or self.__class__.typedef != self.format.typedef:
            # if self.debug: print "creating format for %d" % id
            self.__class__.format = RecordFormat(self.__class__.typedef)

        # list of values parsed from the input stream
        self.values = self.__class__.format.getDefaults()

    def __getattr__(self, name):
        """Return EMR attribute if the name exists in the typedef list
        of the object.  This is only called when the standard
        attribute lookup fails on this object, so we don't have to
        handle the case where name is an actual attribute of self."""
        f = Record.__getattribute__(self, 'format')
        try:
            if name in f.names:
                v = Record.__getattribute__(self, 'values')
                return v[name]
        except IndexError:
            raise IndexError(
                "name=%s index=%d values=%s" % (name, index, str(v)))
        raise AttributeError("%s not defined in EMR object" % name)

    def __setattr__(self, name, value):
        """Set a value in the object, propagating through to
        self.values[] if the name is in the typedef list."""
        f = Record.__getattribute__(self, 'format')
        try:
            if f and name in f.names:
                v = Record.__getattribute__(self, 'values')
                v[name] = value
            else:
                # it's not an automatically serializable item, so store it.
                self.__dict__[name] = value
        except IndexError:
            raise IndexError(
                "name=%s index=%d values=%s" % (name, index, str(v)))


class _EMR_UNKNOWN(Record):
    # extend from new-style class, or __getattr__ doesn't work

    """baseclass for EMR objects"""
    emr_id = 0

    twobytepadding = b'\0' * 2

    def __init__(self):
        Record.__init__(self)
        self.iType = self.__class__.emr_id
        self.nSize = 0

        self.verbose = False

        self.datasize = 0
        self.data = None
        self.unhandleddata = None

        # error code.  Currently just used as a boolean
        self.error = 0

    def hasHandle(self):
        """Return true if this object has a handle that needs to be
        saved in the object array for later recall by SelectObject."""
        return False

    def setBounds(self, bounds):
        """Set bounds of object.  Depends on naming convention always
        defining the bounding rectangle as
        rclBounds_[left|top|right|bottom]."""
        self.rclBounds = [
            [bounds[0][0], bounds[0][1]], [bounds[1][0], bounds[1][1]]]

    def getBounds(self):
        """Return bounds of object, or None if not applicable."""
        if 'rclBounds' in self.values:
            return self.rclBounds
        return None

    def unserialize(self, fh, already_read, itype=-1, nsize=-1):
        """Read data from the file object and, using the format
        structure defined by the subclass, parse the data and store it
        in self.values[] list."""
        prevlen = len(already_read)

        if itype > 0:
            self.iType = itype
            self.nSize = nsize
        else:
            (self.iType, self.nSize) = struct.unpack("<ii", already_read)
        if self.nSize > prevlen:
            self.data = already_read + fh.read(self.nSize - prevlen)
            last = self.format.unpack(self.data, self, prevlen)
            if self.nSize > last:
                self.unserializeExtra(self.data[last:])

    def unserializeExtra(self, data):
        """Hook for subclasses to handle extra data in the record that
        isn't specified by the format statement."""
        self.unhandleddata = data
        pass

    def serialize(self, fh):
        try:
            # print "packing!"
            bytes = self.format.pack(self.values, self, 8)
            # fh.write(struct.pack(self.format.fmt,*self.values))
        except struct.error:
            print("!!!!!Struct error:", end=' ')
            print(self)
            raise
        before = self.nSize
        self.nSize = 8 + len(bytes) + self.sizeExtra()
        if self.verbose and before != self.nSize:
            print("resize: before=%d after=%d" % (before, self.nSize), end=' ')
            print(self)
        if self.nSize % 4 != 0:
            print("size error--must be divisible by 4. before=%d after=%d calcNumBytes=%d extra=%d" %
                  (before, self.nSize, len(bytes), self.sizeExtra()))
            for name in self.format.names:
                fmt = self.format.fmtmap[name]
                size = fmt.calcNumBytes(self, name)
                print("  name=%s size=%s" % (name, size))
            print(self)
            raise TypeError
        fh.write(struct.pack("<ii", self.iType, self.nSize))
        fh.write(bytes)
        self.serializeExtra(fh)

    def serializeExtra(self, fh):
        """This is for special cases, like writing text or lists.  If
        this is not overridden by a subclass method, it will write out
        anything in the self.unhandleddata string."""
        if self.unhandleddata:
            fh.write(self.unhandleddata)

    def resize(self):
        before = self.nSize
        self.nSize = 8 + self.format.calcNumBytes(self) + self.sizeExtra()
        if self.verbose and before != self.nSize:
            print("resize: before=%d after=%d" % (before, self.nSize), end=' ')
            print(self)
        if self.nSize % 4 != 0:
            print("size error--must be divisible by 4. before=%d after=%d calcNumBytes=%d extra=%d" %
                  (before, self.nSize, self.format.calcNumBytes(self), self.sizeExtra()))
            for name in self.format.names:
                fmt = self.format.fmtmap[name]
                size = fmt.calcNumBytes(self, name)
                print("  name=%s size=%s" % (name, size))
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
        details = self.format.getString(self)
        ret = "\n" if details else ""

        return "**%s: iType=%s nSize=%s  struct='%s' size=%d extra=%d\n%s%s" % (
            self.__class__.__name__.lstrip('_'),
            self.iType,
            self.nSize,
            self.format.fmt,
            self.format.minstructsize,
            self.sizeExtra(),
            details,
            ret)
