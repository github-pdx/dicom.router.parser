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