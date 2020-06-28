# -*- coding: UTF-8 -*-
"""Module to read and parse DICOM tag data from '.txt' dump files."""
import inspect
import os
import sys
import time
import pathlib
import traceback
from collections import OrderedDict
from pylib import config
from pylib import dicom_tools
from pylib import cmd_args

BASE_DIR, MODULE_NAME = os.path.split(os.path.abspath(__file__))
PARENT_PATH, CURR_DIR = os.path.split(BASE_DIR)


def show_exception():
    """Custom exception handling function."""
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback,
                              limit=2, file=sys.stdout)


def get_dump_type(src_path: pathlib.Path) -> dict:
    """Dynamically determines if input is Fuji or DCMTK format."""
    type_dict = {'is_dcmtk': False, 'is_fuji': False, 'is_other': True}
    try:
        if isinstance(src_path, pathlib.Path) and src_path.exists():
            with open(src_path, 'r') as read_file_handle:
                lines_list = read_file_handle.readlines(300)
                # check only first n-lines of input file for unique substring match
                for line_str in lines_list:
                    if dicom_tools.DCMTK_TAG in line_str:
                        type_dict['is_dcmtk'] = True
                    if dicom_tools.FUJI_TAG in line_str:
                        type_dict['is_fuji'] = True
                if not type_dict['is_dcmtk'] and not type_dict['is_fuji']:
                    type_dict['is_other'] = True
            read_file_handle.close()
    except (OSError, ValueError):
        show_exception()
    return type_dict


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


def get_txt_dump_paths(src_path: pathlib.Path) -> list:
    """Locate .txt tag dump files in source path."""
    def_name = inspect.currentframe().f_code.co_name
    status_str = f"{def_name}() in: '{os.sep.join(src_path.parts[-3:])}'"
    print(status_str)
    file_path_list = []
    if isinstance(src_path, pathlib.Path) and src_path.exists():
        file_path_list = dicom_tools.get_files(src_path, '.txt')
        if not file_path_list:
            error_msg = f"~!ERROR!~ missing files, check path: \n{src_path}"
            print(error_msg)
    return file_path_list


def parse_fuji_tag_dump(src_path: pathlib.Path, file_count: int) -> list:
    """Parse desired DICOM attributes from input Fuji .txt files."""
    parsed_values_list = []
    try:
        if isinstance(src_path, pathlib.Path) and src_path.exists():
            with open(src_path, 'r') as read_file_handle:
                if 'tagdump' not in str(src_path):
                    print(f"   reading_{file_count:03}: {str(src_path)}")
                    lines_list = read_file_handle.readlines()
                    element_dict = dicom_tools.build_fuji_tag_dict()
                    # re-initializes output dict for each file to blank values
                    tag_dict = OrderedDict([(hdr, '') for hdr in
                                            list(element_dict.keys())])
                    tag_dict['filename'] = src_path.name
                    # using values: tag '(0008,0050)' or '0008 0050'
                    tag_indices = get_tag_indices(list(element_dict.values()),
                                                  lines_list)
                    tag_num = 0
                    for tag_key, tag_value in element_dict.items():
                        tag_num += 1
                        line_str = tag_indices[tag_value]
                        if len(tag_indices) > 0:
                            # parse value between double quotes "..."
                            if '"' in line_str:
                                target_value = \
                                    line_str.split('"', 1)[1].split('"')[0]
                                tag_dict[tag_key] = target_value
                    for parsed_val in tag_dict.values():
                        parsed_values_list.append(parsed_val)
            read_file_handle.close()
    except (OSError, ValueError):
        show_exception()
    return parsed_values_list


def parse_dcmtk_tag_dump(src_path: pathlib.Path, file_count: int) -> list:
    """Parse desired DICOM attributes from input DCMTK .txt files."""
    parsed_values_list = []
    try:
        if isinstance(src_path, pathlib.Path) and src_path.exists():
            with open(src_path, 'r') as read_file_handle:
                if 'tagdump' not in str(src_path):
                    print(f"   reading_{file_count:03}: {str(src_path)}")
                    lines_list = read_file_handle.readlines()
                    element_dict = dicom_tools.build_dcmtk_tag_dict()
                    # re-initializes output dict for each file to blank values
                    tag_dict = OrderedDict([(hdr, '')
                                            for hdr in
                                            list(element_dict.keys())])
                    tag_dict['filename'] = src_path.name
                    # using values: tag '(0008,0050)' or '0008 0050'
                    tag_indices = get_tag_indices(list(element_dict.values()),
                                                  lines_list)
                    tag_num = 0
                    for tag_key, tag_value in element_dict.items():
                        tag_num += 1
                        line_str = tag_indices[tag_value]
                        if len(tag_indices) > 0:
                            # parse value between square brackets [..]
                            if '[' in line_str:
                                target_value = \
                                    line_str.split('[', 1)[1].split(']')[0]
                                tag_dict[tag_key] = target_value
                            elif '=' in line_str:
                                target_value = \
                                    line_str.split('=', 1)[1].split('#')[0]
                                tag_dict[tag_key] = target_value.strip()
                        if config.DEBUG:
                            print(f"tag_{tag_num:02} {tag_key:24} "
                                  f"\t{tag_value} line: {line_str:40} "
                                  f"len:{len(line_str):02} chars")
                    for parsed_val in tag_dict.values():
                        parsed_values_list.append(parsed_val)
            read_file_handle.close()
    except (OSError, ValueError):
        show_exception()
    return parsed_values_list


def parse_txt_tag_dumps(src_path: pathlib.Path) -> list:
    """Parse desired DICOM attributes from input '.txt' files."""
    def_name = inspect.currentframe().f_code.co_name
    all_tag_list = [dicom_tools.HEADERS]
    if isinstance(src_path, pathlib.Path) and src_path.exists():
        dump_path_list = get_txt_dump_paths(src_path)
        dump_count = 0
        for dump_path in dump_path_list:
            dump_type = get_dump_type(dump_path)
            if dump_type['is_dcmtk']:
                dump_count += 1
                all_tag_list.append(
                    parse_dcmtk_tag_dump(dump_path, dump_count))
            elif dump_type['is_fuji']:
                dump_count += 1
                all_tag_list.append(
                    parse_fuji_tag_dump(dump_path, dump_count))
        print(f"{def_name}() {dump_count} of {len(dump_path_list)} files")
    return all_tag_list


def main():
    """Driver to read and parse DICOM tag data from text files."""
    print(f"{MODULE_NAME} starting...")
    start = time.perf_counter()
    config.show_header(MODULE_NAME)
    args = cmd_args.get_cmd_args()
    if args.input_path.exists():
        if config.DEMO_ENABLED:
            dst_path = pathlib.Path(PARENT_PATH, 'data', 'output')
        else:
            dst_path = pathlib.Path(PARENT_PATH, CURR_DIR, 'tag_dumps_all')
        if not dst_path.exists():
            dst_path.mkdir(parents=True, exist_ok=True)
        all_tag_list = parse_txt_tag_dumps(args.input_path)
        txt_filename = f"{config.TEMP_TAG}dicom_textfile_dumps.xlsx"
        # works on both linux and windows
        if len(all_tag_list) > 1:  # more than just headers
            xls_status = dicom_tools.export_to_excel(args.output_path,
                                                     txt_filename,
                                                     all_tag_list)
            print(xls_status)
    else:
        print(f"~!ERROR!~ invalid path: {args.input_path}")
    end = time.perf_counter() - start
    print(f"{MODULE_NAME} finished in {end:0.2f} seconds")


if __name__ == "__main__":
    main()
