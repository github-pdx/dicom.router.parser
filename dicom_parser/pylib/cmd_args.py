# -*- coding: UTF-8 -*-
"""UI module to parse user input."""
import argparse
import inspect
import os
import pathlib
from pathvalidate.argparse import sanitize_filepath_arg

BASE_DIR, MODULE_NAME = os.path.split(os.path.abspath(__file__))
PARENT_PATH, CURR_DIR = os.path.split(BASE_DIR)
TWO_PARENT_PATH = os.sep.join(pathlib.Path(BASE_DIR).parts[:-2])

__all__ = ['get_cmd_args']


def get_cmd_args() -> list:
    """Command line input on directory to scan recursively for media files."""
    def_name = inspect.currentframe().f_code.co_name
    parser = argparse.ArgumentParser(description='dicom_parser')
    parser.add_argument("-i", "--input_path",
                        type=sanitize_filepath_arg,
                        help="input file path")
    parser.add_argument("-o", "--output_path",
                        type=sanitize_filepath_arg,
                        help="output file path")
    args = parser.parse_args()
    if args.input_path is None:
        args.input_path = pathlib.Path(TWO_PARENT_PATH, 'data', 'input')
    else:
        args.input_path = pathlib.Path(args.input_path)
        if args.input_path.exists() and args.input_path.is_dir():
            print(f"{def_name}() dumping path:'{str(args.file_path)}'")
        else:
            parser.error(f"invalid path: '{str(args.input_path)}'")
            args.input_path = None
    if args.output_path is None:
        args.output_path = pathlib.Path(TWO_PARENT_PATH, 'data', 'output')
        if not args.output_path.exists():
            args.output_path.mkdir(parents=True, exist_ok=True)
    else:
        args.output_path = pathlib.Path(args.output_path)
        if args.output_path.exists() and args.output_path.is_dir():
            print(f"{def_name}() dumping path:'{str(args.output_path)}'")
        else:
            parser.error(f"invalid path: '{str(args.output_path)}'")
            args.output_path = None
    return args
