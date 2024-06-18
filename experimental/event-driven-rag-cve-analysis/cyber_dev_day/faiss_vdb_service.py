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

import asyncio
import copy
import json
import logging
import threading
import time
import typing
from functools import wraps

import pandas as pd

import cudf

from morpheus.service.vdb.vector_db_service import VectorDBResourceService
from morpheus.service.vdb.vector_db_service import VectorDBService

logger = logging.getLogger(__name__)

IMPORT_EXCEPTION = None
IMPORT_ERROR_MESSAGE = "MilvusVectorDBResourceService requires the milvus and pymilvus packages to be installed."

try:
    from langchain.vectorstores.faiss import FAISS
except ImportError as import_exc:
    IMPORT_EXCEPTION = import_exc


class FaissVectorDBResourceService(VectorDBResourceService):
    """
    Represents a service for managing resources in a Milvus Vector Database.

    Parameters
    ----------
    name : str
        Name of the resource.
    client : MilvusClient
        An instance of the MilvusClient for interaction with the Milvus Vector Database.
    """

    def __init__(self, parent: "FaissVectorDBService", *, name: str) -> None:
        if IMPORT_EXCEPTION is not None:
            raise ImportError(IMPORT_ERROR_MESSAGE) from IMPORT_EXCEPTION

        super().__init__()

        self._parent = parent
        self._name = name

        self._index = FAISS.load_local(folder_path=self._parent._local_dir,
                                       embeddings=self._parent._embeddings,
                                       index_name=self._name,
                                       allow_dangerous_deserialization=True)

    def insert(self, data: list[list] | list[dict], **kwargs: dict[str, typing.Any]) -> dict:
        """
        Insert data into the vector database.

        Parameters
        ----------
        data : list[list] | list[dict]
            Data to be inserted into the collection.
        **kwargs : dict[str, typing.Any]
            Extra keyword arguments specific to the vector database implementation.

        Returns
        -------
        dict
            Returns response content as a dictionary.
        """
        raise NotImplementedError("Insert operation is not supported in FAISS")

    def insert_dataframe(self, df: typing.Union[cudf.DataFrame, pd.DataFrame], **kwargs: dict[str, typing.Any]) -> dict:
        """
        Insert a dataframe entires into the vector database.

        Parameters
        ----------
        df : typing.Union[cudf.DataFrame, pd.DataFrame]
            Dataframe to be inserted into the collection.
        **kwargs : dict[str, typing.Any]
            Extra keyword arguments specific to the vector database implementation.

        Returns
        -------
        dict
            Returns response content as a dictionary.
        """
        raise NotImplementedError("Insert operation is not supported in FAISS")

    def describe(self, **kwargs: dict[str, typing.Any]) -> dict:
        """
        Provides a description of the collection.

        Parameters
        ----------
        **kwargs : dict[str, typing.Any]
            Extra keyword arguments specific to the vector database implementation.

        Returns
        -------
        dict
            Returns response content as a dictionary.
        """
        raise NotImplementedError("Describe operation is not supported in FAISS")

    def query(self, query: str, **kwargs: dict[str, typing.Any]) -> typing.Any:
        """
        Query data in a collection in the Milvus vector database.

        This method performs a search operation in the specified collection/partition in the Milvus vector database.

        Parameters
        ----------
        query : str, optional
            The search query, which can be a filter expression, by default None.
        **kwargs : dict
            Additional keyword arguments for the search operation.

        Returns
        -------
        typing.Any
            The search result, which can vary depending on the query and options.

        Raises
        ------
        RuntimeError
            If an error occurs during the search operation.
            If query argument is `None` and `data` keyword argument doesn't exist.
            If `data` keyword arguement is `None`.
        """
        raise NotImplementedError("Query operation is not supported in FAISS")

    async def similarity_search(self,
                                embeddings: list[list[float]],
                                k: int = 4,
                                **kwargs: dict[str, typing.Any]) -> list[list[dict]]:
        """
        Perform a similarity search within the collection.

        Parameters
        ----------
        embeddings : list[list[float]]
            Embeddings for which to perform the similarity search.
        k : int, optional
            The number of nearest neighbors to return, by default 4.
        **kwargs : dict[str, typing.Any]
            Extra keyword arguments specific to the vector database implementation.

        Returns
        -------
        list[dict]
            Returns a list of dictionaries representing the results of the similarity search.
        """

        async def single_search(single_embedding):
            docs = await self._index.asimilarity_search_by_vector(embedding=single_embedding, k=k)

            return [d.dict() for d in docs]

        return list(await asyncio.gather(*[single_search(embedding) for embedding in embeddings]))

    def update(self, data: list[typing.Any], **kwargs: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """
        Update data in the collection.

        Parameters
        ----------
        data : list[typing.Any]
            Data to be updated in the collection.
        **kwargs : dict[str, typing.Any]
            Extra keyword arguments specific to upsert operation.

        Returns
        -------
        dict[str, typing.Any]
            Returns result of the updated operation stats.
        """
        raise NotImplementedError("Update operation is not supported in FAISS")

    def delete_by_keys(self, keys: int | str | list, **kwargs: dict[str, typing.Any]) -> typing.Any:
        """
        Delete vectors by keys from the collection.

        Parameters
        ----------
        keys : int | str | list
            Primary keys to delete vectors.
        **kwargs :  dict[str, typing.Any]
            Extra keyword arguments specific to the vector database implementation.

        Returns
        -------
        typing.Any
            Returns result of the given keys that are deleted from the collection.
        """
        raise NotImplementedError("Delete by keys operation is not supported in FAISS")

    def delete(self, expr: str, **kwargs: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """
        Delete vectors from the collection using expressions.

        Parameters
        ----------
        expr : str
            Delete expression.
        **kwargs :  dict[str, typing.Any]
            Extra keyword arguments specific to the vector database implementation.

        Returns
        -------
        dict[str, typing.Any]
            Returns result of the given keys that are deleted from the collection.
        """
        raise NotImplementedError("Delete operation is not supported in FAISS")

    def retrieve_by_keys(self, keys: int | str | list, **kwargs: dict[str, typing.Any]) -> list[typing.Any]:
        """
        Retrieve the inserted vectors using their primary keys.

        Parameters
        ----------
        keys : int | str | list
            Primary keys to get vectors for. Depending on pk_field type it can be int or str
            or a list of either.
        **kwargs :  dict[str, typing.Any]
            Additional keyword arguments for the retrieval operation.

        Returns
        -------
        list[typing.Any]
            Returns result rows of the given keys from the collection.
        """
        raise NotImplementedError("Retrieve by keys operation is not supported in FAISS")

    def count(self, **kwargs: dict[str, typing.Any]) -> int:
        """
        Returns number of rows/entities.

        Parameters
        ----------
        **kwargs :  dict[str, typing.Any]
            Additional keyword arguments for the count operation.

        Returns
        -------
        int
            Returns number of entities in the collection.
        """
        raise NotImplementedError("Count operation is not supported in FAISS")

    def drop(self, **kwargs: dict[str, typing.Any]) -> None:
        """
        Drop a collection, index, or partition in the Milvus vector database.

        This function allows you to drop a collection.

        Parameters
        ----------
        **kwargs : dict
            Additional keyword arguments for specifying the type and partition name (if applicable).
        """
        raise NotImplementedError("Drop operation is not supported in FAISS")


class FaissVectorDBService(VectorDBService):
    """
    Service class for Milvus Vector Database implementation. This class provides functions for interacting
    with a Milvus vector database.

    Parameters
    ----------
    host : str
        The hostname or IP address of the Milvus server.
    port : str
        The port number for connecting to the Milvus server.
    alias : str, optional
        Alias for the Milvus connection, by default "default".
    **kwargs : dict
        Additional keyword arguments specific to the Milvus connection configuration.
    """

    _collection_locks = {}
    _cleanup_interval = 600  # 10mins
    _last_cleanup_time = time.time()

    def __init__(self, local_dir: str, embeddings, **kwargs: dict[str, typing.Any]):

        if IMPORT_EXCEPTION is not None:
            raise ImportError(IMPORT_ERROR_MESSAGE) from IMPORT_EXCEPTION

        self._local_dir = local_dir
        self._embeddings = embeddings

    def load_resource(self, name: str = "index", **kwargs: dict[str, typing.Any]) -> FaissVectorDBResourceService:

        return FaissVectorDBResourceService(self, name=name, **kwargs)

    def has_store_object(self, name: str) -> bool:
        """
        Check if a collection exists in the Milvus vector database.

        Parameters
        ----------
        name : str
            Name of the collection to check.

        Returns
        -------
        bool
            True if the collection exists, False otherwise.
        """
        return self._client.has_collection(collection_name=name)

    def list_store_objects(self, **kwargs: dict[str, typing.Any]) -> list[str]:
        """
        List the names of all collections in the Milvus vector database.

        Returns
        -------
        list[str]
            A list of collection names.
        """
        return self._client.list_collections(**kwargs)

    def _create_schema_field(self, field_conf: dict) -> "pymilvus.FieldSchema":

        field_schema = pymilvus.FieldSchema.construct_from_dict(field_conf)

        return field_schema

    def create(self, name: str, overwrite: bool = False, **kwargs: dict[str, typing.Any]):
        """
        Create a collection in the Milvus vector database with the specified name and configuration. This method
        creates a new collection in the Milvus vector database with the provided name and configuration options.
        If the collection already exists, it can be overwritten if the `overwrite` parameter is set to True.

        Parameters
        ----------
        name : str
            Name of the collection to be created.
        overwrite : bool, optional
            If True, the collection will be overwritten if it already exists, by default False.
        **kwargs : dict
            Additional keyword arguments containing collection configuration.

        Raises
        ------
        ValueError
            If the provided schema fields configuration is empty.
        """
        logger.debug("Creating collection: %s, overwrite=%s, kwargs=%s", name, overwrite, kwargs)

        # Preserve original configuration.
        collection_conf = copy.deepcopy(kwargs)

        auto_id = collection_conf.get("auto_id", False)
        index_conf = collection_conf.get("index_conf", None)
        partition_conf = collection_conf.get("partition_conf", None)

        schema_conf = collection_conf.get("schema_conf")
        schema_fields_conf = schema_conf.pop("schema_fields")

        if not self.has_store_object(name) or overwrite:
            if overwrite and self.has_store_object(name):
                self.drop(name)

            if len(schema_fields_conf) == 0:
                raise ValueError("Cannot create collection as provided empty schema_fields configuration")

            schema_fields = [FieldSchemaEncoder.from_dict(field_conf) for field_conf in schema_fields_conf]

            schema = pymilvus.CollectionSchema(fields=schema_fields, **schema_conf)

            self._client.create_collection_with_schema(collection_name=name,
                                                       schema=schema,
                                                       index_params=index_conf,
                                                       auto_id=auto_id,
                                                       shards_num=collection_conf.get("shards", 2),
                                                       consistency_level=collection_conf.get(
                                                           "consistency_level", "Strong"))

            if partition_conf:
                timeout = partition_conf.get("timeout", 1.0)
                # Iterate over each partition configuration
                for part in partition_conf["partitions"]:
                    self._client.create_partition(collection_name=name, partition_name=part["name"], timeout=timeout)

    def create_from_dataframe(self,
                              name: str,
                              df: typing.Union[cudf.DataFrame, pd.DataFrame],
                              overwrite: bool = False,
                              **kwargs: dict[str, typing.Any]) -> None:
        """
        Create collections in the vector database.

        Parameters
        ----------
        name : str
            Name of the collection.
        df : Union[cudf.DataFrame, pd.DataFrame]
            The dataframe to create the collection from.
        overwrite : bool, optional
            Whether to overwrite the collection if it already exists. Default is False.
        **kwargs : dict[str, typing.Any]
            Extra keyword arguments specific to the vector database implementation.
        """

        fields = self._build_schema_conf(df=df)

        create_kwargs = {
            "schema_conf": {
                "description": "Auto generated schema from DataFrame in Morpheus",
                "schema_fields": fields,
            }
        }

        if (kwargs.get("index_field", None) is not None):
            # Check to make sure the column name exists in the fields
            create_kwargs["index_conf"] = {
                "field_name": kwargs.get("index_field"),  # Default index type
                "metric_type": "L2",
                "index_type": "HNSW",
                "params": {
                    "M": 8,
                    "efConstruction": 64,
                },
            }

        self.create(name=name, overwrite=overwrite, **create_kwargs)

    def insert(self, name: str, data: list[list] | list[dict], **kwargs: dict[str,
                                                                              typing.Any]) -> dict[str, typing.Any]:
        """
        Insert a collection specific data in the Milvus vector database.

        Parameters
        ----------
        name : str
            Name of the collection to be inserted.
        data : list[list] | list[dict]
            Data to be inserted in the collection.
        **kwargs : dict[str, typing.Any]
            Additional keyword arguments containing collection configuration.

        Returns
        -------
        dict
            Returns response content as a dictionary.

        Raises
        ------
        RuntimeError
            If the collection not exists exists.
        """

        resource = self.load_resource(name)
        return resource.insert(data, **kwargs)

    def insert_dataframe(self,
                         name: str,
                         df: typing.Union[cudf.DataFrame, pd.DataFrame],
                         **kwargs: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """
        Converts dataframe to rows and insert to a collection in the Milvus vector database.

        Parameters
        ----------
        name : str
            Name of the collection to be inserted.
        df : typing.Union[cudf.DataFrame, pd.DataFrame]
            Dataframe to be inserted in the collection.
        **kwargs : dict[str, typing.Any]
            Additional keyword arguments containing collection configuration.

        Returns
        -------
        dict
            Returns response content as a dictionary.

        Raises
        ------
        RuntimeError
            If the collection not exists exists.
        """
        resource = self.load_resource(name)

        return resource.insert_dataframe(df=df, **kwargs)

    def query(self, name: str, query: str = None, **kwargs: dict[str, typing.Any]) -> typing.Any:
        """
        Query data in a collection in the Milvus vector database.

        This method performs a search operation in the specified collection/partition in the Milvus vector database.

        Parameters
        ----------
        name : str
            Name of the collection to search within.
        query : str
            The search query, which can be a filter expression.
        **kwargs : dict
            Additional keyword arguments for the search operation.

        Returns
        -------
        typing.Any
            The search result, which can vary depending on the query and options.
        """

        resource = self.load_resource(name)

        return resource.query(query, **kwargs)

    async def similarity_search(self, name: str, **kwargs: dict[str, typing.Any]) -> list[dict]:
        """
        Perform a similarity search within the collection.

        Parameters
        ----------
        name : str
            Name of the collection.
        **kwargs : dict[str, typing.Any]
            Extra keyword arguments specific to the vector database implementation.

        Returns
        -------
        list[dict]
            Returns a list of dictionaries representing the results of the similarity search.
        """

        resource = self.load_resource(name)

        return resource.similarity_search(**kwargs)

    def update(self, name: str, data: list[typing.Any], **kwargs: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """
        Update data in the vector database.

        Parameters
        ----------
        name : str
            Name of the collection.
        data : list[typing.Any]
            Data to be updated in the collection.
        **kwargs : dict[str, typing.Any]
            Extra keyword arguments specific to upsert operation.

        Returns
        -------
        dict[str, typing.Any]
            Returns result of the updated operation stats.
        """

        if not isinstance(data, list):
            raise RuntimeError("Data is not of type list.")

        resource = self.load_resource(name)

        return resource.update(data=data, **kwargs)

    def delete_by_keys(self, name: str, keys: int | str | list, **kwargs: dict[str, typing.Any]) -> typing.Any:
        """
        Delete vectors by keys from the collection.

        Parameters
        ----------
        name : str
            Name of the collection.
        keys : int | str | list
            Primary keys to delete vectors.
        **kwargs :  dict[str, typing.Any]
            Extra keyword arguments specific to the vector database implementation.

        Returns
        -------
        typing.Any
            Returns result of the given keys that are delete from the collection.
        """

        resource = self.load_resource(name)

        return resource.delete_by_keys(keys=keys, **kwargs)

    def delete(self, name: str, expr: str, **kwargs: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """
        Delete vectors from the collection using expressions.

        Parameters
        ----------
        name : str
            Name of the collection.
        expr : str
            Delete expression.
        **kwargs :  dict[str, typing.Any]
            Extra keyword arguments specific to the vector database implementation.

        Returns
        -------
        dict[str, typing.Any]
            Returns result of the given keys that are delete from the collection.
        """

        resource = self.load_resource(name)
        result = resource.delete(expr=expr, **kwargs)

        return result

    def retrieve_by_keys(self, name: str, keys: int | str | list, **kwargs: dict[str, typing.Any]) -> list[typing.Any]:
        """
        Retrieve the inserted vectors using their primary keys from the Collection.

        Parameters
        ----------
        name : str
            Name of the collection.
        keys : int | str | list
            Primary keys to get vectors for. Depending on pk_field type it can be int or str
            or a list of either.
        **kwargs :  dict[str, typing.Any]
            Additional keyword arguments for the retrieval operation.

        Returns
        -------
        list[typing.Any]
            Returns result rows of the given keys from the collection.
        """

        resource = self.load_resource(name)

        result = resource.retrieve_by_keys(keys=keys, **kwargs)

        return result

    def count(self, name: str, **kwargs: dict[str, typing.Any]) -> int:
        """
        Returns number of rows/entities in the given collection.

        Parameters
        ----------
        name : str
            Name of the collection.
        **kwargs :  dict[str, typing.Any]
            Additional keyword arguments for the count operation.

        Returns
        -------
        int
            Returns number of entities in the collection.
        """
        resource = self.load_resource(name)

        return resource.count(**kwargs)

    def drop(self, name: str, **kwargs: dict[str, typing.Any]) -> None:
        """
        Drop a collection, index, or partition in the Milvus vector database.

        This method allows you to drop a collection, an index within a collection,
        or a specific partition within a collection in the Milvus vector database.

        Parameters
        ----------
        name : str
            Name of the collection, index, or partition to be dropped.
        **kwargs : dict
            Additional keyword arguments for specifying the type and partition name (if applicable).

        Notes on Expected Keyword Arguments:
        ------------------------------------
        - 'collection' (str, optional):
        Specifies the type of collection to drop. Possible values: 'collection' (default), 'index', 'partition'.

        - 'partition_name' (str, optional):
        Required when dropping a specific partition within a collection. Specifies the partition name to be dropped.

        - 'field_name' (str, optional):
        Required when dropping an index within a collection. Specifies the field name for which the index is created.

        - 'index_name' (str, optional):
        Required when dropping an index within a collection. Specifies the name of the index to be dropped.

        Raises
        ------
        ValueError
            If mandatory arguments are missing or if the provided 'collection' value is invalid.
        """

        logger.debug("Dropping collection: %s, kwargs=%s", name, kwargs)

        if self.has_store_object(name):
            resource = kwargs.get("resource", "collection")
            if resource == "collection":
                self._client.drop_collection(collection_name=name)
            elif resource == "partition":
                if "partition_name" not in kwargs:
                    raise ValueError("Mandatory argument 'partition_name' is required when resource='partition'")
                partition_name = kwargs["partition_name"]
                if self._client.has_partition(collection_name=name, partition_name=partition_name):
                    # Collection need to be released before dropping the partition.
                    self._client.release_collection(collection_name=name)
                    self._client.drop_partition(collection_name=name, partition_name=partition_name)
            elif resource == "index":
                if "field_name" in kwargs and "index_name" in kwargs:
                    self._client.drop_index(collection_name=name,
                                            field_name=kwargs["field_name"],
                                            index_name=kwargs["index_name"])
                else:
                    raise ValueError(
                        "Mandatory arguments 'field_name' and 'index_name' are required when resource='index'")

    def describe(self, name: str, **kwargs: dict[str, typing.Any]) -> dict:
        """
        Describe the collection in the vector database.

        Parameters
        ----------
        name : str
            Name of the collection.
        **kwargs : dict[str, typing.Any]
            Additional keyword arguments specific to the Milvus vector database.

        Returns
        -------
        dict
            Returns collection information.
        """

        resource = self.load_resource(name)

        return resource.describe(**kwargs)

    def release_resource(self, name: str) -> None:
        """
        Release a loaded collection from the memory.

        Parameters
        ----------
        name : str
            Name of the collection to release.
        """

        self._client.release_collection(collection_name=name)

    def close(self) -> None:
        """
        Close the connection to the Milvus vector database.

        This method disconnects from the Milvus vector database by removing the connection.

        """
        self._client.close()
