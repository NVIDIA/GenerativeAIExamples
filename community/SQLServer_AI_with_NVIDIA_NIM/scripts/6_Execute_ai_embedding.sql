
DECLARE @StartTime DATETIME2 = SYSDATETIME();

EXEC dbo.nvidia_run_ai_embedding
    @ModelName = 'EmbedE5_OpenAI',
    @TopN = 8;


DECLARE @EndTime DATETIME2 = SYSDATETIME();
DECLARE @TotalMs INT = DATEDIFF(MILLISECOND, @StartTime, @EndTime);
DECLARE @Msg NVARCHAR(1000) = N'Total runtime: ' +
    CONCAT(@TotalMs / 60000, ' min ', (@TotalMs % 60000) / 1000, ' sec ', @TotalMs % 1000, ' ms');

RAISERROR (@Msg, 0, 1) WITH NOWAIT;
