# -*- coding: UTF-8 -*-
"""Unit tests to extract DICOM tags."""
import unittest
import os
import pathlib
from dicom_parser import parse_dicom_tags as pt

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
        self.valid_ext = ['.txt', '.dcm']
        self.out_path = pathlib.Path(BASE_DIR, '~unittest_output')
        if not self.out_path.exists():
            self.out_path.mkdir(parents=True, exist_ok=True)
            print(f"\nsetUp: {self.out_path}\n")

    def test_get_dicom_dump_paths(self):
        all_dcm_list = pt.get_dicom_dump_paths(self.valid_dicoms)
        self.assertIsInstance(all_dcm_list, list)
        self.assertGreater(len(all_dcm_list), 0)
        all_tag_list = pt.get_dicom_dump_paths(self.valid_dumps)
        self.assertEqual(len(all_tag_list), 0)

    def test_parse_dicom_tag_dumps(self):
        all_dcm_list = pt.get_dicom_dump_paths(self.valid_dicoms)
        for dcm_path in all_dcm_list:
            tag_list = pt.parse_dicom_tag_dumps(dcm_path)
            self.assertIsInstance(tag_list, list)
            self.assertGreater(len(tag_list), 0)

    def test_sanitize_input(self):
        bad_str = "{}[]()<>^#+*?$@&%$!,:;/\\ -."
        expected_str = "-."
        sanitized_str = pt.sanitize_input(bad_str)
        self.assertEqual(expected_str, sanitized_str)

    def test_read_dicom_extract_tags(self):
        dicom_path_list = pt.get_dicom_dump_paths(self.valid_dicoms)
        for file_count, dicom_path in enumerate(dicom_path_list):
            tag_list = pt.read_dicom_extract_tags(dicom_path, file_count)
            self.assertIsInstance(tag_list, list)
            self.assertGreater(len(tag_list), 0)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
