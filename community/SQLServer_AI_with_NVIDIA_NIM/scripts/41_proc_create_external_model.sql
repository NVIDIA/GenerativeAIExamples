CREATE OR ALTER PROCEDURE dbo.CreateExternalModel
    @Location NVARCHAR(512),  -- The endpoint URL for the external model
    @Model NVARCHAR(255),     -- The name of the model to use
    @Name SYSNAME             -- The name of the external model to create
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
        LOCATION = ''' + REPLACE(@Location, '''', '''''') + N''',
        API_FORMAT = ''OpenAI'',
        MODEL_TYPE = EMBEDDINGS,
        MODEL = ''' + REPLACE(@Model, '''', '''''') + N'''
    );';

    -- Execute the dynamic SQL to create the external model
    EXEC sp_executesql @CreateSql;

    -- Return a success message
    PRINT 'External model [' + @Name + '] has been created successfully.';
END;
GO