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

DECLARE @StartTime DATETIME2 = SYSDATETIME();

EXEC dbo.nvidia_run_ai_embedding
    @ModelName = 'Embed_OpenAI',
    @TopN = 8;


DECLARE @EndTime DATETIME2 = SYSDATETIME();
DECLARE @TotalMs INT = DATEDIFF(MILLISECOND, @StartTime, @EndTime);
DECLARE @Msg NVARCHAR(1000) = N'Total runtime: ' +
    CONCAT(@TotalMs / 60000, ' min ', (@TotalMs % 60000) / 1000, ' sec ', @TotalMs % 1000, ' ms');

RAISERROR (@Msg, 0, 1) WITH NOWAIT;


