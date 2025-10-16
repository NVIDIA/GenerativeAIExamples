DROP TABLE IF EXISTS Production.ProductDescriptionEmbeddings;
GO

CREATE TABLE Production.ProductDescriptionEmbeddings
(
  ProductID            INT         NOT NULL,
  ProductDescriptionID INT         NOT NULL,
  ProductModelID       INT         NOT NULL,
  CultureID            NCHAR(6)    NOT NULL,
  Embedding            VECTOR(1024)    NULL,        -- 1024-d model
  ModifiedDate         DATETIME    NOT NULL
      CONSTRAINT DF_ProductDescriptionEmbeddings_ModifiedDate DEFAULT (GETDATE())
);

-- Populate rows without embeddings (ModifiedDate auto-fills via DEFAULT)
INSERT INTO Production.ProductDescriptionEmbeddings
( ProductID, ProductDescriptionID, ProductModelID, CultureID, Embedding )
SELECT p.ProductID, pmpdc.ProductDescriptionID, pmpdc.ProductModelID, pmpdc.CultureID, NULL
FROM Production.ProductModelProductDescriptionCulture AS pmpdc
JOIN Production.Product AS p
  ON pmpdc.ProductModelID = p.ProductModelID
ORDER BY p.ProductID;
GO

-- Keep your clustered PK as-is
ALTER TABLE Production.ProductDescriptionEmbeddings
ADD CONSTRAINT PK_ProductDescriptionEmbeddings
PRIMARY KEY CLUSTERED
( ProductID ASC, ProductModelID ASC, ProductDescriptionID ASC, CultureID ASC );
GO

-- Same helpful nonclustered indexes
CREATE INDEX IX_pde_NullEmbedding
ON Production.ProductDescriptionEmbeddings
( ProductDescriptionID, ProductID, ProductModelID, CultureID )
WHERE Embedding IS NULL;
GO

CREATE INDEX IX_pde_ByDescription
ON Production.ProductDescriptionEmbeddings (ProductDescriptionID, CultureID)
INCLUDE (ProductID, ProductModelID, ModifiedDate);
GO