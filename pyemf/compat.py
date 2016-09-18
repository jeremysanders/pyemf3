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

import sys

# python 2/3 compatibility helpers
is_py3 = sys.version_info[0] == 3
if is_py3:
    from io import BytesIO, StringIO
    cunicode = str
else:
    from cStringIO import StringIO
    BytesIO = StringIO
    cunicode = unicode
