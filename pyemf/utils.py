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


def RGB(r, g, b):
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

    if isinstance(r, float):
        r = int(255 * r)
    r = max(0, min(255, r))

    if isinstance(g, float):
        g = int(255 * g)
    g = max(0, min(255, g))

    if isinstance(b, float):
        b = int(255 * b)
    b = max(0, min(255, b))

    return (b << 16) | (g << 8) | r


def _normalizeColor(c):
    """
Normalize the input into a packed integer.  If the input is a tuple,
pass it through L{RGB} to generate the color value.

@param c: color
@type c: int or (r,g,b) tuple
@return: packed integer color from L{RGB}
@rtype: int
"""
    if isinstance(c, int):
        return c
    if isinstance(c, tuple) or isinstance(c, list):
        return RGB(*c)
    raise TypeError(
        "Color must be specified as packed integer or 3-tuple (r,g,b)")
