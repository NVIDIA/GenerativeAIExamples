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

USE [AdventureWorks]
GO
/****** Object:  StoredProcedure [dbo].[nvidia_run_proc_embedding]    Script Date: 11/11/2025 2:13:02 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER   PROCEDURE [dbo].[nvidia_run_proc_embedding]
    @ModelName         NVARCHAR(255),
    @VectorSize        INT,
    @VectorColumnName  SYSNAME,      -- e.g., N'Embed_E5_ACA'
    @Url               NVARCHAR(512),
    @MaxRows           INT = 10       -- counts UNIQUE ProductDescriptionID values
AS
BEGIN
    SET NOCOUNT ON;

    -- Ensure target vector column exists
    IF NOT EXISTS (
        SELECT 1 FROM sys.columns
        WHERE object_id = OBJECT_ID('Production.ProductDescriptionEmbeddings')
          AND name = @VectorColumnName
    )
    BEGIN
        DECLARE @AlterSql NVARCHAR(MAX) =
            N'ALTER TABLE Production.ProductDescriptionEmbeddings ' +
            N'ADD ' + QUOTENAME(@VectorColumnName) + N' VECTOR(' + CAST(@VectorSize AS NVARCHAR(10)) + N')';
        EXEC sp_executesql @AlterSql;
    END;

    -- Ensure ModifiedDate exists
    IF NOT EXISTS (
        SELECT 1 FROM sys.columns
        WHERE object_id = OBJECT_ID('Production.ProductDescriptionEmbeddings')
          AND name = 'ModifiedDate'
    )
    BEGIN
        EXEC(N'ALTER TABLE Production.ProductDescriptionEmbeddings
              ADD ModifiedDate DATETIME NOT NULL
                  CONSTRAINT DF_ProductDescriptionEmbeddings_ModifiedDate
                  DEFAULT (GETDATE()) WITH VALUES;');
    END;

    -- Pick @MaxRows unique ProductDescriptionIDs whose chosen vector is NULL
    IF OBJECT_ID('tempdb..#TargetIds') IS NOT NULL DROP TABLE #TargetIds;
    CREATE TABLE #TargetIds (ProductDescriptionID INT PRIMARY KEY);

    DECLARE @PickIdsSql NVARCHAR(MAX) = N'
        INSERT INTO #TargetIds(ProductDescriptionID)
        SELECT TOP (@TopN) pde.ProductDescriptionID
        FROM Production.ProductDescriptionEmbeddings AS pde
        WHERE pde.' + QUOTENAME(@VectorColumnName) + N' IS NULL
        GROUP BY pde.ProductDescriptionID
        ORDER BY pde.ProductDescriptionID;';

    DECLARE @TopN INT = @MaxRows;

    EXEC sp_executesql @PickIdsSql, N'@TopN INT', @TopN = @TopN;

    -- Build one row per PDID with its Description
    IF OBJECT_ID('tempdb..#ToEmbed') IS NOT NULL DROP TABLE #ToEmbed;
    CREATE TABLE #ToEmbed (ProductDescriptionID INT PRIMARY KEY, Description NVARCHAR(MAX));

    INSERT INTO #ToEmbed(ProductDescriptionID, Description)
    SELECT t.ProductDescriptionID, pd.Description
    FROM #TargetIds AS t
    JOIN Production.ProductDescription AS pd
      ON pd.ProductDescriptionID = t.ProductDescriptionID;

    -- REST call + update
    DECLARE @Headers  NVARCHAR(MAX) = N'{"Content-Type":"application/json","Accept":"application/json"}';
    DECLARE @Payload  NVARCHAR(MAX), @Response NVARCHAR(MAX);
    DECLARE @Retval   INT, @PDID INT, @Text NVARCHAR(MAX), @EmbArray NVARCHAR(MAX);

    DECLARE cur CURSOR LOCAL FAST_FORWARD FOR
        SELECT ProductDescriptionID, Description FROM #ToEmbed ORDER BY ProductDescriptionID;
    OPEN cur; FETCH NEXT FROM cur INTO @PDID, @Text;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        -- description text => input_type "passage"
        DECLARE @Escaped NVARCHAR(MAX) = '"' + REPLACE(@Text, '"', '\"') + '"';
        SET @Payload = N'{
            "input": [' + @Escaped + N'],
            "model": "' + @ModelName + N'",
            "input_type": "query",
            "dimensions": 1024
        }';

        ---------------------------------------------------------------------------------
        -- Use SP_INVOKE_EXTERNAL_REST_ENDPOINT
        EXEC @Retval = sys.sp_invoke_external_rest_endpoint
             @url      = @Url,
             @method   = N'POST',
             @headers  = @Headers,
             @payload  = @Payload,
             @response = @Response OUTPUT;

        ---------------------------------------------------------------------------------

        IF (@Retval = 0)
        BEGIN
            -- accept both shapes: {"data":[...]} or {"result":{"data":[...]}}
            SET @EmbArray = COALESCE(
                JSON_QUERY(@Response, '$.data[0].embedding'),
                JSON_QUERY(@Response, '$.result.data[0].embedding')
            );

            IF @EmbArray IS NOT NULL
               AND (SELECT COUNT(*) FROM OPENJSON(@EmbArray)) = @VectorSize
            BEGIN
                DECLARE @UpdateSql NVARCHAR(MAX) = N'
                    UPDATE pde
                    SET ' + QUOTENAME(@VectorColumnName) + N' = TRY_CAST(@Emb AS VECTOR(' + CAST(@VectorSize AS NVARCHAR(10)) + N')),
                        ModifiedDate = GETDATE()
                    FROM Production.ProductDescriptionEmbeddings AS pde
                    WHERE pde.ProductDescriptionID = @PDID
                      AND pde.' + QUOTENAME(@VectorColumnName) + N' IS NULL;';

                EXEC sp_executesql @UpdateSql,
                     N'@Emb NVARCHAR(MAX), @PDID INT',
                     @Emb = @EmbArray, @PDID = @PDID;
            END
        END

        FETCH NEXT FROM cur INTO @PDID, @Text;
    END
    CLOSE cur; DEALLOCATE cur;
END
