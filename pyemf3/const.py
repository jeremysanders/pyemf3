# Reference: libemf.h
# and also wine: http://cvs.winehq.org/cvsweb/wine/include/wingdi.h

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

FS_LATIN1              = 0x00000001
FS_LATIN2              = 0x00000002
FS_CYRILLIC            = 0x00000004
FS_GREEK               = 0x00000008
FS_TURKISH             = 0x00000010
FS_HEBREW              = 0x00000020
FS_ARABIC              = 0x00000040
FS_BALTIC              = 0x00000080
FS_VIETNAMESE          = 0x00000100
FS_THAI                = 0x00010000
FS_JISJAPAN            = 0x00020000
FS_CHINESESIMP         = 0x00040000
FS_WANSUNG             = 0x00080000
FS_CHINESETRAD         = 0x00100000
FS_JOHAB               = 0x00200000
FS_SYMBOL              = 0x80000000

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

# Clipping paths
RGN_ERROR         = 0
RGN_AND           = 1
RGN_OR            = 2
RGN_XOR           = 3
RGN_DIFF          = 4
RGN_COPY          = 5
RGN_MIN           = RGN_AND
RGN_MAX           = RGN_COPY

# Color management
ICM_OFF   = 1
ICM_ON    = 2
ICM_QUERY = 3
ICM_MIN   = 1
ICM_MAX   = 3

# World coordinate system transformation
MWT_IDENTITY      = 1
MWT_LEFTMULTIPLY  = 2
MWT_RIGHTMULTIPLY = 3
