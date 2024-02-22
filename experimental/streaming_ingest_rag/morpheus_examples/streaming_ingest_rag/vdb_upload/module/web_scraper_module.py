# Copyright (c) 2023-2024, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
from functools import partial

import mrc
import mrc.core.operators as ops
import requests
import requests_cache
from bs4 import BeautifulSoup
import lxml
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from pydantic import ValidationError

import cudf

from morpheus.messages import MessageMeta
from morpheus.utils.module_utils import ModuleLoaderFactory
from morpheus.utils.module_utils import register_module

logger = logging.getLogger(__name__)


class WebScraperSchema(BaseModel):
    link_column: str = "link"
    chunk_size: int = 512
    chunk_overlap: int = 51
    enable_cache: bool = False
    cache_path: str = "./.cache/http/RSSDownloadStage.sqlite"
    cache_dir: str = "./.cache/llm/rss"

    class Config:
        extra = "forbid"


WebScraperLoaderFactory = ModuleLoaderFactory("web_scraper", "morpheus_examples_llm", WebScraperSchema)


def download_and_split(msg: MessageMeta, text_splitter, link_column, session) -> MessageMeta:
    """
        Uses the HTTP GET method to download/scrape the links found in the message, splits the scraped data, and stores
        it in the output, excludes output for any links which produce an error.
    """
    if (link_column not in msg.get_column_names()):
        return None

    df = msg.copy_dataframe()

    # Convert the dataframe into a list of dictionaries
    df_dicts = df.to_dict(orient="records")

    final_rows: list[dict] = []

    for row in df_dicts:
        url = row[link_column]

        try:
            # Try to get the page content
            response = session.get(url)

            if (not response.ok):
                logger.warning("Error downloading document from URL '%s'. " + "Returned code: %s. With reason: '%s'",
                               url,
                               response.status_code,
                               response.reason)
                continue

            raw_html = response.text
            soup = BeautifulSoup(raw_html, "lxml")

            text = soup.get_text(strip=True, separator=' ')
            split_text = text_splitter.split_text(text)

            for text in split_text:
                row_cp = row.copy()
                row_cp.update({"page_content": text})
                final_rows.append(row_cp)

            if isinstance(response, requests_cache.models.response.CachedResponse):
                logger.debug("Processed cached page: '%s'", url)
            else:
                logger.debug("Processed page: '%s'", url)

        except ValueError as exc:
            logger.error("Error parsing document: %s", exc)
            continue
        except Exception as exc:
            logger.error("Error downloading document from URL '%s'. Error: %s", url, exc)
            continue

    return MessageMeta(df=cudf.DataFrame(final_rows))


@register_module("web_scraper", "morpheus_examples_llm")
def _web_scraper(builder: mrc.Builder):
    module_config = builder.get_current_module_config()

    # Validate the module configuration using the contract
    try:
        web_scraper_config = WebScraperSchema(**module_config.get("web_scraper_config", {}))
    except ValidationError as e:
        error_messages = '; '.join([f"{error['loc'][0]}: {error['msg']}" for error in e.errors()])
        log_error_message = f"Invalid web scraper configuration: {error_messages}"
        logger.error(log_error_message)

        raise

    link_column = web_scraper_config.link_column
    chunk_size = web_scraper_config.chunk_size
    enable_cache = web_scraper_config.enable_cache
    cache_path = web_scraper_config.cache_path
    cache_dir = web_scraper_config.cache_dir

    if (enable_cache):
        os.makedirs(cache_dir, exist_ok=True)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size,
                                                   chunk_overlap=chunk_size // 10,
                                                   length_function=len)

    if (enable_cache):
        session = requests_cache.CachedSession(cache_path, backend='sqlite')
    else:
        session = requests.Session()

    session.headers.update({
        "User-Agent":
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    })

    op_func = partial(download_and_split, text_splitter=text_splitter, link_column=link_column, session=session)

    node = builder.make_node("web_scraper", ops.map(op_func), ops.filter(lambda x: x is not None))
    node.launch_options.pe_count = 1
    node.launch_options.engines_per_pe = os.cpu_count()

    builder.register_module_input("input", node)
    builder.register_module_output("output", node)