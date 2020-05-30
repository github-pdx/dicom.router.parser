# -*- coding: UTF-8 -*-
"""Unit tests to extract DICOM tags."""
import unittest
import os
import pathlib
from sys import platform
from dicom_parser import parse_dicom_tags

BASE_DIR, SCRIPT_NAME = os.path.split(os.path.abspath(__file__))
TWO_PARENT_PATH = os.sep.join(pathlib.Path(BASE_DIR).parts[:-2])
PARENT_PATH, CURR_DIR = os.path.split(BASE_DIR)


class TestDicomParser(unittest.TestCase):
    """Test case class for parse_dicom_tags.py"""

    def setUp(self):
        self.valid_dir = pathlib.Path(PARENT_PATH, 'data', 'input', 'DICOM')
        self.valid_file = pathlib.Path(BASE_DIR, SCRIPT_NAME)
        self.no_ext_file = pathlib.Path(PARENT_PATH, 'LICENSE')
        self.valid_parent = pathlib.Path(PARENT_PATH)
        self.invalid_path = pathlib.Path(PARENT_PATH, 'does_not_exist')
        self.valid_ext = ['.txt', '.dcm']
        self.is_win = platform.startswith('win')
        self.out_path = os.path.join(BASE_DIR, '~unittest_output')
        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)
            print(f"\nsetUp: {self.out_path}\n")

    def test_get_header_column_widths(self):
        """TO DO."""

        self.assertTrue(True)

    def test_export_to_excel(self):
        """TO DO."""
        self.assertTrue(True)
            
    def test_is_fuji_tag_dump(self):
        """TO DO."""
        self.assertTrue(True)

    def test_get_tag_line_number(self):
        """TO DO."""
        self.assertTrue(True)

    def test_get_tag_indices(self):
        """TO DO."""
        self.assertTrue(True)

    def test_parse_dicom_tag_dump(self):
        """TO DO."""
        self.assertTrue(True)

    def test_get_cmd_args(self):
        """TO DO."""
        self.assertTrue(True)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
