# -*- coding: UTF-8 -*-
"""Unit tests for DICOM tools."""
import unittest
import os
import re
import pathlib
from collections import OrderedDict
from pydicom.tag import Tag
import dicom_parser.parse_dicom_tags as pt
from dicom_parser.pylib import dicom_tools as dt

BASE_DIR, SCRIPT_NAME = os.path.split(os.path.abspath(__file__))
PARENT_PATH, CURR_DIR = os.path.split(BASE_DIR)


class TestDicomTools(unittest.TestCase):
    """Test case class for dicom_tools.py"""

    def setUp(self):
        self.valid_dicom = pathlib.Path(PARENT_PATH, 'data',
                                        'input', 'DICOM')
        self.valid_txt = pathlib.Path(PARENT_PATH, 'data',
                                      'input', 'tag_dumps')
        self.valid_dcmtk = pathlib.Path(PARENT_PATH, 'data', 'input',
                                        'tag_dumps', 'dcmtk_dump_src.txt')
        self.valid_fuji = pathlib.Path(PARENT_PATH, 'data', 'input',
                                       'tag_dumps', 'fuji_dicom_dump.txt')
        self.out_path = pathlib.Path(BASE_DIR, '~unittest_output')
        if not self.out_path.exists():
            self.out_path.mkdir(parents=True, exist_ok=True)
            print(f"\nsetUp: {self.out_path}\n")

    def test_get_header_column_widths(self):
        stat_list = pt.parse_dicom_tag_dumps(self.valid_dicom)
        hdr_col_width_dict = dt.get_header_column_widths(stat_list)
        self.assertIsInstance(hdr_col_width_dict, dict)
        for hdr in dt.HEADERS:
            self.assertTrue(hdr in hdr_col_width_dict.keys())

    def test_export_to_excel(self):
        all_dicom_list = pt.parse_dicom_tag_dumps(self.valid_dicom)
        status = dt.export_to_excel(self.out_path,
                                    "~dicom_dicom_tags.xlsx",
                                    all_dicom_list)

        self.assertTrue("SUCCESS" in status)
        output_path = pathlib.Path(BASE_DIR, '~unittest_output',
                                   "~dicom_dicom_tags.xlsx")
        self.assertTrue(output_path.exists())

    def test_parse_txt_tag_dumps(self):
        all_txt_list = pt.parse_dicom_tag_dumps(self.valid_txt)
        self.assertIsInstance(all_txt_list, list)
        self.assertGreater(len(all_txt_list), 0)

    def test_build_pydicom_tag_dict(self):
        pydicom_dict = OrderedDict(
            [("filename", 'default.txt'),
             ("accessionNumber", Tag(0x0008, 0x0050)),
             ("modality", Tag(0x0008, 0x0060)),
             ("sourceApplicationEntityTitle", Tag(0x0002, 0x0016)),
             ("stationName", Tag(0x0008, 0x1010)),
             ("institutionName", Tag(0x0008, 0x0080)),
             ("manufacturer", Tag(0x0008, 0x0070)),
             ("manufacturerModelName", Tag(0x0008, 0x1090)),
             ("transferSyntaxUid", Tag(0x0002, 0x0010))])
        dicom_tag_dict = dt.build_pydicom_tag_dict()
        # match: (0x0008,0x0050)
        for key, tag in dicom_tag_dict.items():
            if 'filename' not in key:
                self.assertIsInstance(key, str)
                self.assertIsInstance(tag, int)
                self.assertEqual(pydicom_dict[key], tag)

    def test_build_fuji_tag_dict(self):
        fuji_dict = OrderedDict(
            [("filename", 'default.txt'),
             ("accessionNumber", '0008 0050'),
             ("modality", '0008 0060'),
             ("sourceApplicationEntityTitle", '0002 0016'),
             ("stationName", '0008 1010'),
             ("institutionName", '0008 0080'),
             ("manufacturer", '0008 0070'),
             ("manufacturerModelName", '0008 1090'),
             ("transferSyntaxUid", '0002 0010')])
        fuji_tag_dict = dt.build_fuji_tag_dict()
        # match: 0008 0050
        for key, tag in fuji_tag_dict.items():
            if 'filename' not in key:
                match = re.search("^[0-9]{4} [0-9]{4}$", tag)
                self.assertIsNotNone(match)
                self.assertIsInstance(tag, str)
                self.assertEqual(tag[match.start():match.end()], tag)
                self.assertEqual(fuji_dict[key], tag)

    def test_build_dcmtk_tag_dict(self):
        dcmtk_dict = OrderedDict(
            [("filename", 'default.txt'),
             ("accessionNumber", '(0008,0050)'),
             ("modality", '(0008,0060)'),
             ("sourceApplicationEntityTitle", '(0002,0016)'),
             ("stationName", '(0008,1010)'),
             ("institutionName", '(0008,0080)'),
             ("manufacturer", '(0008,0070)'),
             ("manufacturerModelName", '(0008,1090)'),
             ("transferSyntaxUid", '(0002,0010)')])
        dcmtk_tag_dict = dt.build_dcmtk_tag_dict()
        # match: (0008,0050)
        for key, tag in dcmtk_tag_dict.items():
            if 'filename' not in key:
                match = re.search("^(\\([0-9]{4},)([0-9]{4}\\))$", tag)
                self.assertIsNotNone(match)
                self.assertIsInstance(tag, str)
                self.assertEqual(tag[match.start():match.end()], tag)
                self.assertEqual(dcmtk_dict[key], tag)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
