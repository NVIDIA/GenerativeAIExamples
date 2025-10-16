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



