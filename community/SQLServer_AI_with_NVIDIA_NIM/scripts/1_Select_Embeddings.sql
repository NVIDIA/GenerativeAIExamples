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

-- Output columns in this exact order:
-- ProductID, ProductDescriptionID, ProductModelID, CultureID, Embedding, Embed_E5_ACA, Description, ModifiedDate
-- If Embed_E5_ACA doesn't exist yet, return NULL AS [Embed_E5_ACA].

DECLARE @hasEmbedE5ACA bit =
  CASE WHEN COL_LENGTH('Production.ProductDescriptionEmbeddings','Embed_E5_ACA') IS NOT NULL
       THEN 1 ELSE 0 END;

DECLARE @where nvarchar(max) =
  CASE WHEN @hasEmbedE5ACA = 1
       THEN N'(pde.Embedding IS NOT NULL OR pde.Embed_E5_ACA IS NOT NULL)'
       ELSE N'pde.Embedding IS NOT NULL'
  END;

DECLARE @sql nvarchar(max) =
N';WITH RankedEmbeddings AS (
    SELECT
        pde.ProductID,
        pde.ProductDescriptionID,
        pde.ProductModelID,
        pde.CultureID,
        pde.Embedding' + CASE WHEN @hasEmbedE5ACA = 1 THEN N', pde.Embed_E5_ACA' ELSE N'' END + N',
        pd.Description,
        pde.ModifiedDate,
        ROW_NUMBER() OVER (PARTITION BY pde.ProductDescriptionID ORDER BY pde.ProductID) AS rn
    FROM Production.ProductDescriptionEmbeddings AS pde
    JOIN Production.ProductDescription AS pd
      ON pd.ProductDescriptionID = pde.ProductDescriptionID
    WHERE ' + @where + N'
)
SELECT
    RE.ProductID,
    RE.ProductDescriptionID,
    RE.ProductModelID,
    RE.CultureID,
    RE.Embedding,
    ' + CASE WHEN @hasEmbedE5ACA = 1
             THEN N'RE.Embed_E5_ACA'
             ELSE N'NULL AS [Embed_E5_ACA]'
        END + N',
    RE.Description,
    RE.ModifiedDate
FROM RankedEmbeddings AS RE
WHERE rn = 1
ORDER BY RE.ProductDescriptionID;';

EXEC sp_executesql @sql;




