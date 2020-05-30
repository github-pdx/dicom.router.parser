# -*- coding: UTF-8 -*-
"""Config module for constants and header information."""
import json
import locale
import os
import platform as pfm
import sys
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen
import pkg_resources

BASE_DIR, SCRIPT_NAME = os.path.split(os.path.abspath(__file__))
PARENT_PATH, CURR_DIR = os.path.split(BASE_DIR)
IS_WINDOWS = sys.platform.startswith('win')
DEBUG = False
VERBOSE = False
DEMO_ENABLED = True
TEMP_TAG = '~'

__author__ = "github.pdx"
__email__ = "github.pdx@runbox.com"
__status__ = "demo"
__license__ = "MIT"
__version__ = "1.4.9"

__all__ = ['show_packages', 'get_login', 'get_isp_info', 'show_header']


def show_packages():
    """Displays currently installed python packages on host."""
    installed = sorted([f"{d.project_name:}=={d.version}" for d in
                        list(pkg_resources.working_set)])
    for pkg_name in installed:
        print(f"{pkg_name}")


def get_login() -> str:
    """"getpass.getuser() os.getlogin(): docker does not have username."""
    try:
        username = os.getlogin()
    except OSError:
        username = 'anon_docker'
    return username


def get_isp_info() -> str:
    """Get current ISP information of connected host."""
    isp_req = Request('http://ipinfo.io/json')
    info_str = ''
    try:
        response = urlopen(isp_req)
        isp_data = json.load(response)
        info_str = json.dumps(isp_data, sort_keys=True, indent=6)
    except HTTPError as exception:
        print(f"HTTPError code: {exception.code}")
    except URLError as exception:
        print(f"\nERROR: {sys.exc_info()[0]} {exception}")
        return exception.reason
    return info_str


def show_header(script_name) -> None:
    """Display project status, host characteristics, and ISP information."""
    host_enc = locale.getpreferredencoding()
    host_arch = f"{pfm.system()} {pfm.architecture()[0]} {pfm.machine()}"
    header = f"""    license: \t{__license__}
    python:  \t{pfm.python_version()}
    host:    \t{pfm.node():6} ({host_enc} {host_arch:16})
    login:   \t{get_login()}
    script:  \t{script_name}
    author:  \t{__author__}
    email:   \t{__email__}
    status:  \t{__status__}
    version: \t{__version__}
    isp_info:\t{get_isp_info()}"""
    print(header)
