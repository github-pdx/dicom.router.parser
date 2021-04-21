<#  
PS script to copy largest DICOM (.dcm) from source directory to new destination 
Then runs a tag dump to extract specific information about each study. 
Note: the largest file size is used to avoid inadvertently parsing presentation states (PR) or stuctured reports (SR).
Lastly, this script exports desired metadata to .csv/.xlsx, where each row = 1 instance of a DICOM transfer to the PHSWIMG_RTR. 
#>
$author = "averille.dev"
$email = "dicom.pdx@runbox.com"
$status = "Testing on PHODICOMRTRTST PS v4.0 to v5.1"
$version = "1.3.8"
$ps_version = $PSVersionTable.PSVersion
$script_name = $MyInvocation.MyCommand.Name 

<# 
Sources: 
https://dicom.offis.de/dcmtk.php.en
https://support.dcmtk.org/docs-354/dcmdump.html
https://www.microsoft.com/en-us/download/details.aspx?id=14632
https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/export-csv?view=powershell-6
https://community.spiceworks.com/topic/813598-add-custom-colum-and-header-to-export
https://www.red-gate.com/simple-talk/sysadmin/powershell/powershell-one-liners-collections-hashtables-arrays-and-strings/#first
https://stackoverflow.com/questions/12206314/detect-if-visual-c-redistributable-for-visual-studio-2012-is-installed
https://stackoverflow.com/questions/37715867/sort-all-files-in-all-folders-by-size
https://lazywinadmin.com/2015/08/powershell-remove-special-characters.html#w-meta-character
https://get-powershellblog.blogspot.com/2017/06/lets-kill-write-output.html
https://stackoverflow.com/questions/38523369/write-host-vs-write-information-in-powershell-5
#>

$server_name = $env:ComputerName
$root_dir = $PSScriptRoot
$base_filename = "IMG_RTR_Transfers"

#~#~#~# FLAGS: toggle with $True or $False #~#~#~# 
$PURGE_ALL = $False
$PURGE_OUTPUT_CSV = $True
$DEBUG = $False
$VERBOSE = $True
$PRINT_FILE_STATS = $False
$PRINT_TIMER = $True
$delimiter = ","

#~#~#~# OPTIONS:
$EXPORT_FIRST_DCM = $True
$DUMP_TAGS_XMLs = $True
$FILTER_AETs = $False

$AET_PATTERN = [string[]] ("ADAC_","AEGISWEB","FILA_","VANC_", "MCPB_", "MEHC_","RSEND_","SWMC_","SW_","SW_CATH","VHI_")
$AET_PATTERN_STR = ""
ForEach($substring in $AET_PATTERN) {
    $AET_PATTERN_STR += "'" + $substring + "'"
}


function Start_Timer () {
    [OutputType([System.Diagnostics.Stopwatch])]
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    return $timer 
}


function Stop_Print_Timer ([System.Diagnostics.Stopwatch] $input_timer, [string] $input_title='default_title' ) {
    $input_timer.Stop()
    if ($PRINT_TIMER) {
        $elapsed_time = [TimeSpan]$input_timer.Elapsed
        $formatTime = Format_Elapsed_Time $elapsed_time
        Write-Host (" '{0,-24}' {1,-24} runtime: {2}" -f $script_name, $input_title, $formatTime) -ForegroundColor DarkCyan
    }
}
$benchmark = Start_Timer


function Get_TimeStamp {  
    return "{0:MM/dd/yy} {0:HH:mm:ss tt}" -f (Get-Date)
}


function Get_Month_Filename {  
    return "_{0:MM-yyyy}" -f (Get-Date)
}


function Get_Week_Filename { 
    $month_str = "{0:MM-yyyy}" -f (Get-Date)
    $week_num = (Get-Date -UFormat %V)
    $week_str = "week$week_num"
    return "_$month_str_$week_str"
}


function Get_Today_Filename {  
    return "_{0:MM-dd-yyyy}" -f (Get-Date)
}


function Get_TimeStamp_Filename {  
    return "_{0:MM-dd-yyyy}-{0:HH.mm_tt}" -f (Get-Date)
}


function Get_Modified_Timestamp ( [string]$input_filepath='default_path' ) { 
    $file_stat = (Get-Item -Path $input_filepath)
    return "created@{0:HH.mmtt}" -f $file_stat.LastWriteTime
}


function is_Path_Valid ( [string]$title_str='default_title', [string]$input_path='default_path' ) { 
    if (Test-Path $input_path) { 
        $isPathValid = $True
    } else {
        $isPathValid = $False
        Write-Warning -Message ("!*ERROR*!~ {0}: '{1}' does not exist...`n" -f $title_str, $input_path )
    }
    return $isPathValid
}


function Print_Bool_State ( [string]$input_title='default_title', [bool]$input_bool ) {
    if (($input_bool) -and ($VERBOSE)) {
        Write-Host ("{0,-18} {1,-5}= ENABLED" -f $input_title, $input_bool ) -ForegroundColor DarkGreen
    } else {
        Write-Host ("{0,-18} {1,-5}= DISABLED" -f $input_title, $input_bool ) -ForegroundColor Red
    }
}


$pwd_path = Get-Location
$pwd_parent_path = Split-Path -Path $pwd_path -Parent
$dcmtk_path = "$pwd_parent_path\dicom_libs\lib_dcmtk-3.6.6\bin"
$isdcmtkPathValid = is_Path_Valid "dcmtk_path" $dcmtk_path

#$src_parent_path = "D:\ImageRepository"     # on compass router 
$src_parent_path = "$pwd_parent_path\data\input"  # for demo: current working directory
$src_path = (Join-Path "$src_parent_path" -ChildPath "DICOM")
$isSrcValid = is_Path_Valid "src_path" $src_path

$dst_parent_path = "$pwd_parent_path\data\output"
$dst_path = (Join-Path "$dst_parent_path" -ChildPath "$base_filename$(Get_Month_Filename)")
$dst_drive_name = Split-Path -Path $dst_parent_path -Qualifier

Write-Host ("'{0}' v:{1} running PSversion:{2} on {3}" -f $script_name, $version, $ps_version, $server_name) -ForegroundColor Gray
$isDstValid = is_Path_Valid "dst_drive_name" $dst_drive_name


function Create_Directory ( [string]$input_dirpath='default_path' ) {
    if(!(Test-Path "$input_dirpath")) {
         $null = New-Item -ItemType Directory -Path $input_dirpath -Force
    }
}


function Purge_Directory ( [string]$input_dirpath='default_path' ) {
    if( Test-Path $input_dirpath ) {
        try {
            Write-Warning -Message ("purging: $input_dirpath")
            Remove-Item -LiteralPath $input_dirpath  -Recurse -Force
            Start-Sleep -Seconds 1
        } catch {
            $ErrorMessage = $_.Exception.Message
            Write-Warning -Message ("~!*ERROR*!~ {0}" -f $ErrorMessage)
        }          
    }
}


function Purge_File ( [string]$input_filepath='default_path' ) {
    if (Test-Path $input_filepath) {
        try {
            Write-Host ("purging: $input_filepath")
            Remove-Item -LiteralPath "$input_filepath" -Force
        } catch {
            $ErrorMessage = $_.Exception.Message
            Write-Warning -Message ("~!*ERROR*!~ {0}" -f $ErrorMessage)
        } # end try-catch
    }
}


if ($isDstValid) {
    $dump_dst_parent = "$dst_path" + "_DICOMs"
    $file_dst_parent = "$dst_path" + "_REPORTs"
    $log_outfile = (Join-Path "$file_dst_parent" -ChildPath "$base_filename$(Get_Today_Filename).txt")

    if(Test-Path $dst_parent_path) {
        if ($PURGE_ALL) {
            Purge_Directory $dump_dst_parent
            Purge_Directory $file_dst_parent
        } 
        Purge_File $log_outfile
    } 
    if ($EXPORT_FIRST_DCM -or $DUMP_TAGS_XMLs) {
        Create_Directory $dump_dst_parent
    }
    Create_Directory $file_dst_parent

    Write-Host (" <-- src_path: {0}" -f $src_path)
    Write-Host (" --> dst_path: {0}" -f $dst_path)
}


function Format_Elapsed_Time ( [TimeSpan]$ts ) {
    [OutputType([string])]
    $elapsedTime = ""
    if ( $ts.Minutes -gt 0 ) {
        $elapsedTime = [string]::Format( "{0:00} min {1:00}.{2:00} sec", $ts.Minutes, $ts.Seconds, $ts.Milliseconds / 10 );
    }
    else {
        $elapsedTime = [string]::Format( "{0:00}.{1:00} sec", $ts.Seconds, $ts.Milliseconds / 10 );
    }
    if ($ts.Hours -eq 0 -and $ts.Minutes -eq 0 -and $ts.Seconds -eq 0) {
        $elapsedTime = [string]::Format("{0:00}.{1:00} sec", $ts.Seconds, $ts.Milliseconds);
    }
    if ($ts.Milliseconds -eq 0) {
        $elapsedTime = [string]::Format("{0:00} ms", $ts.TotalMilliseconds);
    } 
    return $elapsedTime
}


function Print_File_Stats ( [string]$input_filepath='default_path' ) {
    $file_stat_str = ""
    if (Test-Path $input_filepath) {
        try {
            $input_filename = [System.IO.Path]::GetFileName($input_filepath)
            $file_acl = (Get-Acl -Path $input_filepath)
            $author = $file_acl.Owner
            $file_stat = (Get-Item -Path $input_filepath)
            $fileSizeMB = (Get-Item -Path $input_filepath) | % {[decimal]($_.Length / 1mb)}
            $fileSizeKB = (Get-Item -Path $input_filepath) | % {[decimal]($_.Length / 1kb)}
            $file_hash = (Get-FileHash -Path $input_filepath -Algorithm SHA1)

            $file_stat_str = ("`t created: [{0:MM-dd-yyyy} {0:HH:mm:ss tt}]" -f $file_stat.CreationTime) 
            $file_stat_str += ("`t owner: {0}" -f $author) 
            $file_stat_str += ("`t size: {0,0:f2} KB" -f $fileSizeKB) 
            $file_stat_str += ("`n`tmodified: [{0:MM-dd-yyyy} {0:HH:mm:ss tt}]" -f $file_stat.LastWriteTime) 
            $file_stat_str += ("`t {0}: {1}" -f $file_hash.Algorithm, $file_hash.Hash)         
       } catch {
            $ErrorMessage = $_.Exception.Message
            Write-Warning -Message ("~!*ERROR*!~ {0}" -f $ErrorMessage)
        } finally {
            if ($file_stat_str.Length -gt 0) {
                if ($PRINT_FILE_STATS) {
                    Write-Host ("{0} {1}" -f $input_title, $file_stat_str) -ForegroundColor Gray
                }
            }
        } #end try-catch-finally
    } # input_filepath
}


function Is_Excel_Installed () {
    [OutputType([bool])]
    $isExcelInstalled = $False
    if (Test-Path HKLM:SOFTWARE\Classes\Excel.Application) {
        #Write-Host "Microsoft Excel installed, exporting to .xlsx"
        $isExcelInstalled = $True
    } else {
        Write-Warning -Message "Microsoft Excel NOT installed, exporting to .csv only"
    }
    return $isExcelInstalled
}


function Release_Excel_Reference ($ref) {
    try {
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($ref)
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
    } catch {
        $ErrorMessage = $_.Exception.Message
        Write-Warning -Message ("~!*ERROR*!~ {0}" -f $ErrorMessage)
    }
}

#~#~#~# writes output to a log file with a timestamp #~#~#~# 
function Write-Log ( [string]$input_str) {
	[string]$date = Get-Date -Format g
	#( "[" + $date + "] - " + $input_str) | Out-File -FilePath $log_outfile -Append
    if ($input_str.Length -gt 0) {
        ($input_str) | Out-File -FilePath $log_outfile -Append
    }
} 


#~#~#~# check if sourceAET is from an outside institution #~#~#~# 
function Verify-AET ([string]$input_AET) {
    $isValid = $False
    $isMinLength = ($input_AET.Length -gt 0)
    if($isMinLength) {
        $isNotInsideStudy = ($AET_PATTERN | %{$input_AET.contains($_)}) -notcontains $True
        if($isNotInsideStudy) {
            $isValid = $True
        }
    }
    return ($isValid)
}

#~#~#~# remove tags with invalid characters/symbols #~#~#~# 
function Sanitize_Input ( [string]$input_str='default_str' ) {
    [OutputType([string])]
    $empty_str = ""
    # letters, numbers, newlines, underlines, hyphens, and periods: OK
    $sanitized_str = $input_str -replace "[^a-zA-Z0-9\s._-]", ""
    if ($sanitized_str.Length -gt 0) {
        return ([string]$sanitized_str)
    } else {
        return ([string]$empty_str)
    }
}

#~#~#~# parsing performed one-by-one to maintain data integrity with corrupt tags #~#~#~#
function Get-Dicom-Tag {
    Param
    (
        [Parameter(Mandatory=$True, Position=0)]
        [string] $dcm_path,
        [Parameter(Mandatory=$True, Position=1)]
        [string] $lookup_tag
    )
    $empty_str = ""
    $dump_cmd_str = "$dcmtk_path\dcmdump.exe --quote-as-octal --ignore-errors --quiet --ignore-parse-errors --enable-correction '$dcm_path' --search '$lookup_tag'"
    $cmd_output = iex ($dump_cmd_str)

    if ($cmd_output) {
        $tag_list = $cmd_output.Split([char]0x005B, [char]0x005D)  # value between brackets: [ ] 
        $parsed_tag = [string]$tag_list[1]

        return Sanitize_Input($parsed_tag) 
    }
}

#~#~#~# if output file path is valid, proceed running rest of script #~#~#~#
if ($isDstValid) {

        $outfile_subdir = ("$base_filename$(Get_Week_Filename)")
        $outfile_week_path = (Join-Path "$file_dst_parent" -ChildPath "$outfile_subdir")
        $encoding = "UTF8"

        if ($FILTER_AETs) {
            $csv_path = $outfile_week_path + "_fltr.csv"
            $xls_path = $outfile_week_path + "_fltr.xlsx"
        } else {
            $csv_path = $outfile_week_path + "_all.csv"
            $xls_path = $outfile_week_path + "_all.xlsx"
        }
        if ($PURGE_OUTPUT_CSV) {
            Purge_File $csv_path
        }

        if (Is_Excel_Installed) {
            Write-Host ("`t*xls_path: " + $xls_path)
        } else {
            Write-Host ("`t*csv_path: " + $csv_path)
        }

        Write-Host ( "`n*OPTIONS: selected*")
        Write-Host ( "`t*PURGE_OUTPUT_CSV: {0,-6}" -f $PURGE_OUTPUT_CSV.ToString().ToUpper() )
        Write-Host ( "`t*DUMP_TAGS_XMLs: {0,-6}" -f $DUMP_TAGS_XMLs.ToString().ToUpper() + "`t dumped to: '" + $file_dst_parent + "'")
        Write-Host ( "`t*FILTER_AETs: {0,-6}" -f $FILTER_AETs.ToString().ToUpper() + "`t pattern:[" + $AET_PATTERN_STR + "]`n" )

        Print_Bool_State 'VERBOSE' $VERBOSE
        Print_Bool_State 'DEBUG' $DEBUG
        Print_Bool_State 'PURGE_OUTPUT_CSV' $PURGE_OUTPUT_CSV
        Print_Bool_State 'PRINT_FILE_STATS' $PRINT_FILE_STATS
        Print_Bool_State 'PRINT_TIMER' $PRINT_TIMER

        #~#~#~# create header #~#~#~#
        $header = [string[]] ("StudyCount", "HitCount", "TransferDateTime", "InstitutionName", "PatientID", "AccessionNumber",`
        "SourceApplicationEntityTitle", "SendingApplicationEntityTitle", "ReceivingApplicationEntityTitle", "StationName",`
        "StudyDate", "Modality", "Manufacturer", "ManufacturerModelName",`
        "ImageCount", "FolderSize", "DICOMPath", "DICOMFilename")

        if (Test-Path $csv_path) {
            $last_data_row = (Get-Content $csv_path)[-1]
            $data_array = $last_data_row.Split('"') 
            $last_row_count = [int]$data_array[1] 
            $folder_count = $last_row_count
        } else {
            $folder_count = 0
        }
        
        #~#~#~# iterate through each subfolder #~#~#~#
        $folders = Get-ChildItem -Path $src_path -Directory 
        $hit_count = 0

        Write-Host ("`n {0}`t {1,-64} `t{2} `t {3}" -f "folder", "src_subdir_path", "image_count", "folder_size") -ForegroundColor DarkCyan

        foreach($sub_dir in $folders) 
        {
            $folder_count++
            $src_subdir_path = (Join-Path $src_path -ChildPath $sub_dir)
            $dump_dst_week_path = (Join-Path $dump_dst_parent -ChildPath "$base_filename$(Get_Today_Filename)_DUMPs")
            $dst_subdir_path = (Join-Path $dump_dst_week_path -ChildPath $sub_dir)

            $image_count = (Get-ChildItem -Path $src_subdir_path).count
            $folder_size = "{0:N2} MB" -f ((Get-ChildItem $src_subdir_path -Recurse | Measure-Object -Property Length -Sum -ErrorAction Stop).Sum / 1MB)

            Write-Host (" {0:D3}`t {1,-64} `t{2:D4} images `t dir:[{3}]" -f $folder_count, $src_subdir_path, $image_count, $folder_size) -ForegroundColor DarkCyan

            #~#~#~# account for spaces in file path: 'D:\subfolder\filename_with_S P A C E S.dcm' #~#~#~#
            $dcm_fullpaths = (Get-ChildItem -Path "$src_subdir_path" -Filter *.dcm -Recurse -File | Sort-Object -Property Length -Descending | %{ $_.FullName })
            
            if ($dcm_fullpaths.Length -gt 0) {
                $first_dcm_path = $dcm_fullpaths | Select-Object -First 1

                $dateCreated = (Get-Item $first_dcm_path).CreationTime
                $first_dcm_filename = [System.IO.Path]::GetFileName($first_dcm_path)
                $first_dicom_basename = [System.IO.Path]::GetFileNameWithoutExtension($first_dcm_path)
            
                #~#~#~# ensure subdirectory is created for destination #~#~#~#
                if ($EXPORT_FIRST_DCM -or $DUMP_TAGS_XMLs) {
                    if(!(Test-Path $dst_subdir_path)) {
                        $null = New-Item -ItemType Directory -Path $dst_subdir_path -Force
                    }
                }

                #~#~#~# copy single DICOM to new destination folder #~#~#~#
                if ($EXPORT_FIRST_DCM) {
                    Copy-Item -Path $first_dcm_path -Destination $dst_subdir_path
                }

                if ($isdcmtkPathValid) {
                    if ($DUMP_TAGS_XMLs) {
                        #~#~#~# Dump DICOM tags to TEXT file #~#~#~#
                        $output_txt_path = $dst_subdir_path +"\"+ $first_dicom_basename + ".txt"
                        $tag_dump_str = iex "$dcmtk_path\dcmdump.exe --ignore-parse-errors --quote-as-octal --ignore-errors --enable-correction $first_dcm_path"
                        $dump_header_str = ("{0}`t image_count: {1}`t folder_size: {2}" -f $first_dcm_path.ToString(), $image_count.ToString(), $folder_size.ToString())
                        Set-Content -Path $output_txt_path -Value $dump_header_str
                        Add-Content -Path $output_txt_path -Value $tag_dump_str

                        #~#~#~#  Convert to XML file already redirects to output file #~#~#~#  
                        $output_xml_path = "$dst_subdir_path\$first_dicom_basename.xml"
                        iex "$dcmtk_path\dcm2xml.exe '$first_dcm_path' '$output_xml_path'"
                    }

                    if ($DEBUG) {
                        Write-Host ("`t <-- first_dcm_path:  `t" + $first_dcm_path)
                        Write-Host ("`t --> dst_subdir_path: `t" + $dst_subdir_path) 
                        Start-Sleep -Seconds 2
                    }
            
                    $PatientID = Get-Dicom-Tag $first_dcm_path "PatientID"
                    $AccessionNumber = Get-Dicom-Tag $first_dcm_path "AccessionNumber"

                    $SourceApplicationEntityTitle = Get-Dicom-Tag $first_dcm_path "SourceApplicationEntityTitle"
                    $SendingApplicationEntityTitle = Get-Dicom-Tag $first_dcm_path "SendingApplicationEntityTitle"
                    $ReceivingApplicationEntityTitle = Get-Dicom-Tag $first_dcm_path "ReceivingApplicationEntityTitle"

                    $StationName = Get-Dicom-Tag $first_dcm_path "StationName"
                    $InstitutionName = Get-Dicom-Tag $first_dcm_path "InstitutionName"
                    $StudyDate = Get-Dicom-Tag $first_dcm_path "StudyDate"
                    $Modality = Get-Dicom-Tag $first_dcm_path "Modality"

                    if ($StudyDate) {
                        # DICOM dates do not have hyphens/slashes, just numbers in yyyyMMdd format
                        $SanitizedStudyDate = $StudyDate -replace '[^0-9]', ''
                        $culture = Get-Culture 
                        $StudyDateFormat = ([datetime]::ParseExact($SanitizedStudyDate,"yyyyMMdd", $culture)).toshortdatestring()
                    } else {
                        $StudyDateFormat = ""
                    }

                    $Manufacturer = Get-Dicom-Tag $first_dcm_path "Manufacturer"
                    $ManufacturerModelName = Get-Dicom-Tag $first_dcm_path "ManufacturerModelName"

                    $parsed_tag_list = [string[]]($folder_count, $hit_count, $dateCreated, $InstitutionName, $PatientID, $AccessionNumber,`
                    $SourceApplicationEntityTitle, $SendingApplicationEntityTitle, $ReceivingApplicationEntityTitle,`
                    $StationName, $StudyDateFormat, $Modality, $Manufacturer, $ManufacturerModelName, `
                    $image_count, $folder_size, $src_subdir_path, $first_dcm_filename )
            
                    $isValidAET = $True
                    if ($FILTER_AETs) {
                        $isValidAET = Verify-AET ($SendingApplicationEntityTitle)
                        #Write-Host ("`t srcAET: '" + $SendingApplicationEntityTitle +"'`t len?: " + $SendingApplicationEntityTitle.Length + " valid?: " +$isValidAET.ToString().ToUpper() +"`t hit_count: " + $hit_count  +" of " + $folder_count)
                    }

                    if ($isValidAET) {
                        #~#~#~# export tag data to CSV  #~#~#~#
                        $data = New-Object System.Object
                        $data | Add-Member -MemberType NoteProperty -Name $header[0] -Value "$folder_count"
                        #$data | Add-Member -MemberType NoteProperty -Name $header[1] -Value "$hit_count"
                        $data | Add-Member -MemberType NoteProperty -Name $header[2] -Value "$dateCreated"

                        $data | Add-Member -MemberType NoteProperty -Name $header[3] -Value "$InstitutionName"
                        $data | Add-Member -MemberType NoteProperty -Name $header[4] -Value "$PatientID"
                        $data | Add-Member -MemberType NoteProperty -Name $header[5] -Value "$AccessionNumber"
                
                        $data | Add-Member -MemberType NoteProperty -Name $header[6] -Value "$SourceApplicationEntityTitle"
                        $data | Add-Member -MemberType NoteProperty -Name $header[7] -Value "$SendingApplicationEntityTitle"
                        $data | Add-Member -MemberType NoteProperty -Name $header[8] -Value "$ReceivingApplicationEntityTitle"

                        $data | Add-Member -MemberType NoteProperty -Name $header[9] -Value "$StationName"

                        $data | Add-Member -MemberType NoteProperty -Name $header[10] -Value "$StudyDateFormat"
                        $data | Add-Member -MemberType NoteProperty -Name $header[11] -Value "$Modality"
                        $data | Add-Member -MemberType NoteProperty -Name $header[12] -Value "$Manufacturer"
                        $data | Add-Member -MemberType NoteProperty -Name $header[13] -Value "$ManufacturerModelName"

                        $data | Add-Member -MemberType NoteProperty -Name $header[14] -Value "$image_count"
                        $data | Add-Member -MemberType NoteProperty -Name $header[15] -Value "$folder_size"
                        $data | Add-Member -MemberType NoteProperty -Name $header[16] -Value "$src_subdir_path"
                        $data | Add-Member -MemberType NoteProperty -Name $header[17] -Value "$first_dcm_filename"

                        #~#~#~# append new data to .csv file #~#~#~#
                        $data | Export-Csv -Path $csv_path -Encoding $encoding -delimiter $delimiter -NoTypeInformation -Append -Force
                        $hit_count++
                    }
                }
            }
        }
        #~#~#~# export to excel and auto-format #~#~#~#
    If (Is_Excel_Installed) {

        #~#~#~# export to excel and auto-format #~#~#~#
        if (Test-Path $csv_path) {
            $xls = New-Object -ComObject Excel.Application
            $xls.Visible = $False
            
            try {
                $undef = [Type]::Missing
                $workbook = $xls.Workbooks.Open($csv_path, $undef, $undef, 6, $undef, $undef, $undef, $undef, $delimiter)
                
                # workbook=Excel_file, worksheet=tab, range=2+_cells in sheet, 
                $enum_query_type = 1   # 0=external_src, 1=range, 2=xml, 3=query, 4=pivot
                $link_source = $False
                $enum_has_headers = 0  # 0=guess, 1=no-sort, 2=default-sort
                $worksheet = $workbook.ActiveSheet.ListObjects.add($enum_query_type,$workbook.ActiveSheet.UsedRange,$link_source,$enum_has_headers)

                $worksheet.Application.ActiveWindow.SplitRow = 1
                $worksheet.Application.ActiveWindow.FreezePanes = $True
                $xls.DisplayAlerts=$False

                $xls_center=-4108
                $xls.Rows.HorizontalAlignment = $xls_center

                #~#~#~# dynamically find columns of interest #~#~#~#
                $folder_col = $xls.Columns.find("StudyCount").Column
                $mrn_col = $xls.Columns.find("PatientID").Column
                $acc_col = $xls.Columns.find("AccessionNumber").Column
                $images_col = $xls.Columns.find("ImageCount").Column

                # A:number     B:timestamp         D:number,    E:number        N:number       J:date-only
                # StudyCount   TransferDateTime    PatientID    AccessionNumber ImageCount     StudyDate 
                $xls.Columns.item($folder_col).NumberFormat = "0"   # StudyCount
                $xls.Columns.item($mrn_col).NumberFormat = "0"      # PatientID
                $xls.Columns.item($acc_col).NumberFormat = "0"      # AccessionNumber
                $xls.Columns.item($images_col).NumberFormat = "0"   # ImageCount
                                            
                $null = $xls.ActiveSheet.UsedRange.EntireColumn.AutoFit()
                $xls_lsx_type = 51        # Open XML Workbook *.xlsx
                $workbook.SaveAs($xls_path, $xls_lsx_type)
                
            } catch {
                $ErrorMessage = $_.Exception.Message
                Write-Warning -Message ("~!*ERROR*!~ {0}" -f $ErrorMessage)
            } finally {     
                $xls.Workbooks.Close()
                $xls.Quit()
            }
         } else {
                Write-Warning -Message ("~!*ERROR*!~ '{0}' not found..." -f $csv_path)
         }
         Write-Host ("SUCCESS! {0}" -f $xls_path) -ForegroundColor DarkGreen
    }
}

$transfer_count_str = ("`n{0} tranfers logged of {1} total studies `t[FILTER_AETs: {2}]" -f $hit_count, $folder_count, $FILTER_AETs.ToString().ToUpper() )
Write-Host ($transfer_count_str)

$title_str = ("finished running on '{0}'" -f $server_name)
Stop_Print_Timer $benchmark $title_str
