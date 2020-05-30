# -*- coding: UTF-8 -*-
"""Module to read and parse DICOM tag data from '.txt' dump files."""
import argparse
import inspect
import math
import os
import string
import sys
import time
import pathlib
from collections import OrderedDict
import xlsxwriter
from pylib import config
from pylib import dicom_tools

BASE_DIR, SCRIPT_NAME = os.path.split(os.path.abspath(__file__))
PARENT_PATH, CURR_DIR = os.path.split(BASE_DIR)
IS_WINDOWS = sys.platform.startswith('win')
DEBUG = False
MAX_EXCEL_TAB = 31
ALPHABET = string.ascii_uppercase
VALID_CHARS = f"-_.()~{ALPHABET}{string.digits}"


def get_header_column_widths(input_tag_list: list) -> dict:
    """Returns dynamically sized column widths based on cell values."""
    # list: [row1:[hdr1, ..., hdrN], row2:[data1, ..., dataN]... rowN]
    headers = list(input_tag_list[0])
    scalar = 1.2  # account for presentations difference
    hdr_col_width_dict = OrderedDict([(hdr, -1) for hdr in headers])
    for tag_list in input_tag_list:
        for col_num, cell_val in enumerate(tag_list):
            header = headers[col_num]
            max_length = len(cell_val)
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
        xls_font_name = 'Segoe UI'
        font_pt_size = 11  # default: 11 pt
        header_format = workbook.add_format({'bold': True,
                                             'underline': True,
                                             'font_color': 'blue',
                                             'center_across': True})
        header_format.set_font_size(font_pt_size)
        header_format.set_font_name(xls_font_name)
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
        ctr_txt.set_font_name(xls_font_name)
        ctr_date = workbook.add_format()
        ctr_date.set_num_format('mm/dd/yy hh:mm AM/PM')
        ctr_date.set_align('vcenter')
        ctr_date.set_align('center')
        ctr_date.set_font_name(xls_font_name)
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


def is_fuji_tag_dump(txt_file_lines: list) -> tuple:
    """Dynamically determines if input is Fuji or DCMTK."""
    is_fuji = False
    is_dcmtk = False
    # check only first n-lines of input file for unique substring match
    for line_str in txt_file_lines[0:5]:
        if dicom_tools.FUJI_TAG in line_str:
            is_fuji = True
        if dicom_tools.DCMTK_TAG in line_str:
            is_dcmtk = True
    return is_fuji, is_dcmtk


def get_tag_line_number(tag_keyword: str, lines: list) -> int:
    """Optimization: stop iterating once index to tag_keyword is located."""
    # using tag_keyword '(0008,0050)' or '0008 0050'
    # if tag_keyword not in input_lines, return -1.
    return next((line_num for line_num, line_str in enumerate(lines)
                 if tag_keyword in line_str), -1)


def get_tag_indices(tags: list, lines: list,
                    is_optimized: bool = True) -> dict:
    """Iterates through lines to find desired DICOM tags."""
    tag_indices_dict = OrderedDict([(hdr, '') for hdr in tags])
    # using tag_keyword '(0008,0050)' or '0008 0050'
    if is_optimized:
        for tag_keyword in tags:
            line_num = get_tag_line_number(tag_keyword, lines)
            if line_num != -1:
                tag_indices_dict[tag_keyword] = lines[line_num]
    else:
        for line_num, line_str in enumerate(lines):
            for tag_keyword in tags:
                if tag_keyword in line_str:
                    tag_indices_dict[tag_keyword] = line_str
    if config.DEBUG:
        for tag_key, tag_value in tag_indices_dict.items():
            print(f"{tag_key}={tag_value}", end='')
    return tag_indices_dict


def parse_dicom_tag_dump(input_headers: list,
                         src_path: pathlib.Path) -> list:
    """Parse DICOM desired tag data from input .txt files."""
    def_name = inspect.currentframe().f_code.co_name
    status_str = f"{def_name}() in: '{os.sep.join(src_path.parts[-3:])}'"
    print(status_str)
    file_path_list = dicom_tools.get_files(src_path, '.txt')
    file_count = 0
    dump_count = 0
    output_tag_list = [input_headers]  # first row contains headers
    if not file_path_list:
        error_msg = f"~!ERROR!~ missing files, check path: \n{src_path}"
        print(error_msg)
    else:
        print(f"parsing: ({len(file_path_list)}) '.txt' files")
        for this_file in file_path_list:
            file_count += 1
            parsed_file_list = []
            read_file_handle = open(this_file, 'r')
            if 'tagdump' not in str(this_file):
                print(f"   reading_{file_count:03}: {str(this_file)}")
                lines_list = read_file_handle.readlines()
                # dynamically determine which input file format:
                (is_fuji, is_dcmtk) = is_fuji_tag_dump(lines_list[0:5])
                if is_fuji:
                    elements = dicom_tools.build_fuji_tag_dict(this_file)
                elif is_dcmtk:
                    elements = dicom_tools.build_dcmtk_tag_dict(this_file)
                else:
                    elements = None  # input '.txt' not a tag dump
                if elements:
                    # re-initializes output dict for each file to blank values
                    tag_dict = OrderedDict([(hdr, '')
                                            for hdr in list(elements.keys())])
                    tag_dict['filename'] = os.path.split(this_file)[-1]
                    # using values: tag '(0008,0050)' or '0008 0050'
                    tag_indices = get_tag_indices(list(elements.values()),
                                                  lines_list)
                    tag_num = 0
                    dump_count += 1
                    for tag_key, tag_value in elements.items():
                        tag_num += 1
                        line_str = tag_indices[tag_value]
                        if len(tag_indices) > 0:
                            if is_dcmtk:
                                # parse value between square brackets [..]
                                if '[' in line_str:
                                    target_value = \
                                        line_str.split('[', 1)[1].split(']')[0]
                                    tag_dict[tag_key] = target_value
                                elif '=' in line_str:
                                    target_value = \
                                        line_str.split('=', 1)[1].split('#')[0]
                                    tag_dict[tag_key] = target_value.strip()
                            elif is_fuji:
                                # parse value between double quotes "..."
                                if '"' in line_str:
                                    target_value = \
                                        line_str.split('"', 1)[1].split('"')[0]
                                    tag_dict[tag_key] = target_value
                        if config.DEBUG:
                            print(f"tag_{tag_num:02} {tag_key:24} "
                                  f"\t{tag_value} line: {line_str:40} "
                                  f"len:{len(line_str):02} chars")
                    for parsed_val in tag_dict.values():
                        parsed_file_list.append(parsed_val)
                    output_tag_list.append(parsed_file_list)
            read_file_handle.close()
        print(f"extraction: {dump_count} dumps of "
              f"{file_count} '.txt' files")
    return output_tag_list


def get_cmd_args() -> pathlib.Path:
    """Command line input on directory to scan recursively for DICOM dumps."""
    def_name = inspect.currentframe().f_code.co_name
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="input path")
    args = parser.parse_args()
    if args.input is None:
        if config.DEMO_ENABLED:
            dst_path = pathlib.Path(PARENT_PATH, 'data',
                                    'input', 'tag_dumps')
        else:
            dst_path = pathlib.Path(PARENT_PATH, 'tag_dumps_all')
    else:
        dst_path = pathlib.Path(args.input)
        if dst_path.exists() and dst_path.is_dir():
            print(f"{def_name}() dumping path:'{str(dst_path)}'")
        else:
            parser.error(f"invalid path: '{dst_path}'")
            dst_path = None
    return dst_path


def main():
    """Driver to read and parse DICOM tag data from text files."""
    print(f"{SCRIPT_NAME} starting...")
    start = time.perf_counter()
    config.show_header(SCRIPT_NAME)
    src_path = get_cmd_args()
    if src_path.exists():
        if config.DEMO_ENABLED:
            dst_path = pathlib.Path(PARENT_PATH, 'data', 'output')
        else:
            dst_path = pathlib.Path(PARENT_PATH, CURR_DIR, 'tag_dumps_all')
        if not dst_path.exists():
            os.makedirs(str(dst_path))
        all_tag_list = parse_dicom_tag_dump(dicom_tools.HEADERS, src_path)
        filename = f"{config.TEMP_TAG}dicom_tag_dumps.xlsx"
        # works on both linux and windows
        if len(all_tag_list) > 1:  # more than just headers
            xls_status = export_to_excel(dst_path, filename, all_tag_list)
            print(xls_status)
    else:
        print(f"~!ERROR!~ invalid path: {src_path}")
    end = time.perf_counter() - start
    print(f"{SCRIPT_NAME} finished in {end:0.2f} seconds")


if __name__ == "__main__":
    main()
