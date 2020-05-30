# -*- coding: UTF-8 -*-
"""DICOM centric utilities for DCMTK and Fuji tags."""
import pathlib
from collections import OrderedDict

__all__ = ['build_fuji_tag_dict', 'build_dcmtk_tag_dict', 'get_files']

FUJI_TAG = 'Grp  Elmt | Description'
DCMTK_TAG = 'Dicom-Meta-Information-Header'

HEADERS = ["filename", "accessionNumber", "modality",
           "sourceApplicationEntityTitle", "stationName",
           "institutionName", "manufacturer",
           "manufacturerModelName", "transferSyntaxUid"]

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


# tag: (0008,0050) is represented as '0008 0050' for FUJI sourced files
def build_fuji_tag_dict(input_filename: pathlib.Path) -> dict:
    """Creates mapping of Fuji tag names to values"""
    fuji_tag_dict = OrderedDict()
    fuji_tag_dict['filename'] = str(input_filename)
    fuji_tag_dict['accessionNumber'] = '0008 0050'
    fuji_tag_dict['modality'] = '0008 0060'
    fuji_tag_dict['sourceApplicationEntityTitle'] = '0002 0016'
    fuji_tag_dict['stationName'] = '0008 1010'
    fuji_tag_dict['institutionName'] = '0008 0080'
    fuji_tag_dict['manufacturer'] = '0008 0070'
    fuji_tag_dict['manufacturerModelName'] = '0008 1090'
    fuji_tag_dict['transferSyntaxUid'] = '0002 0010'
    return fuji_tag_dict


# tag: (0008,0050) is represented as '(0008,0050)' for DCMTK sourced files
def build_dcmtk_tag_dict(input_filename: pathlib.Path) -> dict:
    """Creates mapping of DCMTK tag names to values"""
    dcmtk_tag_dict = OrderedDict()
    dcmtk_tag_dict['filename'] = str(input_filename)
    dcmtk_tag_dict['accessionNumber'] = '(0008,0050)'
    dcmtk_tag_dict['modality'] = '(0008,0060)'
    dcmtk_tag_dict['sourceApplicationEntityTitle'] = '(0002,0016)'
    dcmtk_tag_dict['stationName'] = '(0008,1010)'
    dcmtk_tag_dict['institutionName'] = '(0008,0080)'
    dcmtk_tag_dict['manufacturer'] = '(0008,0070)'
    dcmtk_tag_dict['manufacturerModelName'] = '(0008,1090)'
    dcmtk_tag_dict['transferSyntaxUid'] = '(0002,0010)'
    return dcmtk_tag_dict


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


'''
   0002 0016 | sourceApplicationEntityTitle
   0008 0050 | accessionNumber
   0008 0060 | modality
   0008 1010 | stationName
   0008 0080 | institutionName
   0008 0070 | manufacturer
   0008 1090 | manufacturerModelName

http://dicomlookup.com/default.asp
http://dicom.nema.org/dicom/2013/output/chtml/part05/sect_6.2.html
'CS' refers to the value representation: Code String 16 bytes max

FUJI:  vertical bars | or ---- present in each line
key: tag with no parentheses or comma '#### ####'
value: between double quotes "..."
example:   0008 0060 | modality       | CS |     1 | "CR"

DCMTK:  number sign # present in each line
key: between (####,####)
value: between square brackets [...]
example:   (0008,0060) CS [CT]         #   2, 1 Modality
'''
