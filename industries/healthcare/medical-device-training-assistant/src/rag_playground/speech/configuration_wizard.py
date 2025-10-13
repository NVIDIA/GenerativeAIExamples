# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A module containing utilities for defining application configuration.

This module provides a configuration wizard class that can read configuration data from YAML, JSON, and environment
variables. The configuration wizard is based heavily off of the JSON and YAML wizards from the `dataclass-wizard`
Python package. That package is in-turn based heavily off of the built-in `dataclass` module.

This module adds Environment Variable parsing to config file reading.
"""
# pylint: disable=too-many-lines; this file is meant to be portable between projects so everything is put into one file

import json
import logging
import os
from dataclasses import _MISSING_TYPE, dataclass
from typing import Any, Callable, Dict, List, Optional, TextIO, Tuple, Union

import yaml
from dataclass_wizard import JSONWizard, LoadMeta, YAMLWizard, errors, fromdict, json_field
from dataclass_wizard.models import JSONField
from dataclass_wizard.utils.string_conv import to_camel_case

configclass = dataclass(frozen=True)
ENV_BASE = "APP"
_LOGGER = logging.getLogger(__name__)


def configfield(name: str, *, env: bool = True, help_txt: str = "", **kwargs: Any) -> JSONField:
    """Create a data class field with the specified name in JSON format.

    :param name: The name of the field.
    :type name: str
    :param env: Whether this field should be configurable from an environment variable.
    :type env: bool
    :param help_txt: The description of this field that is used in help docs.
    :type help_txt: str
    :param **kwargs: Optional keyword arguments to customize the JSON field. More information here:
                     https://dataclass-wizard.readthedocs.io/en/latest/dataclass_wizard.html#dataclass_wizard.json_field
    :type **kwargs: Any
    :returns: A JSONField instance with the specified name and optional parameters.
    :rtype: JSONField

    :raises TypeError: If the provided name is not a string.
    """
    # sanitize specified name
    if not isinstance(name, str):
        raise TypeError("Provided name must be a string.")
    json_name = to_camel_case(name)

    # update metadata
    meta = kwargs.get("metadata", {})
    meta["env"] = env
    meta["help"] = help_txt
    kwargs["metadata"] = meta

    # create the data class field
    field = json_field(json_name, **kwargs)
    return field


class _Color:
    """A collection of colors used when writing output to the shell."""

    # pylint: disable=too-few-public-methods; this class does not require methods.

    PURPLE = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


class ConfigWizard(JSONWizard, YAMLWizard):  # type: ignore[misc] # dataclass-wizard doesn't provide stubs
    """A configuration wizard class that can read configuration data from YAML, JSON, and environment variables."""

    # pylint: disable=arguments-differ,arguments-renamed; this class intentionally reduces arguments for some methods.

    @classmethod
    def print_help(
        cls,
        help_printer: Callable[[str], Any],
        *,
        env_parent: Optional[str] = None,
        json_parent: Optional[Tuple[str, ...]] = None,
    ) -> None:
        """Print the help documentation for the application configuration with the provided `write` function.

        :param help_printer: The `write` function that will be used to output the data.
        :param help_printer: Callable[[str], None]
        :param env_parent: The name of the parent environment variable. Leave blank, used for recursion.
        :type env_parent: Optional[str]
        :param json_parent: The name of the parent JSON key. Leave blank, used for recursion.
        :type json_parent: Optional[Tuple[str, ...]]
        :returns: A list of tuples with one item per configuration value. Each item will have the environment variable
                  and a tuple to the path in configuration.
        :rtype: List[Tuple[str, Tuple[str, ...]]]
        """
        if not env_parent:
            env_parent = ""
            help_printer("---\n")
        if not json_parent:
            json_parent = ()

        for (
            _,
            val,
        ) in (
            cls.__dataclass_fields__.items()  # pylint: disable=no-member; false positive
        ):  # pylint: disable=no-member; member is added by dataclass.
            jsonname = val.json.keys[0]
            envname = jsonname.upper()
            full_envname = f"{ENV_BASE}{env_parent}_{envname}"
            is_embedded_config = hasattr(val.type, "envvars")

            # print the help data
            indent = len(json_parent) * 2
            if is_embedded_config:
                default = ""
            elif not isinstance(val.default_factory, _MISSING_TYPE):
                default = val.default_factory()
            elif isinstance(val.default, _MISSING_TYPE):
                default = "NO-DEFAULT-VALUE"
            else:
                default = val.default
            help_printer(f"{_Color.BOLD}{' ' * indent}{jsonname}:{_Color.END} {default}\n")

            # print comments
            if is_embedded_config:
                indent += 2
            if val.metadata.get("help"):
                help_printer(f"{' ' * indent}# {val.metadata['help']}\n")
            if not is_embedded_config:
                typestr = getattr(val.type, "__name__", None) or str(val.type).replace("typing.", "")
                help_printer(f"{' ' * indent}# Type: {typestr}\n")
            if val.metadata.get("env", True):
                help_printer(f"{' ' * indent}# ENV Variable: {full_envname}\n")
            # if not is_embedded_config:
            help_printer("\n")

            if is_embedded_config:
                new_env_parent = f"{env_parent}_{envname}"
                new_json_parent = json_parent + (jsonname,)
                val.type.print_help(help_printer, env_parent=new_env_parent, json_parent=new_json_parent)

        help_printer("\n")

    @classmethod
    def envvars(
        cls, env_parent: Optional[str] = None, json_parent: Optional[Tuple[str, ...]] = None,
    ) -> List[Tuple[str, Tuple[str, ...], type]]:
        """Calculate valid environment variables and their config structure location.

        :param env_parent: The name of the parent environment variable.
        :type env_parent: Optional[str]
        :param json_parent: The name of the parent JSON key.
        :type json_parent: Optional[Tuple[str, ...]]
        :returns: A list of tuples with one item per configuration value. Each item will have the environment variable,
                  a tuple to the path in configuration, and they type of the value.
        :rtype: List[Tuple[str, Tuple[str, ...], type]]
        """
        if not env_parent:
            env_parent = ""
        if not json_parent:
            json_parent = ()
        output = []

        for (
            _,
            val,
        ) in (
            cls.__dataclass_fields__.items()  # pylint: disable=no-member; false positive
        ):  # pylint: disable=no-member; member is added by dataclass.
            jsonname = val.json.keys[0]
            envname = jsonname.upper()
            full_envname = f"{ENV_BASE}{env_parent}_{envname}"
            is_embedded_config = hasattr(val.type, "envvars")

            # add entry to output list
            if is_embedded_config:
                new_env_parent = f"{env_parent}_{envname}"
                new_json_parent = json_parent + (jsonname,)
                output += val.type.envvars(env_parent=new_env_parent, json_parent=new_json_parent)
            elif val.metadata.get("env", True):
                output += [(full_envname, json_parent + (jsonname,), val.type)]

        return output

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigWizard":
        """Create a ConfigWizard instance from a dictionary.

        :param data: The dictionary containing the configuration data.
        :type data: Dict[str, Any]
        :returns: A ConfigWizard instance created from the input dictionary.
        :rtype: ConfigWizard

        :raises RuntimeError: If the configuration data is not a dictionary.
        """
        # sanitize data
        if not data:
            data = {}
        if not isinstance(data, dict):
            raise RuntimeError("Configuration data is not a dictionary.")

        # parse env variables
        for envvar in cls.envvars():
            var_name, conf_path, var_type = envvar
            var_value = os.environ.get(var_name)
            if var_value:
                var_value = try_json_load(var_value)
                update_dict(data, conf_path, var_value)
                _LOGGER.debug(
                    "Found EnvVar Config - %s:%s = %s", var_name, str(var_type), repr(var_value),
                )

        LoadMeta(key_transform="CAMEL").bind_to(cls)
        return fromdict(cls, data)  # type: ignore[no-any-return] # dataclass-wizard doesn't provide stubs

    @classmethod
    def from_file(cls, filepath: str) -> Optional["ConfigWizard"]:
        """Load the application configuration from the specified file.

        The file must be either in JSON or YAML format.

        :returns: The fully processed configuration file contents. If the file was unreadable, None will be returned.
        :rtype: Optional["ConfigWizard"]
        """
        # open the file
        try:
            # pylint: disable-next=consider-using-with; using a with would make exception handling even more ugly
            file = open(filepath, encoding="utf-8")
        except FileNotFoundError:
            _LOGGER.error("The configuration file cannot be found.")
            file = None
        except PermissionError:
            _LOGGER.error("Permission denied when trying to read the configuration file.")
            file = None
        if not file:
            return None

        # read the file
        try:
            data = read_json_or_yaml(file)
        except ValueError as err:
            _LOGGER.error(
                "Configuration file must be valid JSON or YAML. The following errors occured:\n%s", str(err),
            )
            data = None
            config = None
        finally:
            file.close()

        # parse the file
        if data:
            try:
                config = cls.from_dict(data)
            except errors.MissingFields as err:
                _LOGGER.error("Configuration is missing required fields: \n%s", str(err))
                config = None
            except errors.ParseError as err:
                _LOGGER.error("Invalid configuration value provided:\n%s", str(err))
                config = None
        else:
            config = cls.from_dict({})

        return config


def read_json_or_yaml(stream: TextIO) -> Dict[str, Any]:
    """Read a file without knowing if it is JSON or YAML formatted.

    The file will first be assumed to be JSON formatted. If this fails, an attempt to parse the file with the YAML
    parser will be made. If both of these fail, an exception will be raised that contains the exception strings returned
    by both the parsers.

    :param stream: An IO stream that allows seeking.
    :type stream: typing.TextIO
    :returns: The parsed file contents.
    :rtype: typing.Dict[str, typing.Any]:
    :raises ValueError: If the IO stream is not seekable or if the file doesn't appear to be JSON or YAML formatted.
    """
    exceptions: Dict[str, Union[None, ValueError, yaml.error.YAMLError]] = {
        "JSON": None,
        "YAML": None,
    }
    data: Dict[str, Any]

    # ensure we can rewind the file
    if not stream.seekable():
        raise ValueError("The provided stream must be seekable.")

    # attempt to read json
    try:
        data = json.loads(stream.read())
    except ValueError as err:
        exceptions["JSON"] = err
    else:
        return data
    finally:
        stream.seek(0)

    # attempt to read yaml
    try:
        data = yaml.safe_load(stream.read())
    except (yaml.error.YAMLError, ValueError) as err:
        exceptions["YAML"] = err
    else:
        return data

    # neither json nor yaml
    err_msg = "\n\n".join([key + " Parser Errors:\n" + str(val) for key, val in exceptions.items()])
    raise ValueError(err_msg)


def try_json_load(value: str) -> Any:
    """Try parsing the value as JSON and silently ignore errors.

    :param value: The value on which a JSON load should be attempted.
    :type value: str
    :returns: Either the parsed JSON or the provided value.
    :rtype: typing.Any
    """
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def update_dict(data: Dict[str, Any], path: Tuple[str, ...], value: Any, overwrite: bool = False,) -> None:
    """Update a dictionary with a new value at a given path.

    :param data: The dictionary to be updated.
    :type data: Dict[str, Any]
    :param path: The path to the key that should be updated.
    :type path: Tuple[str, ...]
    :param value: The new value to be set at the specified path.
    :type value: Any
    :param overwrite: If True, overwrite the existing value. Otherwise, don't update if the key already exists.
    :type overwrite: bool
    :returns: None
    """
    end = len(path)
    target = data
    for idx, key in enumerate(path, 1):
        # on the last field in path, update the dict if necessary
        if idx == end:
            if overwrite or not target.get(key):
                target[key] = value
            return

        # verify the next hop exists
        if not target.get(key):
            target[key] = {}

        # if the next hop is not a dict, exit
        if not isinstance(target.get(key), dict):
            return

        # get next hop
        target = target.get(key)  # type: ignore[assignment] # type has already been enforced.
