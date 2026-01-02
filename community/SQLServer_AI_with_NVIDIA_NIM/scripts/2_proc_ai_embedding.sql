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

SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

CREATE OR ALTER PROCEDURE dbo.nvidia_run_ai_embedding
    @ModelName   NVARCHAR(255),                  -- e.g., 'EmbedE5_OpenAI'
    @TopN        INT            = 10,            -- one-shot batch count (ignored if @ProcessAll=1)
    @Prompt      NVARCHAR(MAX)  = NULL,          -- query mode when provided
    @OutVector   VECTOR(1024)   OUTPUT,          -- returns embedding in query mode
    @ProcessAll  BIT            = 0,             -- set 1 to sweep entire table
    @BatchSize   INT            = 1000           -- chunk size when sweeping
WITH EXECUTE AS OWNER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @sql NVARCHAR(MAX);          -- declare ONCE and reuse
    DECLARE @rows INT;

    ---------------------------------------------------------------------
    -- MODE A: Single-query embedding (acts like get_embedding)
    -- Ensure external model has PARAMETERS: {"input_type":"query","dimensions":1024}
    ---------------------------------------------------------------------
    IF @Prompt IS NOT NULL
    BEGIN
        DECLARE @emb VECTOR(1024);

        SET @sql = N'
            SELECT @embOut = AI_GENERATE_EMBEDDINGS(@p USE MODEL ' + QUOTENAME(@ModelName) + N');
        ';

        EXEC sp_executesql
             @sql,
             N'@p NVARCHAR(MAX), @embOut VECTOR(1024) OUTPUT',
             @p = @Prompt,
             @embOut = @emb OUTPUT;

        IF @emb IS NULL RETURN 1;

        SET @OutVector = @emb;
        RETURN 0; -- do NOT touch the table when prompt mode
    END;

    ---------------------------------------------------------------------
    -- MODE B1: Sweep entire table in batches
    ---------------------------------------------------------------------
    IF @ProcessAll = 1
    BEGIN
        SET @rows = 1;

        WHILE (@rows > 0)
        BEGIN
            -- unique temp tables for this branch
            IF OBJECT_ID('tempdb..#TargetIdsAll') IS NOT NULL DROP TABLE #TargetIdsAll;
            CREATE TABLE #TargetIdsAll (ProductDescriptionID INT PRIMARY KEY);

            INSERT INTO #TargetIdsAll (ProductDescriptionID)
            SELECT TOP (@BatchSize) pde.ProductDescriptionID
            FROM Production.ProductDescriptionEmbeddings AS pde
            WHERE pde.Embedding IS NULL
            GROUP BY pde.ProductDescriptionID
            ORDER BY pde.ProductDescriptionID;

            IF NOT EXISTS (SELECT 1 FROM #TargetIdsAll) BREAK;

            IF OBJECT_ID('tempdb..#TouchedAll') IS NOT NULL DROP TABLE #TouchedAll;
            CREATE TABLE #TouchedAll (ProductDescriptionID INT);

            SET @sql = N'
            ;WITH NullRows AS (
                SELECT  pde.ProductDescriptionID,
                        pd.Description
                FROM Production.ProductDescriptionEmbeddings AS pde
                JOIN #TargetIdsAll AS t
                  ON t.ProductDescriptionID = pde.ProductDescriptionID
                JOIN Production.ProductDescription AS pd
                  ON pd.ProductDescriptionID = pde.ProductDescriptionID
                WHERE pde.Embedding IS NULL
            ),
            NewVecs AS (
                SELECT
                    n.ProductDescriptionID,
                    AI_GENERATE_EMBEDDINGS(n.Description USE MODEL ' + QUOTENAME(@ModelName) + N') AS NewEmbedding
                FROM NullRows AS n
            )
            UPDATE pde
               SET pde.Embedding    = nv.NewEmbedding,
                   pde.ModifiedDate = GETDATE()
               OUTPUT inserted.ProductDescriptionID INTO #TouchedAll(ProductDescriptionID)
            FROM Production.ProductDescriptionEmbeddings AS pde
            JOIN NewVecs AS nv
              ON nv.ProductDescriptionID = pde.ProductDescriptionID
            WHERE pde.Embedding IS NULL
              AND nv.NewEmbedding IS NOT NULL
            OPTION (MAXDOP 1);';

            EXEC sp_executesql @sql;

            SELECT @rows = COUNT(*) FROM #TouchedAll;
        END;

        SELECT 'ProcessedAll' AS Mode, @BatchSize AS BatchSize;
        RETURN 0;
    END;

    ---------------------------------------------------------------------
    -- MODE B2: One-shot batch (TOP @TopN)
    ---------------------------------------------------------------------
    -- unique temp tables for this branch
    IF OBJECT_ID('tempdb..#TargetIdsOnce') IS NOT NULL DROP TABLE #TargetIdsOnce;
    CREATE TABLE #TargetIdsOnce (ProductDescriptionID INT PRIMARY KEY);

    INSERT INTO #TargetIdsOnce (ProductDescriptionID)
    SELECT TOP (@TopN) pde.ProductDescriptionID
    FROM Production.ProductDescriptionEmbeddings AS pde
    WHERE pde.Embedding IS NULL
    GROUP BY pde.ProductDescriptionID
    ORDER BY pde.ProductDescriptionID;

    IF OBJECT_ID('tempdb..#TouchedOnce') IS NOT NULL DROP TABLE #TouchedOnce;
    CREATE TABLE #TouchedOnce (ProductDescriptionID INT);

    SET @sql = N'
    ;WITH NullRows AS (
        SELECT  pde.ProductDescriptionID,
                pd.Description
        FROM Production.ProductDescriptionEmbeddings AS pde
        JOIN #TargetIdsOnce AS t
          ON t.ProductDescriptionID = pde.ProductDescriptionID
        JOIN Production.ProductDescription AS pd
          ON pd.ProductDescriptionID = pde.ProductDescriptionID
        WHERE pde.Embedding IS NULL
    ),
    NewVecs AS (
        SELECT
            n.ProductDescriptionID,
            AI_GENERATE_EMBEDDINGS(n.Description USE MODEL ' + QUOTENAME(@ModelName) + N') AS NewEmbedding
        FROM NullRows AS n
    )
    UPDATE pde
       SET pde.Embedding    = nv.NewEmbedding,
           pde.ModifiedDate = GETDATE()
       OUTPUT inserted.ProductDescriptionID INTO #TouchedOnce(ProductDescriptionID)
    FROM Production.ProductDescriptionEmbeddings AS pde
    JOIN NewVecs AS nv
      ON nv.ProductDescriptionID = pde.ProductDescriptionID
    WHERE pde.Embedding IS NULL
      AND nv.NewEmbedding IS NOT NULL
    OPTION (MAXDOP 1);';

    EXEC sp_executesql @sql;

    SELECT DISTINCT ProductDescriptionID FROM #TouchedOnce;
    RETURN 0;
END;
GO


