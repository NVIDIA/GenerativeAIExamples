DECLARE @StartTime DATETIME2 = SYSDATETIME();

EXEC dbo.nvidia_run_proc_embedding
    @ModelName = N'nvidia/nv-embedqa-e5-v5',
    @VectorSize = 1024,
    @VectorColumnName = N'Embed_E5_ACA',
    --@Url = N'https://ams-dedic.thankfulrock-348762e0.westus3.azurecontainerapps.io/v1/embeddings',
    @Url = N'https://192.168.10.218:8000/v1/embeddings',
    --@Url = N'https://ngc-test.ashysmoke-ef652ce7.westus.azurecontainerapps.io/v1/embeddings',
    @MaxRows = 3;

DECLARE @EndTime DATETIME2 = SYSDATETIME();
DECLARE @TotalMs INT = DATEDIFF(MILLISECOND, @StartTime, @EndTime);
DECLARE @Msg NVARCHAR(1000) = N'Total runtime: ' +
    CONCAT(@TotalMs / 60000, ' min ', (@TotalMs % 60000) / 1000, ' sec ', @TotalMs % 1000, ' ms');

RAISERROR (@Msg, 0, 1) WITH NOWAIT;
