USE [Compass2]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[institution_to_aet_mapping](
	[id] [uniqueidentifier] NOT NULL DEFAULT NEWSEQUENTIALID(),
	[calling_aet] [varchar](24) NULL,
    [source_ip_addr] [nvarchar](15) NULL,
	[institution_name] [varchar](128) NULL,
 CONSTRAINT [PK_institution_aet_mapping] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO;

