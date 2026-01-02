/*
 Copyright (c) 2025, NVIDIA CORPORATION.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 */

/****** Object:  StoredProcedure [dbo].[CreateExternalModel]    Script Date: 11/7/2025 12:20:24 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER   PROCEDURE [dbo].[CreateExternalModel]
    @Location NVARCHAR(512),  -- The endpoint URL for the external model
    @Model NVARCHAR(255),     -- The name of the model to use
    @Name SYSNAME,             -- The name of the external model to create
    @SchemaName   SYSNAME       = N'dbo',   -- Schema for the external model
    @ApiFormat    NVARCHAR(50)  = N'OpenAI',-- API_FORMAT
    @ModelType    NVARCHAR(32)  = N'EMBEDDINGS', -- MODEL_TYPE (EMBEDDINGS for /embeddings)
    @Parameters   NVARCHAR(MAX) = N'{"input_type":"query","dimensions":1024}' -- extra POST fields

AS
BEGIN
    SET NOCOUNT ON;

    -- Generate the quoted model name for use in dynamic SQL
    DECLARE @QuotedName SYSNAME = QUOTENAME(@Name);

    -- Check if the model already exists
    IF EXISTS (SELECT 1 FROM sys.external_models WHERE name = @Name)
    BEGIN
        -- Drop the existing model
        DECLARE @DropSql NVARCHAR(MAX);
        SET @DropSql = N'DROP EXTERNAL MODEL ' + @QuotedName + N';';
        EXEC sp_executesql @DropSql;
    END;

    -- Create the external model
    DECLARE @CreateSql NVARCHAR(MAX);
    SET @CreateSql = N'CREATE EXTERNAL MODEL ' + @QuotedName + N'
    WITH (
        LOCATION    = N''' + REPLACE(@Location,  '''', '''''') + N''',
        API_FORMAT  = '''  + REPLACE(@ApiFormat, '''', '''''') + N''',
        MODEL_TYPE  = '    + @ModelType + N',
        MODEL       = N''' + REPLACE(@Model,     '''', '''''') + N''',
        PARAMETERS  = N''' + REPLACE(COALESCE(@Parameters, N'{}'), '''', '''''') + N'''
    );';

    -- Execute the dynamic SQL to create the external model
    EXEC sp_executesql @CreateSql;

    -- Return a success message
    PRINT 'External model [' + @Name + '] has been created successfully.';
END;
