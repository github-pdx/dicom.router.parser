# -*- coding: UTF-8 -*-
"""Unit tests to extract DICOM tags."""
import unittest
import os
import pathlib
from collections import OrderedDict
from dicom_parser import parse_txt_dumps as pt

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
        self.fuji_tag = 'Grp  Elmt | Description'
        self.dcmtk_tag = 'Dicom-Meta-Information-Header'
        self.fuji_dict = OrderedDict(
            [("accessionNumber", 24),
             ("modality", 25),
             ("sourceApplicationEntityTitle", 9),
             ("stationName", 30),
             ("institutionName", 27),
             ("manufacturer", 26),
             ("manufacturerModelName", 41),
             ("transferSyntaxUid", 6)])
        self.dcmtk_dict = OrderedDict(
            [("AccessionNumber", 27),
             ("Modality", 28),
             ("SourceApplicationEntityTitle", 11),
             ("StationName", 33),
             ("InstitutionName", 30),
             ("Manufacturer", 29),
             ("ManufacturerModelName", 44),
             ("TransferSyntaxUID", 8)])
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

    def test_get_tag_line_number_fuji(self):
        read_file_handle = open(self.valid_fuji, 'r')
        lines_list = read_file_handle.readlines()
        for tag_keyword in self.fuji_dict.keys():
            line_num = pt.get_tag_line_number(tag_keyword, lines_list)
            self.assertEqual(self.fuji_dict[tag_keyword], line_num)
        read_file_handle.close()

    def test_get_tag_line_number_dcmtk(self):
        read_file_handle = open(self.valid_dcmtk, 'r')
        lines_list = read_file_handle.readlines()
        for tag_keyword in self.dcmtk_dict.keys():
            line_num = pt.get_tag_line_number(tag_keyword, lines_list)
            self.assertEqual(self.dcmtk_dict[tag_keyword], line_num)
        read_file_handle.close()

    def test_get_tag_indices_fuji(self):
        read_file_handle = open(self.valid_fuji, 'r')
        lines_list = read_file_handle.readlines()
        for tag_keyword in self.fuji_dict.keys():
            line_num = pt.get_tag_line_number(tag_keyword, lines_list)
            indices_dict = pt.get_tag_indices(self.fuji_dict.keys(),
                                              lines_list)
            self.assertEqual(lines_list[line_num], indices_dict[tag_keyword])
        read_file_handle.close()

    def test_get_tag_indices_dcmtk(self):
        read_file_handle = open(self.valid_dcmtk, 'r')
        lines_list = read_file_handle.readlines()
        for tag_keyword in self.dcmtk_dict.keys():
            line_num = pt.get_tag_line_number(tag_keyword, lines_list)
            indices_dict = pt.get_tag_indices(self.dcmtk_dict.keys(),
                                              lines_list)
            self.assertEqual(lines_list[line_num], indices_dict[tag_keyword])
        read_file_handle.close()

    def test_get_txt_dump_paths(self):
        dump_path_list = pt.get_txt_dump_paths(self.valid_dumps)
        for txt_path in dump_path_list:
            self.assertEqual(txt_path.suffix, '.txt')
            self.assertIsInstance(txt_path, pathlib.Path)
            self.assertTrue(txt_path.exists())
        self.assertGreater(len(dump_path_list), 1)

    def test_parse_fuji_tag_dump(self):
        read_file_handle = open(self.valid_fuji, 'r')
        lines_list = read_file_handle.readlines(300)
        tag_list = pt.parse_fuji_tag_dump(self.valid_fuji, 0)
        self.assertGreater(len(tag_list), 1)
        self.assertTrue(self.fuji_tag in ''.join(lines_list))
        self.assertFalse(self.dcmtk_tag in ''.join(lines_list))
        read_file_handle.close()

    def test_parse_dcmtk_tag_dump(self):
        read_file_handle = open(self.valid_dcmtk, 'r')
        lines_list = read_file_handle.readlines(300)
        tag_list = pt.parse_fuji_tag_dump(self.valid_dcmtk, 0)
        self.assertGreater(len(tag_list), 1)
        self.assertTrue(self.dcmtk_tag in ''.join(lines_list))
        self.assertFalse(self.fuji_tag in ''.join(lines_list))
        read_file_handle.close()

    def test_parse_txt_tag_dumps(self):
        tag_list = pt.parse_txt_tag_dumps(self.valid_dumps)
        # includes headers for count of 4
        self.assertEqual(len(tag_list), 4)
        tag_list = pt.parse_txt_tag_dumps(self.valid_dicoms)
        self.assertEqual(len(tag_list), 1)
        tag_list = pt.parse_txt_tag_dumps(self.invalid_path)
        self.assertEqual(len(tag_list), 1)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
