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

CREATE OR ALTER PROCEDURE dbo.nvidia_run_ai_embedding
    @ModelName NVARCHAR(255),                      -- Pass the model name dynamically, e.g., 'EmbedE5_OpenAI'
    @TopN INT = 10                                 -- Limit how many rows to process
WITH EXECUTE AS OWNER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    ---------------------------------------------------------------------
    -- Step 2: Choose target ProductDescriptionIDs to process in this run
    ---------------------------------------------------------------------
    IF OBJECT_ID('tempdb..#TargetIds') IS NOT NULL DROP TABLE #TargetIds;
    CREATE TABLE #TargetIds (ProductDescriptionID INT PRIMARY KEY);

    INSERT INTO #TargetIds (ProductDescriptionID)
    SELECT TOP (@TopN) pde.ProductDescriptionID
    FROM Production.ProductDescriptionEmbeddings AS pde
    WHERE pde.Embedding IS NULL
    GROUP BY pde.ProductDescriptionID
    ORDER BY pde.ProductDescriptionID;

    ---------------------------------------------------------------------
    -- Step 3: Compute embeddings using AI_GENERATE_EMBEDDINGS and update
    ---------------------------------------------------------------------
    IF OBJECT_ID('tempdb..#Touched') IS NOT NULL DROP TABLE #Touched;
    CREATE TABLE #Touched (ProductDescriptionID INT);

    -- Build dynamic SQL for embedding generation
    DECLARE @DynamicSQL NVARCHAR(MAX);
    SET @DynamicSQL = N'
    ;WITH NullRows AS (
        SELECT  pde.ProductDescriptionID,
                pd.Description
        FROM Production.ProductDescriptionEmbeddings AS pde
        JOIN #TargetIds AS t
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
       OUTPUT inserted.ProductDescriptionID INTO #Touched(ProductDescriptionID)
    FROM Production.ProductDescriptionEmbeddings AS pde
    JOIN NewVecs AS nv
      ON nv.ProductDescriptionID = pde.ProductDescriptionID
    WHERE pde.Embedding IS NULL
      AND nv.NewEmbedding IS NOT NULL
    OPTION (MAXDOP 1);';

    -- Execute the dynamic SQL
    EXEC sp_executesql @DynamicSQL;

    -- Step 4: Return the IDs of the rows that were updated
    SELECT DISTINCT ProductDescriptionID FROM #Touched;
END;

GO
