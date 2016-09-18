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

from .compat import BytesIO, cunicode

def _round4(num):
    """Round to the nearest multiple of 4 greater than or equal to the
    given number.  EMF records are required to be aligned to 4 byte
    boundaries."""
    return ((num+3)//4)*4

##### - Field, Record, and related classes: a way to represent data
##### more advanced than using just import struct

# A structrecord class for EMF strings
class Field(object):
    def __init__(self,fmt,size=1,num=1,offset=None):
        # Format string, if applicable
        self.fmt=fmt

        # Size of record, in bytes
        self.size=size

        # Number of records.  Could be an integer OR a text string
        # that will be interpreted as a key in the object.  That key
        # will be referenced at unpack time to determine the number of
        # records
        self.num=num

        # Relative offset to start of record, if supplied
        self.offset=offset

        self.debug=False

    def getNumBytes(self,obj=None):
        size=self.size*self.getNum(obj)
        #if debug: print "size=%d" % size
        return size

    def calcNumBytes(self,obj,name):
        if isinstance(obj.values[name],list) or isinstance(obj.values[name],tuple):
            size=self.size*len(obj.values[name])
            if self.debug: print("  calcNumBytes: size=%d len(obj.values[%s])=%d total=%d" % (self.size,name,len(obj.values[name]),size))
            # also update the linked number, if applicable
        else:
            size=self.size*self.getNum(obj)
        return size

    # Get number of elements of this object (i.e. number of chars in a
    # string, number of items in a list, etc.)
    def getNum(self,obj=None):
        num=0
        if isinstance(self.num,int):
            num=self.num
        elif obj:
            num=getattr(obj,self.num) # find obj."num"
        #if debug: print "getting number for obj=%s, self.num=%s => num=%d" % (obj.__class__.__name__,self.num,num)
        return num

    def hasNumReference(self):
        # If this format uses a reference to get the number, return
        # that reference name
        if isinstance(self.num,str):
            return self.num
        return False

    def calcNum(self,obj,name):
        if isinstance(obj.values[name],list) or isinstance(obj.values[name],tuple):
            num=len(obj.values[name])
            ##if debug: print "calcNumBytes: size=%d num=%d" % (size,len(obj.values[name]))
            # also update the linked number, if applicable
        else:
            num=self.getNum(obj)
        return num

    def getOffset(self,obj):
        if self.offset==None: return None
        offset=0
        if isinstance(self.offset,int):
            offset+=self.offset
        elif obj:
            offset+=getattr(obj,self.offset) # find obj."offset"
        if self.debug: print("getting offset for obj=%s, self.offset=%s => offset=%d" % (obj.__class__.__name__,self.offset,offset))
        return offset

    def hasOffsetReference(self):
        # If this format uses a reference to get the offset, return
        # that reference name
        if (self.offset,str):
            return self.offset
        return False

    def unpack(self,obj,name,data,ptr):
        raise NotImplementedError()

    def pack(self,obj,name,value):
        raise NotImplementedError()

    def getDefault(self):
        return None

    def setDefault(self):
        pass

    def getString(self,name,val):
        return val

class StructFormat(Field):
    def __init__(self,fmt):
        Field.__init__(self,fmt,struct.calcsize(fmt))

    def unpack(self,obj,name,data,ptr):
        value=struct.unpack(self.fmt,data[ptr:ptr+self.size])[0]
        return (value,self.size)

    def pack(self,obj,name,value):
        return struct.pack(self.fmt,value)

    def str_color(self,val):
        return "red=0x%02x green=0x%02x blue=0x%02x" % ((val&0xff),((val&0xff00)>>8),((val&0xff0000)>>16))

    def getString(self,name,val):
        if name.endswith("olor"):
            val=self.str_color(val)
        elif self.fmt.endswith("s"):
            val=val.decode('utf-16le')
        return val

class String(Field):
    def __init__(self,default=None,size=1,num=1,offset=None):
        # Note the two bytes per unicode char
        Field.__init__(self,None,size=size,num=num,offset=offset)
        self.setDefault(default)

    def calcNumBytes(self,obj,name):
        if self.hasNumReference():
            # If this is a dynamic string, calculate the size required
            txt=obj.values[name]
            if self.size==2:
                # it's unicode, so get the number of actual bytes required
                # to store it
                txt=txt.encode('utf-16')
            # EMF requires that strings be stored as multiples of 4 bytes
            return len(txt)
        else:
            # this is a fixed length string, so we know the length already.
            return Field.calcNumBytes(self,obj,name)

    def calcNum(self,obj,name):
        if self.hasNumReference():
            return len(obj.values[name])
        else:
            return Field.calcNumBytes(self,obj,name)

    def unpack(self,obj,name,data,ptr):
        offset=self.getOffset(obj)
        if offset==None:
            pass
        elif offset>0:
            ptr=offset
        else:
            return ('',0)

        size=self.getNumBytes(obj)
        txt=data[ptr:ptr+size]
        if self.size==2:
            txt=txt.decode('utf-16') # Now is a unicode string
        if self.debug:
            try:
                print("str: '%s'" % str(txt))
            except UnicodeEncodeError:
                print("<<<BAD UNICODE STRING>>>: '%s'" % repr(txt))
        return (txt,size)

    def pack(self,obj,name,value):
        txt=value
        if self.size==2:
            txt=txt.encode('utf-16')
        maxlen=self.getNumBytes(obj)
        if len(txt)>maxlen:
            txt=txt[0:maxlen]
        else:
            txt+='\0'*(maxlen-len(txt))
        return txt

    def getDefault(self):
        # FIXME: need to take account of number
        return self.default

    def setDefault(self,default):
        if default is None:
            if self.size==2:
                default=u''
            else:
                default=''
        self.default=default

class CString(String):
    def __init__(self,default=None,num=1,offset=None):
        String.__init__(self,None,size=1,num=num,offset=offset)

    def unpack(self,obj,name,data,ptr):
        (txt,size)=String.unpack(self,obj,name,data,ptr)
        i=0
        while i<size:
            if txt[i]=='\0': break
            i+=1
        return (txt[0:i],i)

class List(Field):
    def __init__(self,default=None,num=1,fmt='i',offset=None):
        Field.__init__(self,fmt,struct.calcsize(fmt),num,offset=offset)
        self.setDefault(default)

    def unpack(self,obj,name,data,ptr):
        values=[]

        offset=self.getOffset(obj)
        if offset==None:
            pass
        elif offset>0:
            ptr=offset
        else:
            return (values,0)

        num=self.getNum(obj)
        while num>0:
            values.append(struct.unpack(self.fmt,data[ptr:ptr+self.size])[0])
            ptr+=self.size
            num-=1
        return (values,self.getNumBytes(obj))

    def pack(self,obj,name,value):
        fh=BytesIO()
        size=0
        for val in value:
            fh.write(struct.pack(self.fmt,val))
        return fh.getvalue()

    def getDefault(self):
        return self.default

    def setDefault(self,default):
        if default is not None:
            default=[0]*self.getNum()
        self.default=default


class Tuples(Field):
    def __init__(self,default=None,rank=2,num=1,fmt='i',offset=None):
        if fmt[0] in "<>@!=":
            fmt=fmt[0]+fmt[1]*rank
        else:
            fmt=fmt*rank
        Field.__init__(self,fmt,struct.calcsize(fmt),num,offset=offset)
        if self.debug: print("Tuples:%s self.size=%d" % (self.__class__.__name__,self.size))
        self.rank=rank
        self.setDefault(default)

    # always create a list of lists
    def unpack(self,obj,name,data,ptr):
        values=[]

        offset=self.getOffset(obj)
        if offset==None:
            pass
        elif offset>0:
            ptr=offset
        else:
            return (values,0)

        num=self.getNum(obj)
        if self.debug: print("unpack: name=%s num=%d ptr=%d datasize=%d" % (name,num,ptr,len(data)))
        while num>0:
            values.append(list(struct.unpack(self.fmt,data[ptr:ptr+self.size])))
            ptr+=self.size
            num-=1
        return (values,self.getNumBytes(obj))

    # assuming a list of lists
    def pack(self,obj,name,value):
        fh=BytesIO()
        size=0
        if self.debug: print("pack: value=%s" % (str(value)))
        for val in value:
            fh.write(struct.pack(self.fmt,*val))
        return fh.getvalue()

    def getDefault(self):
        # FIXME: need to take account of number
        return self.default

    def setDefault(self,default):
        if default is None:
            default=[[0]*self.rank]*self.getNum()
        self.default=default

# Special case of two-tuples
class Points(Tuples):
    def __init__(self,default=None,num=1,fmt='i',offset=None):
        Tuples.__init__(self,rank=2,num=num,fmt=fmt,default=default,offset=offset)


class EMFString(Field):
    def __init__(self,default=None,size=2,num=1,offset=None):
        # Note the two bytes per unicode char
        Field.__init__(self,None,size=size,num=num,offset=offset)
        self.setDefault(default)

    def calcNumBytes(self,obj,name):
        if self.hasNumReference():
            # If this is a dynamic string, calculate the size required
            txt=obj.values[name]
            if self.size==2:
                # it's unicode, so get the number of actual bytes required
                # to store it
                txt=txt.encode('utf-16le')
            # EMF requires that strings be stored as multiples of 4 bytes
            extra=_round4(len(txt))-len(txt)
            return len(txt)+extra
        else:
            # this is a fixed length string, so we know the length already.
            return Field.calcNumBytes(self,obj,name)

    def calcNum(self,obj,name):
        if self.hasNumReference():
            return len(obj.values[name])
        else:
            return Field.calcNumBytes(self,obj,name)

    def unpack(self,obj,name,data,ptr):
        offset=self.getOffset(obj)
        if offset==None:
            pass
        elif offset>0:
            ptr=offset
        else:
            return ('',0)

        size=self.getNumBytes(obj)
        txt=data[ptr:ptr+size]
        size=_round4(len(txt))
        if self.size==2:
            txt=txt.decode('utf-16le') # Now is a unicode string
        if self.debug:
            try:
                print("str: '%s'" % str(txt))
            except UnicodeEncodeError:
                print("<<<BAD UNICODE STRING>>>: '%s'" % repr(txt))
        return (txt,size)

    def pack(self,obj,name,value):
        txt=value
        if isinstance(txt, cunicode):
            txt = txt.encode('utf-16le')
        if self.hasNumReference():
            extra=_round4(len(txt))-len(txt) # must be multiple of 4
            if extra>0:
                txt+=b'\0'*extra
        else:
            maxlen=self.getNumBytes(obj)
            if len(txt)>maxlen:
                txt=txt[0:maxlen]
            else:
                txt+=b'\0'*(maxlen-len(txt))
        return txt

    def getDefault(self):
        # FIXME: need to take account of number
        return self.default

    def setDefault(self,default):
        if default is None:
            if self.size==2:
                default=u''
            else:
                default=''
        self.default=default
