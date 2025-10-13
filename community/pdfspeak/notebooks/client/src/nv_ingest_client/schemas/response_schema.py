# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# NOTE: This code is duplicated from the ingest service:
# src/nv_ingest/schemas/message_brokers/response_schema.py
# Eventually we should move all client wrappers for the message broker into a shared library that both the ingest
# service and the client can use.

from typing import Optional, Union
from pydantic import BaseModel


class ResponseSchema(BaseModel):
    response_code: int
    response_reason: Optional[str] = "OK"
    response: Union[str, dict, None] = None
    trace_id: Optional[str] = None  # Unique trace ID
    transaction_id: Optional[str] = None  # Unique transaction ID
