"""Provides functions for parsing YAML descriptor documents.
"""

import re
import os
from strictyaml import (load, Map, MapPattern, Seq, Str, Float, Int, HexInt, Bool, Optional,
                        Any, ScalarValidator, EmptyList, YAMLValidationError)
from strictyaml.representation import YAML
from .properties import PROPERTY_TYPES
from .util import error

class Id(ScalarValidator):
    """Custom validator for descriptor IDs.
    Checks, if an ID is a valid identifier in C code.
    """

    def __init__(self):
        self._regex = r'^(?:[a-zA-Z]{1}[a-zA-Z0-9_]*)$'
        self._fullmatch = re.compile(self._regex).match
        self._matching_message = f"when expecting string matching {self._regex}"
        self._keywords = [
            "auto",
            "break",
            "case",
            "char",
            "const",
            "continue",
            "default",
            "do",
            "double",
            "else",
            "enum",
            "extern",
            "float",
            "for",
            "goto",
            "if",
            "inline",
            "int",
            "long",
            "register",
            "restrict",
            "return",
            "short",
            "signed",
            "sizeof",
            "static",
            "struct",
            "switch",
            "typedef",
            "union",
            "unsigned",
            "void",
            "volatile",
            "while",
            "bool",
            "uint8_t",
            "uint16_t",
            "uint32_t",
            "uint64_t",
            "int8_t",
            "int16_t",
            "int32_t",
            "int64_t",
            "time_point",
            "zone_offset",
            "zoned_time",
            "hh_mm_ss",
            "time_range",
            "date_range",
            "ndef_record",
            "data_last_written_timestamp"
        ]

    def validate_scalar(self, chunk):
        if chunk.contents in self._keywords:
            chunk.expecting_but_found("when expecting an identifier found keyword")
        else:
            if self._fullmatch(chunk.contents) is None:
                chunk.expecting_but_found(
                    self._matching_message, "found non-matching string"
                )
                return None
            else:
                return chunk.contents

class LangCode(ScalarValidator):
    """Custom validator for translation language codes.
    """

    def __init__(self):
        self._regex = r'^(?:[a-zA-Z0-9]{2,3})(?:_[a-zA-Z0-9]+)*$'
        self._fullmatch = re.compile(self._regex).match
        self._matching_message = f"when expecting string matching {self._regex}"

    def validate_scalar(self, chunk):
        if self._fullmatch(chunk.contents) is None:
            chunk.expecting_but_found(
                self._matching_message, "found non-matching string")
            return None
        else:
            return chunk.contents

TRANSLATIONS_SCHEMA = Map({
    "language": LangCode(),
    "translations": MapPattern(Id(), Str())
})

MODIFIER_SCHEMA = Map({
    "type": Str(),
    Optional("id"): Id()
})

ITEM_SELECTION_SCHEMA = Map({
    "type": Str(),
    "id": Id(),
    "entries": Seq(Str()),
    Optional("dependencies"): MapPattern(Id(), EmptyList() | Seq(Id())),
    Optional("default"): Str() | Seq(Str())
})

LANGUAGE_SELECTION_SCHEMA = Map({
    "type": Str(),
    "id": Id(),
    "entries": Seq(Str()),
    Optional("default"): Str()
})

TIME_SCHEMA = Map({
    "type": Str(),
    "id": Id(),
    Optional("default"): Str()
})

STRING_SCHEMA = Map({
    "type": Str(),
    "id": Id(),
    "max_length": Int(),
    Optional("default"): Str()
})

INTEGER_SCHEMA = Map({
    "type": Str(),
    "id": Id(),
    Optional("max_value"): Int() | HexInt(),
    Optional("min_value"): Int() | HexInt(),
    Optional("step_size"): Int() | HexInt(),
    Optional("content_type"): Str(),
    Optional("content_type_def"): Str(),
    Optional("default"): Int() | HexInt()
})

FIXED_POINT_SCHEMA = Map({
    "type": Str(),
    "id": Id(),
    "scale": Int() | HexInt(),
    Optional("max_value"): Int() | HexInt(),
    Optional("min_value"): Int() | HexInt(),
    Optional("content_type"): Str(),
    Optional("content_type_def"): Str(),
    Optional("default"): Int() | HexInt()
})

FLOAT_SCHEMA = Map({
    "type": Str(),
    "id": Id(),
    Optional("max_value"): Float(),
    Optional("min_value"): Float(),
    Optional("content_type"): Str(),
    Optional("content_type_def"): Str(),
    Optional("default"): Float()
})

BOOL_SCHEMA = Map({
    "type": Str(),
    "id": Id(),
    Optional("dependencies"): Map({
        "True": Seq(Id()) | EmptyList(),
        "False": Seq(Id()) | EmptyList()
    }),
    Optional("default"): Bool()
})

ARRAY_SCHEMA = Map({
    "type": Str(),
    "id": Id(),
    "max_entries": Int(),
    "properties": Seq(Any())
})

NUMBER_LIST_SCHEMA = Map({
    "type": Str(),
    "id": Id(),
    "numbers": Seq(Int() | Float()),
    Optional("default"): Int() | Float()
})

BASE_SCHEMA = Map({
    "device_type": Str(),
    "manufacturer_id": HexInt(),
    "device_id": HexInt(),
    "firmware_version": HexInt(),
    "protocol_version": HexInt(),
    Optional("device_name"): Str(),
    "properties": Seq(Any()),
    Optional("translation_data"): Seq(TRANSLATIONS_SCHEMA)
})

SCHEMAS = {
    "modifier": MODIFIER_SCHEMA,
    "item_selection": ITEM_SELECTION_SCHEMA,
    "time": TIME_SCHEMA,
    "integer": INTEGER_SCHEMA,
    "float": FLOAT_SCHEMA,
    "fixed": FIXED_POINT_SCHEMA,
    "string": STRING_SCHEMA,
    "bool": BOOL_SCHEMA,
    "array": ARRAY_SCHEMA,
    "number_list": NUMBER_LIST_SCHEMA,
    "language_selection": LANGUAGE_SELECTION_SCHEMA
}

def parse(path) -> YAML:
    """Parse a text file containing a YAML descriptor document into an object and validate it.

    Args:
        text (str): the string to parse from

    Returns:
        YAML: the YAML object created from the document
    """

    with open(path, "r") as yaml_text:
        text = yaml_text.read()
    par_path = os.sep.join(path.split(os.sep)[0:-1])
    pattern = re.compile(r"^.*?(?P<ws>[\t ]*)#[\t ]*include[\t ]*\"(?P<file>[^<>\s]+)\"$", re.MULTILINE)
    text = pattern.sub(lambda m: get_include(par_path, m.group("file"), len(m.group("ws"))), text)
    parsed = load(text, BASE_SCHEMA)
    try:
        _validate_config(parsed)
    except YAMLValidationError as ex:
        error(None, ex)
    return parsed

def get_properties(yaml_config: YAML) -> list:
    """Create a list of property objects from YAML descriptor.

    Args:
        yaml_config (YAML): the YAML descriptor

    Returns:
        list: the property objects
    """

    ids = get_ids(yaml_config)
    if len(ids) != len(set(ids)):
        error(None, "Descriptor contains repeated IDs")
    props = []
    has_language_prop = False
    for prop in yaml_config["properties"]:
        type_name = prop["type"].data
        if type_name == "language":
            if has_language_prop:
                error(prop, "Only one language property allowed")
            has_language_prop = True
        property_class = PROPERTY_TYPES[type_name]
        props.append(property_class(prop, ids, 1))
    return props

def get_device_info(yaml_config):
    """Create an object containing device info from YAML descriptor.

    Args:
        yaml_config (YAML): the YAML descriptor

    Returns:
        dict: the device info
    """

    info = {
        "device_type": yaml_config["device_type"].data,
        "manufacturer_id": yaml_config["manufacturer_id"].data,
        "device_id": yaml_config["device_id"].data,
        "firmware_version": yaml_config["firmware_version"].data,
        "protocol_version": yaml_config["protocol_version"].data,
        "device_name": None
    }
    if "device_name" in yaml_config:
        info["device_name"] = yaml_config["device_name"].data
    return info

def get_ids(yaml) -> list:
    """Create a list of all IDs in the YAML descriptor.

    Args:
        yaml_config (YAML): the YAML descriptor

    Returns:
        list: the IDs
    """

    ids = []
    _collect_ids(yaml, ids)
    if len(ids) > (65536):
        error(None, "Too many IDs (at most 65.536)")
    return ids

def _validate_config(parsed_config, array=False) -> None:
    for prop in parsed_config["properties"]:
        type_name = prop["type"].data
        if type_name == "language" and array:
            error(prop, "Language property not allowed in arrays")
        prop_type = PROPERTY_TYPES[type_name]
        schema = SCHEMAS[prop_type.category]
        prop.revalidate(schema)
        if prop_type.category == "array":
            _validate_config(prop, True)

def _collect_ids(yaml, ids):
    if "id" in yaml:
        ids.append(yaml["id"].data)
    if "entries" in yaml:
        for entry in yaml["entries"]:
            ids.append(entry.data)
    if "properties" in yaml:
        for prop in yaml["properties"]:
            _collect_ids(prop, ids)

def get_include(par_path, path, indent) -> str():
    full_path = path
    if par_path is not None and len(par_path.strip()) > 0:
        full_path = par_path + os.sep + full_path
    with open(full_path, "r") as inc_file:
        lines = inc_file.readlines()
        lines = map(lambda s: (" " * indent) + s, lines)
        return "".join(lines)
