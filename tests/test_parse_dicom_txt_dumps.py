# -*- coding: UTF-8 -*-
"""Unit tests to extract DICOM tags."""
import unittest
import os
import pathlib
from dicom_parser import parse_dicom_txt_dumps as pt
from dicom_parser.pylib import dicom_tools as dt

BASE_DIR, SCRIPT_NAME = os.path.split(os.path.abspath(__file__))
TWO_PARENT_PATH = os.sep.join(pathlib.Path(BASE_DIR).parts[:-2])
PARENT_PATH, CURR_DIR = os.path.split(BASE_DIR)


class TestDicomParser(unittest.TestCase):
    """Test case class for parse_dicom_tags.py"""

    def setUp(self):
        self.valid_dicoms = pathlib.Path(PARENT_PATH, 'data',
                                         'input', 'DICOM')
        self.valid_dumps = pathlib.Path(PARENT_PATH, 'data',
                                        'input', 'tag_dumps')
        self.valid_fuji = pathlib.Path(PARENT_PATH, 'data',
                                       'input', 'tag_dumps',
                                       'fuji_dicom_dump.txt')
        self.valid_dcmtk = pathlib.Path(PARENT_PATH, 'data',
                                        'input', 'tag_dumps',
                                        'dcmtk_dump_src.txt')
        self.valid_ascii = pathlib.Path(PARENT_PATH, 'data',
                                        'input', 'tag_dumps',
                                        'random_ascii.txt')
        self.invalid_path = pathlib.Path(PARENT_PATH, 'does_not_exist')
        self.valid_ext = ['.txt', '.dcm']
        self.out_path = pathlib.Path(BASE_DIR, '~unittest_output')
        if not self.out_path.exists():
            self.out_path.mkdir(parents=True, exist_ok=True)
            print(f"\nsetUp: {self.out_path}\n")

    def test_get_dump_type(self):
        """Verify input files are of three different types"""
        type_dict = pt.get_dump_type(self.valid_fuji)
        self.assertTrue(type_dict['is_fuji'])
        type_dict = pt.get_dump_type(self.valid_dcmtk)
        self.assertTrue(type_dict['is_dcmtk'])
        type_dict = pt.get_dump_type(self.valid_ascii)
        self.assertTrue(type_dict['is_other'])
        type_dict = pt.get_dump_type(self.invalid_path)
        self.assertTrue(type_dict['is_other'])

    def test_get_tag_line_number(self):
        """TO DO."""
        self.assertTrue(True)

    def test_get_tag_indices(self):
        """TO DO."""
        self.assertTrue(True)

    def test_get_txt_dump_paths(self):
        """TO DO."""
        self.assertTrue(True)

    def test_parse_fuji_tag_dump(self):
        """TO DO."""
        self.assertTrue(True)

    def test_parse_dcmtk_tag_dump(self):
        """TO DO."""
        self.assertTrue(True)

    def test_parse_txt_tag_dumps(self):
        """TO DO."""
        self.assertTrue(True)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
