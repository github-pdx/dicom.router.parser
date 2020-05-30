<#  
PS script to connect to Compass database and extract external transfers
#>
$author = "github.pdx"
$email = "dicom.pdx@runbox.com"
$status = "Testing on PHODICOMRTRTST PS v4.0 to v5.1"
$version = "1.1.2"
$ps_version = $PSVersionTable.PSVersion
$script_name = $MyInvocation.MyCommand.Name 

<# 
Sources: 
https://stackoverflow.com/questions/29139058/import-data-from-sql-server-database-to-csv-using-powershell
https://www.sqlshack.com/connecting-powershell-to-sql-server/
https://mcpmag.com/articles/2018/12/10/test-sql-connection-with-powershell.aspx
https://github.com/Tervis-Tumbler/InvokeSQL
https://blog.netnerds.net/2015/02/working-with-basic-net-datasets-in-powershell/
#> 

$root_dir = $PSScriptRoot
$base_filename = "PH_IMG_RTR"

#~#~#~# DB CONFIG: #~#~#~#  COMPASS_USER_MAPPING RUN_USER_RUN SERVER_ROLE_SA
#PHODICOMRTRTST\SQLEXPRESS
$server_name = $env:ComputerName
$db_name = 'Compass2'
$username = 'SERVER_ROLE_SA'
$password = 'dicom.router' 

$connectionString = 'Data Source={0};Database={1};User ID={2};Password={3}' -f $server_name, $db_name, $username, $password

#~#~#~# OPTIONS: #~#~#~# 
$DEBUG = $False
$PRINT_TIMER = $True
$PURGE_CSV_FILE = $False
$delimiter = ","

function Start_Timer () {
    [OutputType([System.Diagnostics.Stopwatch])]
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    return $timer 
}

function Stop_Print_Timer ([System.Diagnostics.Stopwatch] $input_timer, [String] $input_title='default_title' ) {
    $input_timer.Stop()
    if ($PRINT_TIMER) {
        $elapsed_time = [TimeSpan]$input_timer.Elapsed
        $formatTime = Format_Elapsed_Time $elapsed_time
        Write-Host (" '{0,-24}' {1,-24} runtime: {2}" -f $script_name, $input_title, $formatTime) -ForegroundColor DarkCyan
    }
}

$benchmark = Start_Timer

function Get_TimeStamp {  
    return "{0:MM/dd/yy} {0:HH:mm:ss}" -f (Get-Date)
}

function Get_Month_Filename {  
    return "_{0:MM-yyyy}" -f (Get-Date)
}

function Get_Week_Filename { 
    $month_str = "{0:MM-yyyy}" -f (Get-Date)
    $week_num = (Get-Date -UFormat %V)
    $week_str = "week$week_num"
    return "_$month_str.$week_str"
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

function Create_Directory ( [string]$input_dirpath='default_path' ) {
    if(!(Test-Path "$input_dirpath")) {
        try {
            $null = New-Item -ItemType Directory -Path $input_dirpath -Force
        } catch {
            $ErrorMessage = $_.Exception.Message
            Write-Warning -Message ("~!*ERROR*!~ {0}" -f $ErrorMessage)
        }                   
    }
}

function Format_Elapsed_Time( [TimeSpan]$ts ) {
    [OutputType([string])]
    $elapsedTime = ""
    if ( $ts.Minutes -gt 0 ) {
        $elapsedTime = [string]::Format( "{0:00} min. {1:00}.{2:00} sec.", $ts.Minutes, $ts.Seconds, $ts.Milliseconds / 10 );
    }
    else {
        $elapsedTime = [string]::Format( "{0:00}.{1:00} sec.", $ts.Seconds, $ts.Milliseconds / 10 );
    }
    if ($ts.Hours -eq 0 -and $ts.Minutes -eq 0 -and $ts.Seconds -eq 0) {
        $elapsedTime = [string]::Format("{0:00} ms.", $ts.Milliseconds);
    }
    if ($ts.Milliseconds -eq 0) {
        $elapsedTime = [string]::Format("{0} ms", $ts.TotalMilliseconds);
    }
    return $elapsedTime
}

function Get_Delimiter_Name ( [int][char]$delim_str_to_ascii ) {
    [OutputType([string])]
    $delimiter_name = ''
    switch ($delim_str_to_ascii) {
            9    { $delimiter_name = 'tab' }
            32   { $delimiter_name = 'space' }
            44   { $delimiter_name = 'comma' }
            45   { $delimiter_name = 'hyphen' }
            46   { $delimiter_name = 'period' }
            58   { $delimiter_name = 'colon' }
            59   { $delimiter_name = 'semicolon' }
            94   { $delimiter_name = 'caret' }
            95   { $delimiter_name = 'underscore' }
            124  { $delimiter_name = 'pipe' }
            126  { $delimiter_name = 'tilde' }
    }
    if ($DEBUG) {
        Write-Host ("'{0}' {1}" -f $delim_str_to_ascii, $delimiter_name)
    }
    return $delimiter_name
}

$dst_parent_path = "D:\PH_IMG_RTR_TX_LOGS"
$dst_path = (Join-Path "$dst_parent_path" -ChildPath "$base_filename$(Get_Month_Filename)_SQLs")
$dst_drive_name = Split-Path -Path $dst_parent_path -Qualifier

Write-Host ("'{0}' v:{1} running PSversion:{2} on {3}" -f $script_name, $version, $ps_version, $server_name) -ForegroundColor Gray
Write-Host ("dst_path: " + $dst_path) -ForegroundColor Gray

$isDstValid = is_Path_Valid "dst_drive_name" $dst_drive_name
Create_Directory $dst_path
#$VerbosePreference = "SilentlyContinue"


function Print_Query_State ( [string]$input_title='default_title', [string]$input_status='default_status' ) {
    if ($input_status -eq "SUCCESS") {
        Write-Host ("{0,-8} {1}" -f $input_title, $input_status ) -ForegroundColor DarkGreen
    } else {
        Write-Host ("{0,-8} {1}" -f $input_title, $input_status ) -ForegroundColor Red
    }
}

function Perform_Query {
    [OutputType([PSCustomObject])]
    param(
        [Parameter(Mandatory)]
        [string] $input_query
    )
    $ErrorActionPreference = 'Stop'
    $obj = New-Object System.Object
    try {
        $sqlConnection = New-Object System.Data.SqlClient.SqlConnection $connectionString
        $sqlConnection.Open()
        Write-Host ("SQL Connection: '{0}' {1}" -f $sqlConnection.State, $sqlConnection.ConnectionString)
             
        $sqlcmd = $sqlConnection.CreateCommand()
        $sqlcmd = New-Object System.Data.SqlClient.SqlCommand
        $sqlcmd.Connection = $sqlConnection
        $sqlcmd.CommandTimeout = 1
        $sqlcmd.CommandText = $input_query
        $data_table = New-Object Data.Datatable

        if ($input_query) {
            #Write-Warning -Message ($input_query)
            $adapter = New-Object System.Data.SqlClient.SqlDataAdapter $sqlcmd
            $dataset = New-Object System.Data.DataSet
            if ($adapter) {
                $result_count = $adapter.Fill($dataset) 
                $data_table = $dataset.tables[0]
            }
            $obj | Add-Member -MemberType NoteProperty -Name count -Value $result_count
            $obj | Add-Member -MemberType NoteProperty -Name table -Value $data_table
            $obj | Add-Member -MemberType NoteProperty -Name status -Value "SUCCESS"
            return $obj
        }
    } catch {
        $ErrorMessage = $_.Exception.Message
        Write-Warning -Message ("~!*ERROR*!~ {0}" -f $ErrorMessage)
        Write-Warning ("SQL Connection: '{0}' {1}" -f $sqlConnection.State, $sqlConnection.ConnectionString)
        $obj | Add-Member -MemberType NoteProperty -Name count -Value "0"
        $obj | Add-Member -MemberType NoteProperty -Name table -Value "empty"
        $obj | Add-Member -MemberType NoteProperty -Name status -Value "FAILURE"
        return $obj
    } finally {
        $sqlConnection.Close()
    }
}


function Query_Outside_Transfers {
    [OutputType([string])]
    $outside_query = "
	(SELECT ROW_NUMBER() OVER (ORDER BY J.source_calling_ae) as 'StudyCount',
	CONVERT(VARCHAR, J.[createdTime], 22) as 'TransferDateTime',

	J.[patient_id] as 'PatientID',
	J.[accessionNumber] as 'AccessionNumber',
	A.[source] as 'SourceAET',
	A.[called] as 'CalledAET',
	A.[calling] as 'CallingAET',
  
	(SELECT INA.[institution_name] FROM [Compass2].[dbo].[institution_to_aet_mapping] INA WHERE J.source_calling_ae = INA.calling_aet ) as 'InstitutionName',
  
	J.[source_ip_addr] as 'SourceIPAddr',
	J.[matched_rules] as 'MatchingRule',
	J.[destination_name] as 'DestinationName',

	CONVERT(VARCHAR, J.[studyDate], 101) as 'StudyDate',
	LTRIM(RTRIM(J.[modalities])) as 'Modality', 
	(SELECT COUNT(I.[id])) as 'ImageCount',

	J.[id] as 'JobId',
	REPLACE(I.[assocId], '-','') as 'FolderName'

	FROM [Compass2].[dbo].[jobs] J 
	JOIN [Compass2].[dbo].[img_job_assoc] IJA ON J.id = IJA.job_pk
	JOIN [Compass2].[dbo].[images] I ON I.id = IJA.image_pk
	JOIN [Compass2].[dbo].[association] A ON A.id = I.assocId
	WHERE
	[source_calling_ae] NOT LIKE '%PHPACS'
	GROUP BY J.[id], J.[createdTime], J.[patient_id], J.[accessionNumber], A.[source], A.[called], A.[calling], J.[studyDate], J.[modalities], J.[source_called_ae], J.[source_calling_ae], J.[source_ip_addr], J.[matched_rules], J.[destination_name], I.[assocId]
	);
    "
    return $outside_query 
}

#$isConnectionOpen = Test_Sql_Connection -Server $server_name -Database $db_name -Username $username -Password $password
if ($isDstValid) {
    $query = Query_Outside_Transfers
    if ($DUBUG) {
        Write-Host($query)
    }
    $result_obj = Perform_Query $query
    #~#~#~# append new data to .csv file #~#~#~#
    if ($result_obj.status -eq "SUCCESS") {
        if (Test-Path $dst_path) {
            try {
                $delimiter_name = Get_Delimiter_Name $delimiter
                $csv_path = $dst_path + "\$base_filename$(Get_Week_Filename)_SQL_$delimiter_name.csv"
                if ($PURGE_CSV_FILE) {
                    Purge_File $csv_path
                }
                if ($result_obj.count -eq 0) {
                    Write-Warning -Message ("...database tables are empty" )
                }
                if ($result_obj.count -gt 0) {
                    $result_obj.table | Export-Csv -Path $csv_path -delimiter $delimiter -NoTypeInformation -Append -Force
                    $headers = (Get-Content $csv_path | Select-Object -First 1).Split($delimiter)

                    $first_col = [string]$headers.Item(0)
                    if ("$first_col" -like "*System.Data.DataRow*") {
                        # remove 1st row: '#TYPE System.Data.DataRow'
                        $no_type_data = Get-Content -Path $csv_path | Select-Object -Skip 1 
                        Set-Content -Path $csv_path -Value $no_type_data
                        Write-Host("Note: removed 1st row: '#TYPE System.Data.DataRow'" ) -ForegroundColor Gray
                    } 
                }
            } catch {
                $ErrorMessage = $_.Exception.Message
                Write-Warning -Message ("~!*ERROR*!~ $ErrorMessage $FailedItem" )
            }
            if (Test-Path $csv_path) {
                $prior_count = (Get-Content $csv_path | Measure-Object -Line)
                Write-Host ("result_set: {0} rows added for {1} entries total" -f $result_obj.count, $prior_count.Lines)
            }
        } #dst_path
    } #result_obj.status
    Print_Query_State "query:" $result_obj.status
} #isDstValid

$title_str = ("finished running on '{0}'" -f $server_name)
Stop_Print_Timer $benchmark $title_str
