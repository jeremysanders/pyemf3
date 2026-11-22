"""Check EMF byte order, including simulated big-endian struct defaults."""

from contextlib import ExitStack, contextmanager
from io import BytesIO
from pathlib import Path
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pyemf3
from pyemf3 import emf, emr, field


@contextmanager
def big_endian_struct():
    """Emulate native big-endian packing without changing explicit formats."""
    def explicit_format(fmt):
        if fmt[0] in '@=':
            return '>' + fmt[1:]
        if fmt[0] not in '<>!':
            return '>' + fmt
        return fmt

    replacement = SimpleNamespace(
        calcsize=lambda fmt: struct.calcsize(explicit_format(fmt)),
        pack=lambda fmt, *values: struct.pack(explicit_format(fmt), *values),
        unpack=lambda fmt, data: struct.unpack(explicit_format(fmt), data),
        error=struct.error,
    )
    with ExitStack() as stack:
        for module in (field, emr, emf):
            stack.enter_context(patch.object(module, 'struct', replacement))
        yield


class EndiannessTests(unittest.TestCase):
    def test_numeric_fields(self):
        with big_endian_struct():
            for fmt in ('i', 'l'):
                with self.subTest(fmt=fmt):
                    values = [0x01020304, -2]
                    expected = bytes.fromhex('04030201 feffffff')
                    scalar_list = field.List(num=2, fmt=fmt)
                    self.assertEqual(scalar_list.pack(None, '', values), expected)
                    self.assertEqual(scalar_list.unpack(None, '', expected, 0),
                                     (values, len(expected)))

            for fmt, expected in (
                    ('h', bytes.fromhex('0201 feff')),
                    ('i', bytes.fromhex('02010000 feffffff'))):
                with self.subTest(fmt=fmt):
                    values = [[0x0102, -2]]
                    points = field.Points(num=1, fmt=fmt)
                    self.assertEqual(points.pack(None, '', values), expected)
                    self.assertEqual(points.unpack(None, '', expected, 0),
                                     (values, len(expected)))

    def test_custom_pen_dashes(self):
        with big_endian_struct():
            pen = emr.EXTCREATEPEN(
                style=pyemf3.PS_USERSTYLE, styleentries=[0x01020304, 5])
            self.assertEqual(pen.unhandleddata,
                             bytes.fromhex('04030201 05000000'))

    def test_document_bytes(self):
        def document_bytes():
            document = pyemf3.EMF(width=4, height=3, density=300)
            pen = document.CreatePen(
                pyemf3.PS_USERSTYLE | pyemf3.PS_GEOMETRIC, 3,
                (10, 20, 30), styleentries=[7, 3])
            document.SelectObject(pen)
            document.Polyline([(1, 2), (300, 400)])
            document.Polyline([(-40000, 40000), (50000, -50000)])
            document.TextOut(10, 20, 'A\u03a9\u0416')
            document._end()
            output = BytesIO()
            document._serialize(output)
            return output.getvalue()

        expected = document_bytes()
        self.assertIn('A\u03a9\u0416'.encode('utf-16le'), expected)
        with big_endian_struct():
            self.assertEqual(document_bytes(), expected)

    def test_fixture_roundtrips(self):
        fixtures = sorted((Path(__file__).parent / 'orig').glob('*.emf'))
        self.assertTrue(fixtures)
        for fixture in fixtures:
            expected = fixture.read_bytes()
            baseline = pyemf3.EMF()
            baseline.records = []
            baseline._unserialize(BytesIO(expected))
            with big_endian_struct():
                with self.subTest(fixture=fixture.name):
                    document = pyemf3.EMF()
                    document.records = []
                    document._unserialize(BytesIO(expected))
                    self.assertEqual([record.values for record in document.records],
                                     [record.values for record in baseline.records])
                    output = BytesIO()
                    document._serialize(output)
                    self.assertEqual(output.getvalue(), expected)


if __name__ == '__main__':
    unittest.main()
