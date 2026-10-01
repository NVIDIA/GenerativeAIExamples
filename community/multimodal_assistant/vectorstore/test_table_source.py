import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path


def _install_stubs():
    if "fitz" in sys.modules:
        return

    fitz = types.ModuleType("fitz")

    class Rect:
        def __init__(self, *args):
            if len(args) == 1 and not isinstance(args[0], (str, bytes)):
                args = tuple(args[0])
            self.x0, self.y0, self.x1, self.y1 = args[:4]
            self.width = self.x1 - self.x0
            self.height = self.y1 - self.y0

    fitz.Rect = Rect
    sys.modules["fitz"] = fitz

    pandas = types.ModuleType("pandas")

    class DataFrame:
        def __init__(self):
            self.columns = type("Columns", (), {"values": ["col"]})()

        def to_excel(self, path):
            Path(path).write_text("x")

    pandas.DataFrame = DataFrame
    pandas.concat = lambda frames: frames[0]
    sys.modules["pandas"] = pandas

    document = types.ModuleType("langchain.docstore.document")

    class Document:
        def __init__(self, page_content, metadata):
            self.page_content = page_content
            self.metadata = metadata

    document.Document = Document
    sys.modules["langchain"] = types.ModuleType("langchain")
    sys.modules["langchain.docstore"] = types.ModuleType("langchain.docstore")
    sys.modules["langchain.docstore.document"] = document

    llm_client = types.ModuleType("llm.llm_client")

    class LLMClient:
        def __init__(self, *args, **kwargs):
            pass

    llm_client.LLMClient = LLMClient
    sys.modules["llm"] = types.ModuleType("llm")
    sys.modules["llm.llm_client"] = llm_client

    image = types.ModuleType("PIL.Image")
    image.Image = object
    image.open = lambda *args, **kwargs: None
    sys.modules["PIL"] = types.ModuleType("PIL")
    sys.modules["PIL.Image"] = image


def _load(path):
    _install_stubs()
    spec = importlib.util.spec_from_file_location(path.stem + "_" + path.parent.parent.name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.process_graph = lambda image_path: "desc"
    return module


class Header:
    external = False
    names = ["col"]


class Tab:
    header = Header()
    bbox = (0, 10, 100, 40)

    def to_pandas(self):
        return sys.modules["pandas"].DataFrame()


class Pix:
    def save(self, path):
        Path(path).write_text("img")


class Page:
    class rect:
        height = 100

    def find_tables(self, **kwargs):
        return [Tab(), Tab()]

    def get_pixmap(self, clip=None):
        return Pix()


class TableSourceTest(unittest.TestCase):
    def test_source_uses_the_same_table_number_as_the_saved_files(self):
        root = Path(__file__).resolve().parents[2]
        paths = [
            root / "multimodal_assistant" / "vectorstore" / "custom_pdf_parser.py",
            root / "oran-chatbot-multimodal" / "vectorstore" / "custom_pdf_parser.py",
        ]
        for path in paths:
            module = _load(path)
            with tempfile.TemporaryDirectory() as tmp:
                previous = os.getcwd()
                os.chdir(tmp)
                try:
                    docs, _, _ = module.parse_all_tables("report.pdf", Page(), 0, [], {})
                finally:
                    os.chdir(previous)
            self.assertEqual(
                [doc.metadata["source"] for doc in docs],
                ["report-page0-table1", "report-page0-table2"],
                path.name,
            )
            self.assertTrue(docs[0].metadata["dataframe"].endswith("table1-page0.xlsx"))
            self.assertTrue(docs[1].metadata["image"].endswith("table2-page0.jpg"))


if __name__ == "__main__":
    unittest.main()
