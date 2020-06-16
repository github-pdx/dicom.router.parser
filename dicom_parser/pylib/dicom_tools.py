# -*- coding: UTF-8 -*-
"""DICOM centric utilities for DCMTK and Fuji tags."""
import pathlib
import inspect
import os
import sys
import string
import math
from collections import OrderedDict
import xlsxwriter
from pydicom.tag import Tag

__all__ = ['build_fuji_tag_dict', 'build_dcmtk_tag_dict', 'get_files']

FUJI_TAG = 'Grp  Elmt | Description'
DCMTK_TAG = 'Dicom-Meta-Information-Header'

BASE_DIR, MODULE_NAME = os.path.split(os.path.abspath(__file__))
PARENT_PATH, CURR_DIR = os.path.split(BASE_DIR)
DEMO_ENABLED = True
MAX_EXCEL_TAB = 31
ALPHABET = string.ascii_uppercase
VALID_CHARS = f"-_.()~{ALPHABET}{string.digits}"

HEADERS = ["filename", "accessionNumber", "modality",
           "sourceApplicationEntityTitle", "stationName",
           "institutionName", "manufacturer",
           "manufacturerModelName", "transferSyntaxUid"]

DICOM_ATTRIBUTES = OrderedDict(
    [("filename", 'default.txt'),
     ("accessionNumber", '(0008,0050)'),
     ("modality", '(0008,0060)'),
     ("sourceApplicationEntityTitle", '(0002,0016)'),
     ("stationName", '(0008,1010)'),
     ("institutionName", '(0008,0080)'),
     ("manufacturer", '(0008,0070)'),
     ("manufacturerModelName", '(0008,1090)'),
     ("transferSyntaxUid", '(0002,0010)')])

TRANSFER_SYNTAX = OrderedDict(
    [("1.2.840.10008.1.2", 'LittleEndianImplicit'),  # ILE
     ("1.2.840.10008.1.2.1", 'LittleEndianExplicit'),  # ELE
     ("1.2.840.10008.1.2.2", 'BigEndianExplicit'),  # EBE
     ("1.2.840.10008.1.2.4.50", 'JPEGBaselineProcess1'),  # JPG1
     ("1.2.840.10008.1.2.4.51", 'JPEGBaselineProcess2'),  # JPG2
     ("1.2.840.10008.1.2.4.57", 'JPEGLossless14'),  # JPG14
     ("1.2.840.10008.1.2.4.70", 'JPEGLossless14FOP'),  # JPG14FOP
     ("1.2.840.10008.1.2.4.90", 'JPEG2000Lossless'),  # J2KL
     ("1.2.840.10008.1.2.4.91", 'JPEG2000'),  # J2K
     ("1.2.840.10008.1.2.5", 'RunLengthEncoding')])  # RLE
TRANSFER_SYNTAX.update({v: k for k, v in TRANSFER_SYNTAX.items()})


def get_header_column_widths(input_tag_list: list) -> dict:
    """Returns dynamically sized column widths based on cell values."""
    # list: [row1:[hdr1, ..., hdrN], row2:[data1, ..., dataN]... rowN]
    headers = list(input_tag_list[0])
    scalar = 1.2  # account for presentations difference
    hdr_col_width_dict = OrderedDict([(hdr, -1) for hdr in headers])
    for tag_list in input_tag_list:
        for col_num, cell_val in enumerate(tag_list):
            header = headers[col_num]
            max_length = len(str(cell_val))
            if hdr_col_width_dict[header] < max_length:
                if max_length > 10:
                    max_length *= scalar
                # each char, +2 for readability
                hdr_col_width_dict[header] = int(math.ceil(max_length)) + 2
    return hdr_col_width_dict


def export_to_excel(output_path: pathlib.Path, filename: str,
                    stat_list: list) -> str:
    """Exports DICOM tag data into output Excel report file with markup."""
    def_name = inspect.currentframe().f_code.co_name
    try:
        file_basename = filename.split('.')[0]
        output_filepath = pathlib.Path(output_path, filename)
        workbook = xlsxwriter.Workbook(f"{output_filepath}")
        ws1 = workbook.add_worksheet(
            file_basename[:MAX_EXCEL_TAB])  # <= 31 chars
        ws1.freeze_panes(1, 0)
        # Add formatting: RED fill with dark red text
        format_red = workbook.add_format({'bg_color': '#FFC7CE',
                                          'font_color': '#9C0006',
                                          'bold': False})
        # Add formatting: GREEN fill with dark green text
        format_green = workbook.add_format({'bg_color': '#C6EFCE',
                                            'font_color': '#006100',
                                            'bold': False})
        # includes both header and cell values in calculation
        hdr_col_width_dict = get_header_column_widths(stat_list)
        header_format = workbook.add_format({'bold': True,
                                             'underline': True,
                                             'font_color': 'blue',
                                             'center_across': True})
        header_format.set_font_size(11)
        header_format.set_font_name('Segoe UI')
        stat_list.pop(0)  # remove header row
        for idx, key_hdr in enumerate(hdr_col_width_dict):
            alpha = ALPHABET[idx]
            col_width_val = hdr_col_width_dict[key_hdr]
            ws1.set_column(f"{alpha}:{alpha}", col_width_val)  # all rows
            ws1.write(f"{alpha}1", f"{key_hdr}:", header_format)
        ctr_int = workbook.add_format()
        ctr_int.set_num_format('0')
        ctr_int.set_align('vcenter')
        ctr_int.set_align('center')
        ctr_txt = workbook.add_format()
        ctr_txt.set_align('vcenter')
        ctr_txt.set_align('center')
        ctr_txt.set_font_name('Segoe UI')
        ctr_date = workbook.add_format()
        ctr_date.set_num_format('mm/dd/yy hh:mm AM/PM')
        ctr_date.set_align('vcenter')
        ctr_date.set_align('center')
        ctr_date.set_font_name('Segoe UI')
        if stat_list:  # if data after popped header row
            last_alpha = ALPHABET[
                len(stat_list[0]) - 1]  # last index -1 of len()
            ws1.autofilter(f"A1:{last_alpha}65536")
            # A0, B1, C2, D3, E4, F5, G6, H7 = 8 indexed entries
            num = 1  # first row in Excel
            if len(stat_list) > 0:
                for idx, tag_list in enumerate(stat_list):
                    num += 1  # not header row
                    for count, tag_val in enumerate(tag_list):
                        alpha = ALPHABET[count]
                        ws1.write(f"{alpha}{num}", str(tag_val),
                                  ctr_txt)
        ws1.conditional_format('F2:F%d' % num, {'type': 'text',
                                                'criteria': 'containing',
                                                'value': 'Physicists',
                                                'format': format_green})
        ws1.conditional_format('C2:C%d' % num, {'type': 'text',
                                                'criteria': 'containing',
                                                'value': 'OT',
                                                'format': format_red})
        workbook.close()
        status_str = f"SUCCESS! {def_name}() " \
                     f"'{os.sep.join(output_filepath.parts[-3:])}'"
    except (OSError, xlsxwriter.exceptions.FileCreateError,
            UnicodeDecodeError) as exp:
        status_str = f"~!ERROR!~ {def_name}() {sys.exc_info()[0]}\n{exp}"
    return status_str


# tag: (0008,0050) is represented as ds[0x0008,0x0050].value for pydicom
def build_pydicom_tag_dict() -> dict:
    """Creates mapping of pydicom tag values"""
    pydicom_tag_dict = OrderedDict()
    for tag_key, tag_val in DICOM_ATTRIBUTES.items():
        if 'filename' not in tag_key:
            group_num, element_num = tag_val[1:-1].split(',')
            # group_num_hex = int(group_num, 16)
            # element_num_hex = int(element_num, 16)
            pydicom_tag_dict[tag_key] = Tag(group_num, element_num)
        else:
            pydicom_tag_dict['filename'] = 'default.dcm'
    return pydicom_tag_dict


# tag: (0008,0050) is represented as '0008 0050' for FUJI sourced files
def build_fuji_tag_dict() -> dict:
    """Creates mapping of Fuji tag names to values"""
    fuji_tag_dict = OrderedDict()
    for attr, tag in DICOM_ATTRIBUTES.items():
        fuji_tag_dict[attr] = tag[1:-1].replace(",", " ")
    return fuji_tag_dict


# tag: (0008,0050) is represented as '(0008,0050)' for DCMTK sourced files
def build_dcmtk_tag_dict() -> dict:
    """Creates mapping of DCMTK tag names to values"""
    return DICOM_ATTRIBUTES


def get_files(input_path: pathlib.Path, file_ext: str,
              recursive: bool = True) -> list:
    """Get file paths for specific file extension (including sub-folders)."""
    file_path_list = []
    if isinstance(input_path, pathlib.Path) and isinstance(file_ext, str):
        if input_path.exists():
            if recursive:
                file_path_list = [p.absolute() for p in
                                  sorted(input_path.rglob(f"*{file_ext}"))
                                  if p.is_file()]
            else:
                file_path_list = [p.absolute() for p in
                                  sorted(input_path.glob(f"*{file_ext}"))
                                  if p.is_file()]
    return file_path_list
