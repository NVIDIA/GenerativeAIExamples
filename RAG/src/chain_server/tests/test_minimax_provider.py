# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for the MiniMax LLM provider integration.

These tests are self-contained and do not require the full chain_server
dependency stack (llama_index, torch, etc.).
"""

import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


def _ensure_stub(name, attrs=None):
    """Ensure a stub module exists in sys.modules. Does NOT overwrite real packages."""
    parts = name.split(".")
    for i in range(1, len(parts) + 1):
        partial = ".".join(parts[:i])
        if partial not in sys.modules:
            sys.modules[partial] = types.ModuleType(partial)
    mod = sys.modules[name]
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    return mod


def _load_utils_with_mocks():
    """Import utils.py with heavy dependencies mocked out."""

    # Remove any cached version of utils
    for key in list(sys.modules.keys()):
        if "RAG.src.chain_server.utils" in key:
            del sys.modules[key]

    # --- Stub out ALL modules that utils.py imports -----------------------
    # torch
    torch_mod = _ensure_stub("torch")
    torch_mod.cuda = MagicMock()
    torch_mod.cuda.is_available = MagicMock(return_value=False)

    # psycopg2
    _ensure_stub("psycopg2")

    # sqlalchemy
    _ensure_stub("sqlalchemy")
    _ensure_stub("sqlalchemy.engine")
    _ensure_stub("sqlalchemy.engine.url", {"make_url": MagicMock()})

    # llama_index (full hierarchy)
    _ensure_stub("llama_index")
    _ensure_stub("llama_index.core")
    _ensure_stub("llama_index.core.indices", {"VectorStoreIndex": MagicMock()})
    _ensure_stub("llama_index.core.postprocessor")
    _ensure_stub("llama_index.core.postprocessor.types", {
        "BaseNodePostprocessor": type("BaseNodePostprocessor", (), {
            "_postprocess_nodes": lambda self, **kw: []
        })
    })
    _ensure_stub("llama_index.core.schema", {"MetadataMode": MagicMock()})
    _ensure_stub("llama_index.core.service_context", {
        "ServiceContext": MagicMock(),
        "set_global_service_context": MagicMock(),
    })
    _ensure_stub("llama_index.core.utils", {
        "get_tokenizer": MagicMock(),
        "globals_helper": MagicMock(),
    })
    _ensure_stub("llama_index.core.indices.base_retriever")
    _ensure_stub("llama_index.core.indices.query")
    _ensure_stub("llama_index.core.indices.query.schema")
    _ensure_stub("llama_index.core.callbacks", {"CallbackManager": MagicMock()})
    _ensure_stub("llama_index.embeddings")
    _ensure_stub("llama_index.embeddings.langchain", {"LangchainEmbedding": MagicMock()})
    _ensure_stub("llama_index.llms")
    _ensure_stub("llama_index.llms.langchain", {"LangChainLLM": MagicMock()})
    _ensure_stub("llama_index.vector_stores")
    _ensure_stub("llama_index.vector_stores.milvus", {"MilvusVectorStore": MagicMock()})
    _ensure_stub("llama_index.vector_stores.postgres", {"PGVectorStore": MagicMock()})

    # langchain (bare imports in utils.py lines 93-96, 66-69)
    _ensure_stub("langchain")
    _ensure_stub("langchain.llms")
    _ensure_stub("langchain.llms.base", {"LLM": MagicMock()})
    _ensure_stub("langchain.text_splitter", {
        "SentenceTransformersTokenTextSplitter": MagicMock()
    })

    # langchain_core (bare imports)
    _ensure_stub("langchain_core")
    _ensure_stub("langchain_core.documents")
    _ensure_stub("langchain_core.documents.compressor", {"BaseDocumentCompressor": MagicMock()})
    _ensure_stub("langchain_core.embeddings", {"Embeddings": MagicMock()})
    _ensure_stub("langchain_core.language_models")
    _ensure_stub("langchain_core.language_models.chat_models", {"SimpleChatModel": MagicMock()})
    _ensure_stub("langchain_core.vectorstores", {"VectorStore": MagicMock()})

    # langchain_community
    _ensure_stub("langchain_community")
    _ensure_stub("langchain_community.embeddings", {"HuggingFaceEmbeddings": MagicMock()})
    _ensure_stub("langchain_community.vectorstores", {
        "FAISS": MagicMock(), "Milvus": MagicMock(), "PGVector": MagicMock()
    })
    _ensure_stub("langchain_community.docstore")
    _ensure_stub("langchain_community.docstore.in_memory", {"InMemoryDocstore": MagicMock()})

    # langchain_nvidia_ai_endpoints
    _ensure_stub("langchain_nvidia_ai_endpoints", {
        "ChatNVIDIA": MagicMock(), "NVIDIAEmbeddings": MagicMock(), "NVIDIARerank": MagicMock()
    })

    # langchain_openai
    _ensure_stub("langchain_openai", {"ChatOpenAI": MagicMock()})

    # faiss
    _ensure_stub("faiss", {"IndexFlatL2": MagicMock()})

    # tracing module
    _ensure_stub("RAG")
    _ensure_stub("RAG.src")
    _ensure_stub("RAG.src.chain_server")
    _ensure_stub("RAG.src.chain_server.tracing", {"llama_index_cb_handler": MagicMock()})

    # yaml is already installed, no need to stub

    # Now import utils fresh
    from RAG.src.chain_server import utils
    return utils


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------


class TestMiniMaxConfiguration(unittest.TestCase):
    """Test MiniMax configuration through LLMConfig."""

    def test_model_engine_help_text_includes_minimax(self):
        """Verify that the LLMConfig model_engine help text mentions minimax."""
        from RAG.src.chain_server.configuration import LLMConfig
        fields = LLMConfig.__dataclass_fields__
        help_txt = fields["model_engine"].metadata.get("help", "")
        self.assertIn("minimax", help_txt)

    def test_default_model_engine_unchanged(self):
        """Verify that the default model_engine is still nvidia-ai-endpoints."""
        from RAG.src.chain_server.configuration import LLMConfig
        config = LLMConfig()
        self.assertEqual(config.model_engine, "nvidia-ai-endpoints")


class TestGetLlmMiniMax(unittest.TestCase):
    """Test get_llm() function with MiniMax engine."""

    @classmethod
    def setUpClass(cls):
        cls.utils = _load_utils_with_mocks()
        # Access the raw function, bypassing utils_cache and lru_cache decorators
        # Store in a list to prevent Python descriptor protocol from binding `self`
        raw = cls.utils.get_llm
        while hasattr(raw, "__wrapped__"):
            raw = raw.__wrapped__
        cls._raw_fn = [raw]

    def _make_config(self, model_engine="minimax", model_name="MiniMax-M2.7", server_url=""):
        cfg = MagicMock()
        cfg.llm.model_engine = model_engine
        cfg.llm.model_name = model_name
        cfg.llm.server_url = server_url
        return cfg

    def _call_get_llm(self, **kwargs):
        return self._raw_fn[0](**kwargs)

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    def test_minimax_creates_chat_openai(self):
        with patch.object(self.utils, "get_config", return_value=self._make_config()), \
             patch.object(self.utils, "ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()
            self._call_get_llm()
            mock_chat.assert_called_once()
            kw = mock_chat.call_args.kwargs
            self.assertEqual(kw["model"], "MiniMax-M2.7")
            self.assertEqual(kw["openai_api_key"], "test-key-123")
            self.assertEqual(kw["openai_api_base"], "https://api.minimax.io/v1")

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    def test_minimax_default_model_when_ensemble(self):
        with patch.object(self.utils, "get_config", return_value=self._make_config(model_name="ensemble")), \
             patch.object(self.utils, "ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()
            self._call_get_llm()
            self.assertEqual(mock_chat.call_args.kwargs["model"], "MiniMax-M2.7")

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    def test_minimax_custom_model_name(self):
        with patch.object(self.utils, "get_config", return_value=self._make_config(model_name="MiniMax-M2.5-highspeed")), \
             patch.object(self.utils, "ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()
            self._call_get_llm()
            self.assertEqual(mock_chat.call_args.kwargs["model"], "MiniMax-M2.5-highspeed")

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    def test_minimax_custom_server_url(self):
        with patch.object(self.utils, "get_config", return_value=self._make_config(
            server_url="https://custom-proxy.example.com/v1"
        )), patch.object(self.utils, "ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()
            self._call_get_llm()
            self.assertEqual(
                mock_chat.call_args.kwargs["openai_api_base"],
                "https://custom-proxy.example.com/v1",
            )

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    def test_minimax_temperature_clamping_high(self):
        with patch.object(self.utils, "get_config", return_value=self._make_config()), \
             patch.object(self.utils, "ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()
            self._call_get_llm(temperature=2.5)
            self.assertEqual(mock_chat.call_args.kwargs["temperature"], 1.0)

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    def test_minimax_temperature_clamping_low(self):
        with patch.object(self.utils, "get_config", return_value=self._make_config()), \
             patch.object(self.utils, "ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()
            self._call_get_llm(temperature=-0.5)
            self.assertEqual(mock_chat.call_args.kwargs["temperature"], 0.0)

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    def test_minimax_temperature_none_passthrough(self):
        with patch.object(self.utils, "get_config", return_value=self._make_config()), \
             patch.object(self.utils, "ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()
            self._call_get_llm()
            self.assertIsNone(mock_chat.call_args.kwargs["temperature"])

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    def test_minimax_valid_temperature_passthrough(self):
        with patch.object(self.utils, "get_config", return_value=self._make_config()), \
             patch.object(self.utils, "ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()
            self._call_get_llm(temperature=0.7)
            self.assertAlmostEqual(mock_chat.call_args.kwargs["temperature"], 0.7)

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    def test_minimax_passes_top_p_and_max_tokens(self):
        with patch.object(self.utils, "get_config", return_value=self._make_config()), \
             patch.object(self.utils, "ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()
            self._call_get_llm(top_p=0.9, max_tokens=512)
            kw = mock_chat.call_args.kwargs
            self.assertEqual(kw["top_p"], 0.9)
            self.assertEqual(kw["max_tokens"], 512)

    @patch.dict(os.environ, {"MINIMAX_API_KEY": ""})
    def test_minimax_empty_api_key(self):
        with patch.object(self.utils, "get_config", return_value=self._make_config()), \
             patch.object(self.utils, "ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()
            self._call_get_llm()
            mock_chat.assert_called_once()
            self.assertEqual(mock_chat.call_args.kwargs["openai_api_key"], "")

    def test_unsupported_engine_raises_runtime_error(self):
        cfg = MagicMock()
        cfg.llm.model_engine = "unsupported-engine"
        with patch.object(self.utils, "get_config", return_value=cfg):
            with self.assertRaises(RuntimeError) as ctx:
                self._call_get_llm()
            self.assertIn("nvidia-ai-endpoints", str(ctx.exception))
            self.assertIn("minimax", str(ctx.exception))


class TestGetLlmNvidiaUnchanged(unittest.TestCase):
    """Ensure the existing NVIDIA AI endpoints path is not broken."""

    @classmethod
    def setUpClass(cls):
        cls.utils = _load_utils_with_mocks()
        raw = cls.utils.get_llm
        while hasattr(raw, "__wrapped__"):
            raw = raw.__wrapped__
        cls._raw_fn = [raw]

    def test_nvidia_engine_still_works(self):
        cfg = MagicMock()
        cfg.llm.model_engine = "nvidia-ai-endpoints"
        cfg.llm.model_name = "meta/llama3-70b-instruct"
        cfg.llm.server_url = ""
        with patch.object(self.utils, "get_config", return_value=cfg), \
             patch.object(self.utils, "ChatNVIDIA") as mock_nvidia:
            mock_nvidia.return_value = MagicMock()
            self._raw_fn[0]()
            mock_nvidia.assert_called_once()
            self.assertEqual(mock_nvidia.call_args.kwargs["model"], "meta/llama3-70b-instruct")

    def test_nvidia_engine_with_server_url(self):
        cfg = MagicMock()
        cfg.llm.model_engine = "nvidia-ai-endpoints"
        cfg.llm.model_name = "meta/llama3-70b-instruct"
        cfg.llm.server_url = "localhost:8000"
        with patch.object(self.utils, "get_config", return_value=cfg), \
             patch.object(self.utils, "ChatNVIDIA") as mock_nvidia:
            mock_nvidia.return_value = MagicMock()
            self._raw_fn[0]()
            mock_nvidia.assert_called_once()
            self.assertEqual(mock_nvidia.call_args.kwargs["base_url"], "http://localhost:8000/v1")


# ---------------------------------------------------------------------------
# Integration Tests (require MINIMAX_API_KEY)
# ---------------------------------------------------------------------------


@unittest.skipUnless(
    os.environ.get("MINIMAX_API_KEY"),
    "MINIMAX_API_KEY not set; skipping integration tests",
)
class TestMiniMaxIntegration(unittest.TestCase):
    """Integration tests that call the real MiniMax API via langchain-openai."""

    def test_minimax_chat_completion(self):
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model="MiniMax-M2.7",
            openai_api_key=os.environ["MINIMAX_API_KEY"],
            openai_api_base="https://api.minimax.io/v1",
            temperature=0.1,
        )
        response = llm.invoke("Say 'hello' and nothing else.")
        content = response.content if hasattr(response, "content") else str(response)
        self.assertTrue(len(content) > 0)

    def test_minimax_streaming(self):
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model="MiniMax-M2.7",
            openai_api_key=os.environ["MINIMAX_API_KEY"],
            openai_api_base="https://api.minimax.io/v1",
            temperature=0.1,
        )
        chunks = list(llm.stream("Say 'world' and nothing else."))
        self.assertTrue(len(chunks) > 0)

    def test_minimax_m25_highspeed(self):
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model="MiniMax-M2.5-highspeed",
            openai_api_key=os.environ["MINIMAX_API_KEY"],
            openai_api_base="https://api.minimax.io/v1",
            temperature=0.1,
        )
        response = llm.invoke("Say 'test' and nothing else.")
        content = response.content if hasattr(response, "content") else str(response)
        self.assertTrue(len(content) > 0)


if __name__ == "__main__":
    unittest.main()
