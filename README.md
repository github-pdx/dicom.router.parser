# *Compass Imaging Router* DICOM Transfer Reporting

[![Build Status](https://travis-ci.com/averille-dev/dicom_router_parser.svg?branch=master)](https://travis-ci.com/averille-dev/dicom_router_parser)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## PowerShell Script (v4.0+) to Parse DICOMs
1. Copies *largest* DICOM (.dcm) from source directory to new destination
2. Perform DICOM tag dump (or MS SQL Server query) to extract specific information about each study
3. Exports the desired metadata to .csv/.xlsx, where each row = 1 instance of a DICOM transfer to the IMG_RTR
Note: largest file size is used to avoid inadvertently parsing presentation states (PR) or stuctured reports (SR)


## Options: 
To filter studies and toggle logging
```powershell
$PURGE_OUTPUT_CSV = $True
$EXPORT_FIRST_DCM = $False
$DUMP_TAGS_XMLs = $False
$FILTER_PH_AETs = $False
```

## Directories:
```powershell
$dcmtk_path = "$pwd_parent_path\dicom_libs\lib_dcmtk-3.6.6\bin"
$src_path = "$pwd_parent_path\data\input\DICOM"
$dst_path = "$pwd_parent_path\data\output\$base_filename$(Get-Month-Filename)"
IMG_RTR_MM-YYYY_DICOMs (largest dicom, .xml, .txt tag dumps)
IMG_RTR_MM-YYYY_REPORTs (Excel workbook)
```

## Example Output:
![Screenshot](https://github.com/averille-dev/dicom_router_parser/blob/master/img/excel_export_router.png)
* [Compass Router MS SQL Server Excel Report](https://github.com/averille-dev/dicom_router_parser/blob/master/data/examples/IMG_RTR_Transfers_06-09-19.xlsx)
* [DICOM '.txt' Tag Dump](https://github.com/averille-dev/dicom_router_parser/blob/master/data/examples/dicom_exports/9fe63f0a-d304-4a22-9e4b-f0ebe63f7f78.txt)
* [DICOM '.xml' Tag Dump](https://github.com/averille-dev/dicom_router_parser/blob/master/data/examples/dicom_exports/9fe63f0a-d304-4a22-9e4b-f0ebe63f7f78.xml)
* [SQL query](https://github.com/averille-dev/dicom_router_parser/blob/master/sql/select_query.sql)


### Example Dump Output:
![Screenshot](https://github.com/averille-dev/dicom_router_parser/blob/master/img/excel_report_txt_dump.png)
* [Excel Report (textfile dumps)](https://github.com/averille-dev/dicom_router_parser/blob/master/data/output/~dicom_textfile_dumps.xlsx)


### Example DICOM tag Output:
![Screenshot](https://github.com/averille-dev/dicom_router_parser/blob/master/img/excel_report_dicom.png)
* [Excel Report - DICOM Tag](https://github.com/averille-dev/dicom_router_parser/blob/master/data/output/~dicom_dicom_tags.xlsx)


## *DICOM* Resources:
* [Compass Router](http://www.laurelbridge.com/pdf/Compass-User-Manual.pdf)
* [LaurelBride DCF SDK](http://www.laurelbridge.com/products/dcf/)
* [LaurelBride DCF Examples](http://www.laurelbridge.com/docs/dcf34/ExampleDocs/)
* [dcm4che](https://dcm4che.atlassian.net/wiki/spaces/lib/overview)
* [DCMTk](https://dicom.offis.de/dcmtk.php.en#snapshot)
* [GDCM](https://github.com/malaterre/GDCM)
* [NiBabel](https://nipy.org/nibabel/)


## *DICOM* Tools:
* [Slicer3D](https://www.slicer.org/)
* [DICOM Cleaner](http://www.dclunie.com/pixelmed/software/webstart/DicomCleanerUsage.html)
* [MATLAB DICOM Toolbox](https://www.mathworks.com/help/images/scientific-file-formats.html)
* [pydicom](https://pydicom.github.io/pydicom/stable/index.html)
* [LEADTOOLS](https://www.leadtools.com/sdk/medical/pacs)
* [MicroDicom Viewer](https://www.microdicom.com/)


## *DICOM* Test Data:
* [pydicom test datasets](https://github.com/pydicom/pydicom/tree/master/pydicom/data/test_files)
* [GDCM test datasets](http://gdcm.sourceforge.net/wiki/index.php/Sample_DataSet)


### Open-source *PACS*:
* [Orthanc](https://www.orthanc-server.com/)
* [SonicDICOM](https://sonicdicom.com/)
* [OsiriX for Mac](https://www.osirix-viewer.com/resources/pacs/)


## License:
[MIT License](LICENSE)
