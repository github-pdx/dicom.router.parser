# -*- coding: UTF-8 -*-
"""Module to read and parse DICOM tag data from '.txt' dump files."""
import inspect
import os
import sys
import time
import traceback
import pathlib
import pydicom
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


def get_dicom_dump_paths(src_path: pathlib.Path) -> list:
    """Locate .dcm files in source path."""
    def_name = inspect.currentframe().f_code.co_name
    status_str = f"{def_name}() from: '{os.sep.join(src_path.parts[-3:])}'"
    print(status_str)
    file_path_list = dicom_tools.get_files(input_path=src_path,
                                           file_ext='.dcm')
    #if not file_path_list:
    #    error_msg = f"~!ERROR!~ missing files, check path: \n{src_path}"
    #    print(error_msg)
    return file_path_list


def parse_dicom_tag_dumps(src_path: pathlib.Path) -> list:
    """Parse desired DICOM attributes from input '.dcm' files."""
    all_tag_list = [dicom_tools.HEADERS]
    dicom_path_list = get_dicom_dump_paths(src_path)
    for file_count, dicom_path in enumerate(dicom_path_list):
        all_tag_list.append(
            read_dicom_extract_tags(dicom_path, file_count))
    return all_tag_list


def sanitize_input(input_str: str = '') -> str:
    """Remove invalid characters from DICOM tags."""
    sanitized = input_str
    invalid_chars = "{}[]()<>^#+*?$@&%$!,:;/\\ "  # keep - and .
    # sanitized = sanitized.replace("-", "")
    for char in invalid_chars:
        if char in input_str:
            sanitized = sanitized.replace(char, "")
    return sanitized


def read_dicom_extract_tags(src_path: pathlib.Path, file_count: int) -> list:
    """Parse desired DICOM attributes from input DICOM files."""
    parsed_values_list = []
    try:
        print(f"   reading_{file_count:03}: {str(src_path)}")
        dataset = pydicom.read_file(str(src_path))
        element_dict = dicom_tools.build_pydicom_tag_dict()
        element_dict['filename'] = src_path.name
        metatags = ['sourceApplicationEntityTitle', 'transferSyntaxUid']
        # element_dict[tag_key] = ds.file_meta[0x0002, 0x0016].value
        for tag_key, tag in element_dict.items():
            if 'filename' not in tag_key:
                if tag_key in metatags:
                    element_dict[tag_key] = dataset.file_meta[tag].value
                else:
                    # print(f"{tag} '{tag_key}' = '{ds[tag].value}'")
                    if tag in dataset:
                        clean_val = sanitize_input(dataset[tag].value)
                        element_dict[tag_key] = clean_val
        for parsed_val in element_dict.values():
            parsed_values_list.append(parsed_val)
    except (OSError, ValueError, KeyError):
        show_exception()
    return parsed_values_list


def main():
    """Driver to read and parse DICOM tag data from text files."""
    print(f"{MODULE_NAME} starting...")
    start = time.perf_counter()
    config.show_header(MODULE_NAME)
    args = cmd_args.get_cmd_args()
    if args.input_path.exists():
        all_dicom_list = parse_dicom_tag_dumps(args.input_path)
        dcm_filename = f"{config.TEMP_TAG}dicom_dicom_tags.xlsx"
        if len(all_dicom_list) > 1:  # more than just headers
            xls_status = dicom_tools.export_to_excel(args.output_path,
                                                     dcm_filename,
                                                     all_dicom_list)
            print(xls_status)
    else:
        print(f"~!ERROR!~ invalid path: {args.input_path}")
    end = time.perf_counter() - start
    print(f"{MODULE_NAME} finished in {end:0.2f} seconds")


if __name__ == "__main__":
    main()
