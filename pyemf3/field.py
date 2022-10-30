import struct
from io import StringIO, BytesIO

def _round4(num):
    """Round to the nearest multiple of 4 greater than or equal to the
    given number.  EMF records are required to be aligned to 4 byte
    boundaries."""
    return ((num+3)//4)*4

##### - Field, Record, and related classes: a way to represent data
##### more advanced than using just import struct

# A structrecord class for EMF strings
class Field:
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



# Factory for a bunch of flyweight Struct objects
fmtfactory={}
def FormatFactory(fmt):
    if fmt in fmtfactory:
        return fmtfactory[fmt]
    fmtobj=StructFormat(fmt)
    fmtfactory[fmt]=fmtobj
    return fmtobj


class RecordFormat:
    default_endian="<"

    def __init__(self,typedef):
        self.typedef=typedef
        self.minstructsize=0 # minimum structure size (variable entries not counted)

        self.endian=self.default_endian
        self.fmtmap={} # map of name to typecode object
        self.default={}

        self.names=[] # order of names in record

        self.debug=0

        self.fmt=''
        self.setFormat(typedef)

    def getDefaults(self):
        values={}
        for name in self.names:
            fmt=self.fmtmap[name]
            values[name]=self.default[name]
        return values

    def setFormat(self,typedef,default=None):
        if self.debug: print("typedef=%s" % str(typedef))
        if isinstance(typedef,list) or isinstance(typedef,tuple):
            for item in typedef:
                if len(item)==3:
                    typecode,name,default=item
                else:
                    typecode,name=item
                self.appendFormat(typecode,name,default)
        elif typedef:
            raise AttributeError("format must be a list")
        if self.debug: print("current struct=%s size=%d\n  names=%s" % (self.fmt,self.minstructsize,self.names))

    def appendFormat(self,typecode,name,defaultvalue):
        if isinstance(typecode,str):
            if typecode[0] not in "<>@!=":
                typecode=self.endian+typecode
            self.fmt+=typecode
            fmtobj=FormatFactory(typecode)
            self.fmtmap[name]=fmtobj
            self.default[name]=defaultvalue
        elif isinstance(typecode,Field):
            self.fmt+='{'+typecode.__class__.__name__+'}'
            if defaultvalue is not None:
                typecode.setDefault(defaultvalue)
            self.fmtmap[name]=typecode
            self.default[name]=self.fmtmap[name].getDefault()
        else:
            self.fmt+='{'+typecode.__class__.__name__+'}'
            self.fmtmap[name]=typecode(defaultvalue)
            self.default[name]=self.fmtmap[name].getDefault()
        self.minstructsize+=self.fmtmap[name].getNumBytes()
        self.names.append(name)

    def calcNumBytes(self,obj):
        size=0
        for name in self.names:
            fmt=self.fmtmap[name]
            nbytes=fmt.calcNumBytes(obj,name)
            if self.debug: print("calcNumBytes: %s=%d" % (name,nbytes))
            size+=nbytes
        return size

    def unpack(self,data,obj,initptr=0):
        ptr=initptr
        obj.values={}
        if self.minstructsize+ptr>0:
            if self.minstructsize+ptr>len(data):
                # we have a problem.  More stuff to unparse than
                # we have data.  Hmmm.  Fill with binary zeros
                # till I think of a better idea.
                data+="\0"*(self.minstructsize+ptr-len(data))
            for name in self.names:
                fmt=self.fmtmap[name]
                (value,size)=fmt.unpack(obj,name,data,ptr)
                #if fmt.fmt=="<i": value=0
                #if self.debug: print "name=%s fmt=%s value=%s" % (name,fmt.fmt,str(value))
                obj.values[name]=value
                ptr+=size
        return ptr

    def pack(self,values,obj,alreadypacked=0):
        fh=BytesIO()
        size=0
        output={}

        # First, create all the output bytes
        for name in self.names:
            fmt=self.fmtmap[name]
            try:
                output[name]=fmt.pack(obj,name,values[name])
            except:
                print("Exception while trying to pack %s for object:" % name)
                print(obj)
                raise

            # check if the offset to this parameter needs to be
            # adjusted.  This is assuming that the offset occurs
            # BEFORE the parameter, which isn't a bad assumption.
            refname=fmt.hasOffsetReference()
            #print output[name]
            if refname and output[name]:
                if self.debug: print("pack: %s has offset %s, was=%d now=%d" % (name,refname,values[refname],size+alreadypacked))
                values[refname]=size+alreadypacked
                output[refname]=self.fmtmap[refname].pack(obj,refname,values[refname])

            # also need to check if a dependent length needs to be updated
            refname=fmt.hasNumReference()
            #if self.debug: print output[name]
            if refname and output[name]:
                newnum=fmt.calcNum(obj,name)
                if self.debug: print("pack: %s has num %s, was=%d now=%d" % (name,refname,values[refname],newnum))
                values[refname]=newnum
                output[refname]=self.fmtmap[refname].pack(obj,refname,values[refname])

            size+=len(output[name])

        # Finally, write all the output bytes to the filehandle
        for name in self.names:
            fh.write(output[name])
        return fh.getvalue()

    def getString(self,obj):
        txt=StringIO()

        for name in self.names:
            fmt=self.fmtmap[name]
            val=fmt.getString(name,obj.values[name])
            try:
                txt.write("\t%-20s: %s\n" % (name,val))
            except UnicodeEncodeError:
                txt.write("\t%-20s: <<<BAD UNICODE STRING>>> %s\n" % (name,repr(val)))
        return txt.getvalue()


class Record:
    """baseclass for binary records"""

    format=None
    typedef=()

    def __init__(self):
        # if we've never seen this class before, create a new format.
        # Note that subclasses of classes that we have already seen
        # pick up any undefined class attributes from their
        # superclasses, so we have to check if this is a subclass with
        # a different typedef
        if self.__class__.format==None or self.__class__.typedef != self.format.typedef:
            # if self.debug: print "creating format for %d" % id
            self.__class__.format=RecordFormat(self.__class__.typedef)

        # list of values parsed from the input stream
        self.values=self.__class__.format.getDefaults()

    def __getattr__(self,name):
        """Return EMR attribute if the name exists in the typedef list
        of the object.  This is only called when the standard
        attribute lookup fails on this object, so we don't have to
        handle the case where name is an actual attribute of self."""
        f=Record.__getattribute__(self,'format')
        try:
            if name in f.names:
                v=Record.__getattribute__(self,'values')
                return v[name]
        except IndexError:
            raise IndexError("name=%s index=%d values=%s" % (name,index,str(v)))
        raise AttributeError("%s not defined in EMR object" % name)

    def __setattr__(self,name,value):
        """Set a value in the object, propagating through to
        self.values[] if the name is in the typedef list."""
        f=Record.__getattribute__(self,'format')
        try:
            if f and name in f.names:
                v=Record.__getattribute__(self,'values')
                v[name]=value
            else:
                # it's not an automatically serializable item, so store it.
                self.__dict__[name]=value
        except IndexError:
            raise IndexError("name=%s index=%d values=%s" % (name,index,str(v)))




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

        if self.size == 2:
            txt = txt.decode('utf-16le')
        else:
            txt = txt.decode('ascii')

        if self.debug:
            print("str: '%s'" % str(txt))
        return (txt,size)

    def pack(self, obj, name, value):
        txt = value
        if self.size == 2:
            txt = txt.encode('utf-16le')
        else:
            txt = txt.encode('ascii')

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
            default = ''
        self.default=default
