EXEC dbo.CreateExternalModel
    --@Location = 'https://ngc-test.ashysmoke-ef652ce7.westus.azurecontainerapps.io/v1/embeddings',
    @Location = 'https://192.168.10.218:8000/v1/embeddings',
    @Model = 'nvidia/nv-embedqa-e5-v5-query',
    @Name = 'EmbedE5_OpenAI';


SELECT * FROM sys.external_models WHERE name = 'EmbedE5_OpenAI';