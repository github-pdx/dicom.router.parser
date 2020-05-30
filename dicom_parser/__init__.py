import sys
import os
BASE_DIR, SCRIPT_NAME = os.path.split(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
__all__ = ['parse_dicom_tags']