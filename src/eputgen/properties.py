"""Provides classes for processing YAML descriptors.
"""

import math
from datetime import datetime
import struct
from typing import Tuple
from strictyaml import YAML

from .util import serialize_ascii, error, serialize_utf8, warn

TAB_SPACES = 4

TYPE_KEY = "type"
ID_KEY = "id"
PROPERTIES_KEY = "properties"
ENTRIES_KEY = "entries"
DEPENDENCIES_KEY = "dependencies"
MAX_ENTRIES_KEY = "max_entries"
MIN_VALUE_KEY = "min_value"
MAX_VALUE_KEY = "max_value"
STEP_SIZE_KEY = "step_size"
CONTENT_TYPE_KEY = "content_type"
CONTENT_TYPE_DEF_KEY = "content_type_def"
MAX_LENGTH_KEY = "max_length"
NUMBERS_KEY = "numbers"
SCALE_KEY = "scale"
DEFAULT_KEY = "default"

FLAG_MIN_VALUE = 0b00000001
FLAG_MAX_VALUE = 0b00000010
FLAG_STEP_SIZE = 0b00000100
FLAG_CONTENT_TYPE = 0b00001000
FLAG_CONT_DEF_TYPE = 0b00010000

READ_TEMPLATE = \
    "{accessor}{name} = {type_conversion_method}(buf + {data_index});\n"
WRITE_TEMPLATE = \
    "{type_conversion_method}({accessor}{name}, buf + {data_index});\n"

SAFE_GETTER_TEMPLATE = \
    "{rtype} get_{name}({rtype} {name})"

def _add_ascii(data: list, string: str) -> None:
    data.extend(serialize_ascii(string))

def _tab(depth: int = 1) -> str:
    return " " * TAB_SPACES * depth

def _to_short_bytes(val: int) -> bytes:
    return val.to_bytes(length=2, byteorder="big", signed=False)

class Property:
    """Base class for properties.
    Provides base implementations of all necessary methods.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        """Args:
            yaml_prop (YAML): YAML representation of property
            id_list (list): List of all existing IDs
            depth (int): Number of tabs to insert before lines
        """

        self.code = 0b00000000
        self.property = yaml_prop
        self.id_list = id_list
        self.depth = depth
        if ID_KEY in yaml_prop:
            self.identifier = yaml_prop[ID_KEY].data
            if not self.identifier.islower():
                warn(yaml_prop, "Avoid using uppercase characters in IDs.")
        else:
            self.identifier = None

    def get_data_size(self) -> int:
        """Return size of contained properties data in bytes.

        Returns:
            int: Size of data
        """

        return 0

    def serialize(self) -> list:
        """Serialize contained property into metadata byte array.

        Returns:
            list: Serialized metadata
        """

        serialized = [self.code]
        if self.identifier is not None:
            _add_ascii(serialized, self.identifier)
        return serialized

    def serialize_data(self) -> list:
        """Serialize contained property default value into data byte array.

        Returns:
            list: Serialized data
        """

        return None

    def generate_struct_member(self) -> str:
        """Generate C struct member definition for this property.

        Returns:
            str: Generated code
        """

        return None

    def generate_enums(self) -> str:
        """Generate C enums for contained options if available.

        Returns:
            str: Generated code or None
        """

        return None

    def generate_read_code(self, current_index: int, parent_member: str) -> str:
        """Generate C data parsing code for this property.

        Args:
            current_index (int): Current index in byte array
            parent_member (str): Prefix to use for member access in C code

        Returns:
            str: Generated code
        """

        return None

    def generate_write_code(self, current_index: int, parent_member: str) -> str:
        """Generate C data generation code for this property.

        Args:
            current_index (int): Current index in byte array
            parent_member (str): Prefix to use for member access in C code

        Returns:
            str: Generated code
        """

        return None

    def generate_safe_getter_code(self) -> Tuple[str, str]:
        """Generate C code performing sanity checks on data of this property.

        Returns:
            str: Function signature
            str: Function content
        """
        return None

class Divider(Property):
    """Divider modifier property.
    """

    category = "modifier"

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10000000

class Header(Property):
    """Header modifier property.
    """

    category = "modifier"

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10000001

class OneOutOfMProperty(Property):
    """One out of many selection property.
    """

    category = "item_selection"

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10000010
        self.entries = self.property[ENTRIES_KEY].data
        if len(self.entries) > 255:
            error(self.property, "Must have less than 256 entries")
        if DEPENDENCIES_KEY in self.property:
            self.dependencies = self.property[DEPENDENCIES_KEY].data
            if len(self.dependencies) > 255:
                error(self.property, "Must have less than 256 dependent options")
            entry_set = set(self.entries)
            id_set = set(self.id_list)
            dependency_set = set(self.dependencies.keys())
            if not dependency_set.issubset(entry_set):
                error(self.property, "Dependencies contain invalid option ID")
            for dep_ids in self.dependencies.values():
                if len(dep_ids) > 255:
                    error(self.property, "Option must have less than 256 dependencies")
                if not (set(dep_ids)).issubset(id_set):
                    error(self.property, "Dependencies contain non-existant ID")
                if self.identifier in dep_ids:
                    error(self.property, "Can't be dependent on own ID")
        else:
            self.dependencies = {}
        if DEFAULT_KEY in self.property:
            default_entry = self.property[DEFAULT_KEY].data
            self.default = self.entries.index(default_entry) + 1
            # 0 means no choice, indexing starts at 1, so add 1
        else:
            self.default = 0

    def get_data_size(self) -> int:
        return 1

    def serialize(self) -> list:
        serialized = super().serialize()
        entry_count = len(self.entries)
        serialized.append(entry_count)
        for entry in self.entries:
            _add_ascii(serialized, entry)
        deps_count = len(self.dependencies)
        serialized.append(deps_count)
        for opt_id, dep_ids in self.dependencies.items():
            serialized.append(self.entries.index(opt_id))
            serialized.append(len(dep_ids))
            for dep_id in dep_ids:
                ser = _to_short_bytes(self.id_list.index(dep_id))
                serialized.extend(ser)
        return serialized

    def serialize_data(self) -> list:
        return [self.default]

    def generate_struct_member(self) -> str:
        return _tab(self.depth) + f"uint8_t {self.identifier};\n"

    def generate_enums(self) -> str:
        lines = [_tab() + f"{entry}={i},\n" for i, entry in enumerate(self.entries)]
        return "typedef enum {\n" + "".join(lines) + f"}} {self.identifier}_options;\n"

    def generate_read_code(self, current_index: int, parent_member: str) -> str:
        return _tab(1) + READ_TEMPLATE.format(
            accessor=parent_member,
            name=self.identifier,
            type_conversion_method="bytes_to_uint8",
            data_index=current_index)

    def generate_write_code(self, current_index: int, parent_member: str) -> str:
        return _tab(1) + WRITE_TEMPLATE.format(
            accessor=parent_member,
            name=self.identifier,
            type_conversion_method="uint8_to_bytes",
            data_index=current_index)

    def generate_safe_getter_code(self) -> Tuple[str, str]:
        entry_count = len(self.entries)
        signature = SAFE_GETTER_TEMPLATE.format(
            rtype="uint8_t",
            name=self.identifier
        )
        tab = _tab()
        content = f"""{signature} {{
{tab}if ({self.identifier} > {entry_count}) {{
{tab}{tab}return 0;
{tab}}} else {{
{tab}{tab}return {self.identifier};
{tab}}}
}}"""
        return signature + ";", content

class NOutOfMProperty(Property):
    """Many out of many selection property.
    """

    category = "item_selection"

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10000011
        self.entries = self.property[ENTRIES_KEY].data
        if len(self.entries) > 255:
            error(self.property, "Must have less than 256 entries")
        if DEPENDENCIES_KEY in self.property:
            self.dependencies = self.property[DEPENDENCIES_KEY].data
            if len(self.dependencies) > 255:
                error(self.property, "Must have less than 256 dependent options")
            entry_set = set(self.entries)
            id_set = set(self.id_list)
            dependency_set = set(self.dependencies.keys())
            if not dependency_set.issubset(entry_set):
                error(self.property, "Dependencies contain invalid option ID")
            for dep_ids in self.dependencies.values():
                if len(dep_ids) > 255:
                    error(self.property, "Option must have less than 256 dependencies")
                if not (set(dep_ids)).issubset(id_set):
                    error(self.property, "Dependencies contain non-existant ID")
                if self.identifier in dep_ids:
                    error(self.property, "Can't be dependent on own ID")
        else:
            self.dependencies = {}
        self.default = []
        for i in range(0, self.get_data_size()):
            self.default.append(0)
        if DEFAULT_KEY in self.property:
            default_entries = self.property[DEFAULT_KEY].data
            default_indices = map(self.entries.index, default_entries)
            for i in default_indices:
                array_index = math.ceil(i / 8) - 1
                self.default[array_index] = self.default[array_index] | (1 << (i % 8))

    def get_data_size(self) -> int:
        entry_count = len(self.entries)
        return math.ceil(entry_count / 8)

    def serialize(self) -> list:
        serialized = super().serialize()
        entry_count = len(self.entries)
        serialized.append(entry_count)
        for entry in self.entries:
            _add_ascii(serialized, entry)
        deps_count = len(self.dependencies)
        serialized.append(deps_count)
        for opt_id, dep_ids in self.dependencies.items():
            serialized.append(self.entries.index(opt_id))
            serialized.append(len(dep_ids))
            for dep_id in dep_ids:
                ser = _to_short_bytes(self.id_list.index(dep_id))
                serialized.extend(ser)
        return serialized

    def serialize_data(self) -> list:
        return self.default

    def generate_struct_member(self) -> str:
        return _tab(self.depth) + f"uint8_t {self.identifier}[{self.get_data_size()}];\n"

    def generate_enums(self) -> str:
        lines = [_tab() + f"{entry}={i},\n" for i, entry in enumerate(self.entries)]
        return "typedef enum {\n" + "".join(lines) + f"}} {self.identifier}_options;\n"

    def generate_read_code(self, current_index: int, parent_member: str) -> str:
        return (_tab(1) + f"for (int i = 0; i < {self.get_data_size()}; i++) {{\n" +
                _tab(2) +
                f"{parent_member}{self.identifier}[i] = *(buf + {current_index} + i);\n" +
                _tab(1) + "}\n")

    def generate_write_code(self, current_index: int, parent_member: str) -> str:
        return (_tab(1) + f"for (int i = 0; i < {self.get_data_size()}; i++) {{\n" +
                _tab(2) +
                f"*(buf + {current_index} + i) = {parent_member}{self.identifier}[i];\n" +
                _tab(1) + "}\n")

class BoolProperty(Property):
    """Bool property.
    """

    category = "bool"

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10000100
        if DEPENDENCIES_KEY in self.property:
            self.dependencies_true = self.property[DEPENDENCIES_KEY]["True"].data
            self.dependencies_false = self.property[DEPENDENCIES_KEY]["False"].data
            if len(self.dependencies_true) > 255 or len(self.dependencies_false) > 255:
                error(self.property, "Must have less than 256 dependencies")
            dependency_true_set = set(self.dependencies_true)
            dependency_false_set = set(self.dependencies_false)
            id_set = set(self.id_list)
            if (not dependency_true_set.issubset(id_set)
                    or not dependency_false_set.issubset(id_set)):
                error(self.property, "Dependencies contain non-existant ID")
            if self.identifier in self.dependencies_true or self.identifier in self.dependencies_false:
                error(self.property, "Can't be dependent on own ID")
        else:
            self.dependencies_true = {}
            self.dependencies_false = {}
        if DEFAULT_KEY in self.property:
            default_val = self.property[DEFAULT_KEY].data
            if default_val:
                self.default = 1
            else:
                self.default = 0
        else:
            self.default = 0

    def get_data_size(self) -> int:
        return 1

    def serialize(self) -> list:
        serialized = super().serialize()
        serialized.append(len(self.dependencies_true))
        for dep_id in self.dependencies_true:
            ser = _to_short_bytes(self.id_list.index(dep_id))
            serialized.extend(ser)
        serialized.append(len(self.dependencies_false))
        for dep_id in self.dependencies_false:
            ser = _to_short_bytes(self.id_list.index(dep_id))
            serialized.extend(ser)
        return serialized

    def serialize_data(self) -> list:
        return [self.default]

    def generate_struct_member(self) -> str:
        return _tab(self.depth) + f"uint8_t {self.identifier};\n"

    def generate_read_code(self, current_index: int, parent_member: str) -> str:
        return _tab(1) + READ_TEMPLATE.format(
            accessor=parent_member,
            name=self.identifier,
            type_conversion_method="bytes_to_bool",
            data_index=current_index)

    def generate_write_code(self, current_index: int, parent_member: str) -> str:
        return _tab(1) + WRITE_TEMPLATE.format(
            accessor=parent_member,
            name=self.identifier,
            type_conversion_method="bool_to_bytes",
            data_index=current_index)

class ArrayProperty(Property):
    """Array property.
    """

    category = "array"

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10000101
        self.sub_properties = []
        for sub_prop_yaml in self.property[PROPERTIES_KEY]:
            prop_class = PROPERTY_TYPES[sub_prop_yaml[TYPE_KEY].data]
            sub_prop = prop_class(sub_prop_yaml, self.id_list, depth + 1)
            self.sub_properties.append(sub_prop)
        if len(self.sub_properties) > 255:
            raise Exception("Must have less than 256 properties")
        self.max_entries = self.property[MAX_ENTRIES_KEY].data

    def get_data_size(self) -> int:
        return sum(map(lambda s: s.get_data_size(), self.sub_properties)) * self.max_entries

    def serialize(self) -> list:
        serialized = super().serialize()
        serialized.append(self.max_entries)
        serialized.append(len(self.sub_properties))
        for sub_prop in self.sub_properties:
            serialized.extend(sub_prop.serialize())
        return serialized

    def serialize_data(self) -> list:
        arr = []
        for _ in range(0, self.max_entries):
            for prop in self.sub_properties:
                res = prop.serialize_data()
                if res is not None:
                    arr.extend(res)
        return arr

    def generate_struct_member(self) -> str:
        members = [sub_prop.generate_struct_member() for sub_prop in self.sub_properties]
        return (_tab(self.depth) + "struct {\n" +
                "".join(filter(lambda x: x is not None, members)) +
                _tab(self.depth) + f"}} {self.identifier}[{self.max_entries}];\n")

    def generate_enums(self) -> str:
        enums = [sub_prop.generate_enums() for sub_prop in self.sub_properties]
        return "\n".join(filter(lambda x: x is not None, enums))

    def generate_read_code(self, current_index: int, parent_member: str) -> str:
        data_index = current_index
        lines = []
        for instance in range(0, self.max_entries):
            for sub_prop in self.sub_properties:
                member_read = sub_prop.generate_read_code(
                    data_index,
                    f"{parent_member}{self.identifier}[{instance}].")
                data_index += sub_prop.get_data_size()
                lines.append(member_read)
        return "".join(filter(lambda x: x is not None, lines))

    def generate_write_code(self, current_index: int, parent_member: str) -> str:
        data_index = current_index
        lines = []
        for instance in range(0, self.max_entries):
            for sub_prop in self.sub_properties:
                member_write = sub_prop.generate_write_code(
                    data_index,
                    f"{parent_member}{self.identifier}[{instance}].")
                data_index += sub_prop.get_data_size()
                lines.append(member_write)
        return "".join(filter(lambda x: x is not None, lines))

    def generate_safe_getter_code(self) -> Tuple[str, str]:
        getters = [sub_prop.generate_safe_getter_code() for sub_prop in self.sub_properties]
        getters = list(filter(lambda x: x is not None, getters))
        if len(getters) > 0:
            signatures = [getter[0] for getter in getters]
            functions = [getter[1] for getter in getters]
            signatures = "\n".join(signatures)
            functions = "\n".join(functions)
            return (signatures, functions)
        return None

class BaseIntegerProperty(Property):
    """Base class for numeric properties.
    """

    category = "integer"

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 0
        self.code = 0b00000000
        self.read_converter = None
        self.write_converter = None
        self.type_name = None
        self.step_size = None
        self.min_val = None
        self.max_val = None
        self.content_type = None
        self.content_type_def = None
        if STEP_SIZE_KEY in self.property:
            self.step_size = self.property[STEP_SIZE_KEY].data
            if self.step_size < 0:
                error(self.property, "step_size must be > 0")
        if MIN_VALUE_KEY in self.property:
            self.min_val = self.property[MIN_VALUE_KEY].data
            if not self._is_signed() and self.min_val < 0:
                error(self.property, "Type is unsigned, can't have min_value < 0")
            if self.step_size is not None and self.min_val % self.step_size != 0:
                warn(self.property, f"min_value is not a multiple of step_size")
        if MAX_VALUE_KEY in self.property:
            self.max_val = self.property[MAX_VALUE_KEY].data
            if not self._is_signed() and self.max_val < 0:
                error(self.property, "Type is unsigned, can't have max_value < 0")
            if self.step_size is not None and self.max_val % self.step_size != 0:
                warn(self.property, f"max_value is not a multiple of step_size")
        if CONTENT_TYPE_KEY in self.property:
            self.content_type = self.property[CONTENT_TYPE_KEY].data
            if CONTENT_TYPE_DEF_KEY in self.property:
                self.content_type_def = self.property[CONTENT_TYPE_DEF_KEY].data
        self.extra_flags = 0x00
        if self.min_val is not None:
            self.extra_flags |= FLAG_MIN_VALUE
        if self.max_val is not None:
            self.extra_flags |= FLAG_MAX_VALUE
        if self.step_size is not None:
            self.extra_flags |= FLAG_STEP_SIZE
        if self.content_type is not None:
            self.extra_flags |= FLAG_CONTENT_TYPE
            if self.content_type_def is not None:
                self.extra_flags |= FLAG_CONT_DEF_TYPE
        if DEFAULT_KEY in self.property:
            self.default = self.property[DEFAULT_KEY].data
        else:
            self.default = 0

    def _is_signed(self) -> bool:
        return False

    def _val_to_bytes(self, val) -> bytes:
        return val.to_bytes(length=self.data_size, byteorder="big", signed=self._is_signed())

    def get_data_size(self) -> int:
        return self.data_size

    def serialize(self) -> list:
        serialized = super().serialize()
        serialized.append(self.extra_flags)
        if self.min_val is not None:
            serialized.extend(self._val_to_bytes(self.min_val))
        if self.max_val is not None:
            serialized.extend(self._val_to_bytes(self.max_val))
        if self.step_size is not None:
            serialized.extend(self._val_to_bytes(self.step_size))
        if self.content_type is not None:
            serialized.append(NUMBER_CONTENT_TYPES[self.content_type])
            if self.content_type_def is not None:
                try:
                    default_type = NUMBER_CONTENT_TYPE_DEFS[self.content_type][self.content_type_def]
                except KeyError:
                    default_type = 0
                serialized.append(default_type)
        return serialized

    def serialize_data(self) -> list:
        arr = []
        arr.extend(self._val_to_bytes(self.default))
        return arr

    def generate_struct_member(self) -> str:
        return _tab(self.depth) + f"{self.type_name} {self.identifier};\n"

    def generate_read_code(self, current_index: int, parent_member: str) -> str:
        return _tab(1) + READ_TEMPLATE.format(
            accessor=parent_member,
            name=self.identifier,
            type_conversion_method=self.read_converter,
            data_index=current_index)

    def generate_write_code(self, current_index: int, parent_member: str) -> str:
        return _tab(1) + WRITE_TEMPLATE.format(
            accessor=parent_member,
            name=self.identifier,
            type_conversion_method=self.write_converter,
            data_index=current_index)

    def generate_safe_getter_code(self) -> Tuple[str, str]:
        signature = SAFE_GETTER_TEMPLATE.format(
            rtype=self.type_name,
            name=self.identifier
        )
        tab = _tab()
        content = signature + " {\n"
        if self.min_val is not None:
            content += f"""{tab}if ({self.identifier} < {self.min_val}) {{
{tab}{tab}return {self.min_val};
{tab}}}
"""
        if self.max_val is not None:
            content += f"""{tab}if ({self.identifier} > {self.max_val}) {{
{tab}{tab}return {self.max_val};
{tab}}}
"""
        if self.step_size is not None:
            content += f"""{tab}if ({self.identifier} % {self.step_size} != 0) {{
{tab}{tab}return ({self.identifier} / {self.step_size}) * {self.step_size};
{tab}}}
"""
        content += f"{tab}return {self.identifier};\n}}"
        return signature + ";", content

class UInt8Property(BaseIntegerProperty):
    """8 bit unsigned integer property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 1
        self.code = 0b10000110
        self.read_converter = "bytes_to_uint8"
        self.write_converter = "uint8_to_bytes"
        self.type_name = "uint8_t"

class UInt16Property(BaseIntegerProperty):
    """16 bit unsigned integer property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 2
        self.code = 0b10000111
        self.read_converter = "bytes_to_uint16"
        self.write_converter = "uint16_to_bytes"
        self.type_name = "uint16_t"

class UInt32Property(BaseIntegerProperty):
    """32 bit unsigned integer property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 4
        self.code = 0b10001000
        self.read_converter = "bytes_to_uint32"
        self.write_converter = "uint32_to_bytes"
        self.type_name = "uint32_t"

class UInt64Property(BaseIntegerProperty):
    """64 bit unsigned integer property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 8
        self.code = 0b10001001
        self.read_converter = "bytes_to_uint64"
        self.write_converter = "uint64_to_bytes"
        self.type_name = "uint64_t"

class Int8Property(BaseIntegerProperty):
    """8 bit signed integer property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 1
        self.code = 0b10001010
        self.read_converter = "bytes_to_int8"
        self.write_converter = "int8_to_bytes"
        self.type_name = "int8_t"

    def _is_signed(self) -> bool:
        return True

class Int16Property(BaseIntegerProperty):
    """16 bit signed integer property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 2
        self.code = 0b10001011
        self.read_converter = "bytes_to_int16"
        self.write_converter = "int16_to_bytes"
        self.type_name = "int16_t"

    def _is_signed(self) -> bool:
        return True

class Int32Property(BaseIntegerProperty):
    """32 bit signed integer property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 4
        self.code = 0b10001100
        self.read_converter = "bytes_to_int32"
        self.write_converter = "int32_to_bytes"
        self.type_name = "int32_t"

    def _is_signed(self) -> bool:
        return True

class Int64Property(BaseIntegerProperty):
    """64 bit signed integer property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 8
        self.code = 0b10001101
        self.read_converter = "bytes_to_int64"
        self.write_converter = "int64_to_bytes"
        self.type_name = "int64_t"

    def _is_signed(self) -> bool:
        return True

class BaseFloatProperty(BaseIntegerProperty):
    """Base class for floating point properties.
    """

    category = "float"

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.type_format = None

    def _is_signed(self) -> bool:
        return True

    def _val_to_bytes(self, val) -> bytes:
        return struct.pack(self.type_format, val)

class Float32Property(BaseFloatProperty):
    """32 bit signed floating point property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 4
        self.code = 0b10001110
        self.read_converter = "bytes_to_float"
        self.write_converter = "float_to_bytes"
        self.type_name = "float"
        self.type_format = ">f"

class Float64Property(BaseFloatProperty):
    """64 bit signed floating point property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 8
        self.code = 0b10001111
        self.read_converter = "bytes_to_double"
        self.write_converter = "double_to_bytes"
        self.type_name = "double"
        self.type_format = ">d"

class BaseNumberListProperty(Property):
    """Base class for number entry only supporting list of discrete values.
    """

    category = "number_list"

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.read_converter = None
        self.write_converter = None
        self.type_name = None
        self.entries = yaml_prop[NUMBERS_KEY].data
        if len(self.entries) > 65535:
            error(yaml_prop, "List must have less than 65536 entries")
        if len(self.entries) < 1:
            error(yaml_prop, "Property has no entries")
        if DEFAULT_KEY in self.property:
            self.default = self.property[DEFAULT_KEY].data
        else:
            self.default = self.entries[0]

    def _val_to_bytes(self, val) -> bytes:
        return val.to_bytes(length=self.get_data_size(), byteorder="big", signed=True)

    def get_data_size(self) -> int:
        return 8

    def serialize(self) -> list:
        serialized = super().serialize()
        serialized.extend(_to_short_bytes(len(self.entries)))
        for number in self.entries:
            serialized.extend(self._val_to_bytes(number))
        return serialized

    def serialize_data(self) -> list:
        arr = []
        arr.extend(self._val_to_bytes(self.default))
        return arr

    def generate_struct_member(self) -> str:
        return _tab(self.depth) + f"{self.type_name} {self.identifier};\n"

    def generate_read_code(self, current_index: int, parent_member: str) -> str:
        return _tab(1) + READ_TEMPLATE.format(
            accessor=parent_member,
            name=self.identifier,
            type_conversion_method=self.read_converter,
            data_index=current_index)

    def generate_write_code(self, current_index: int, parent_member: str) -> str:
        return _tab(1) + WRITE_TEMPLATE.format(
            accessor=parent_member,
            name=self.identifier,
            type_conversion_method=self.write_converter,
            data_index=current_index)

    def generate_safe_getter_code(self) -> Tuple[str, str]:
        signature = SAFE_GETTER_TEMPLATE.format(
            rtype=self.type_name,
            name=self.identifier
        )
        tab = _tab()
        content = signature + " {\n"
        for entry in self.entries:
            content += f"""{tab}if ({self.identifier} == {entry}) {{
{tab}{tab}return {self.identifier};
{tab}{tab}}}
"""
        content += f"{tab}return {self.entries[0]};\n}}"
        return signature + ";", content

class IntNumberListProperty(BaseNumberListProperty):
    """Discrete number entry with integers.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10010000
        self.read_converter = "bytes_to_int64"
        self.write_converter = "int64_to_bytes"
        self.type_name = "int64_t"

class DoubleNumberListProperty(BaseNumberListProperty):
    """Discrete number entry with doubles.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10010001
        self.read_converter = "bytes_to_double"
        self.write_converter = "double_to_bytes"
        self.type_name = "double"

    def _val_to_bytes(self, val) -> bytes:
        return struct.pack(">d", val)

class BaseDateProperty(Property):
    """Base class for date properties.
    """

    category = "time"

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.type_name = "time_point"
        self.read_converter = "bytes_to_time_point"
        self.write_converter = "time_point_to_bytes"
        if DEFAULT_KEY in self.property:
            self.default = self.property[DEFAULT_KEY].data
        else:
            self.default = None

    def get_data_size(self) -> int:
        return 8

    def serialize_data(self) -> list:
        if self.default is not None:
            utc_time = datetime.strptime(self.default, "%Y-%m-%dT%H:%M:%S.%fZ")
            val = int((utc_time - datetime(1970, 1, 1)).total_seconds() * 1000)
        else:
            val = 0
        return list(val.to_bytes(length=8, byteorder="big", signed=True))

    def generate_struct_member(self) -> str:
        return _tab(self.depth) + f"{self.type_name} {self.identifier};\n"

    def generate_read_code(self, current_index: int, parent_member: str) -> str:
        return _tab(1) + READ_TEMPLATE.format(
            accessor=parent_member,
            name=self.identifier,
            type_conversion_method=self.read_converter,
            data_index=current_index)

    def generate_write_code(self, current_index: int, parent_member: str) -> str:
        return _tab(1) + WRITE_TEMPLATE.format(
            accessor=parent_member,
            name=self.identifier,
            type_conversion_method=self.write_converter,
            data_index=current_index)

class DateProperty(BaseDateProperty):
    """Date property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10010010

class DateTimeProperty(BaseDateProperty):
    """DateTime property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10010011

class TimeProperty(BaseDateProperty):
    """Time property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10010100
        self.type_name = "hh_mm_ss"
        self.read_converter = "bytes_to_hh_mm_ss"
        self.write_converter = "hh_mm_ss_to_bytes"
        if DEFAULT_KEY in self.property:
            self.default = self.property[DEFAULT_KEY].data
        else:
            self.default = None

    def get_data_size(self) -> int:
        return 3

    def serialize_data(self) -> list:
        if self.default is not None:
            time = datetime.strptime(self.default, "%H:%M:%S")
            val = [time.hour, time.minute, time.second]
        else:
            val = [0, 0, 0]
        return val

    def generate_safe_getter_code(self) -> Tuple[str, str]:
        signature = SAFE_GETTER_TEMPLATE.format(
            rtype=self.type_name,
            name=self.identifier
        )
        tab = _tab()
        content = f"""{signature} {{
{tab}hh_mm_ss return_val = {{
{tab}{tab}{self.identifier}.hours,
{tab}{tab}{self.identifier}.minutes,
{tab}{tab}{self.identifier}.seconds
{tab}}};
{tab}if (return_val.hours > 23) {{
{tab}{tab}return_val.hours = 23;
{tab}}}
{tab}if (return_val.minutes > 59) {{
{tab}{tab}return_val.minutes = 59;
{tab}}}
{tab}if (return_val.seconds > 59) {{
{tab}{tab}return_val.seconds = 59;
{tab}}}
{tab}return return_val;
}}
"""
        return signature + ";", content

class ZonedDateTimeProperty(BaseDateProperty):
    """DateTime with timezone property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10010101
        self.type_name = "zoned_time"
        self.read_converter = "bytes_to_zoned_time"
        self.write_converter = "zoned_time_to_bytes"

    def get_data_size(self) -> int:
        return 10

    def serialize_data(self) -> list:
        if self.default is not None:
            zoned_time = datetime.strptime(self.default, "%Y-%m-%dT%H:%M:%S.%f%z")
            val = int((zoned_time - datetime(1970, 1, 1, tzinfo=zoned_time.tzinfo)).total_seconds() * 1000)
            tz_info = zoned_time.utcoffset()
            offset = int(tz_info.total_seconds() / 60)
        else:
            val = 0
            offset = 0
        val_bytes = val.to_bytes(length=8, byteorder="big", signed=True)
        offset_bytes = offset.to_bytes(length=2, byteorder="big", signed=True)
        arr = []
        arr.extend(val_bytes)
        arr.extend(offset_bytes)
        return arr

class DateRangeProperty(BaseDateProperty):
    """Date range property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10010111
        self.type_name = "date_range"
        self.read_converter = "bytes_to_date_range"
        self.write_converter = "date_range_to_bytes"
        if DEFAULT_KEY in self.property:
            self.default = self.property[DEFAULT_KEY].data
        else:
            self.default = None

    def get_data_size(self) -> int:
        return 16

    def serialize_data(self) -> list:
        arr = []
        if self.default is not None:
            rang = self.default.split(";")
            utc_time_from = datetime.strptime(rang[0], "%Y-%m-%dT%H:%M:%S.%fZ")
            utc_time_to = datetime.strptime(rang[1], "%Y-%m-%dT%H:%M:%S.%fZ")
            default_from = int((utc_time_from - datetime(1970, 1, 1)).total_seconds() * 1000)
            default_to = int((utc_time_to - datetime(1970, 1, 1)).total_seconds() * 1000)
        else:
            default_from = 0
            default_to = 0
        arr.extend(default_from.to_bytes(length=8, byteorder="big", signed=True))
        arr.extend(default_to.to_bytes(length=8, byteorder="big", signed=True))
        return arr

class DateTimeRangeProperty(DateRangeProperty):
    """DateTime range property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10011000

class TimeRangeProperty(BaseDateProperty):
    """Time range property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10011001
        self.type_name = "time_range"
        self.read_converter = "bytes_to_time_range"
        self.write_converter = "time_range_to_bytes"
        if DEFAULT_KEY in self.property:
            self.default = self.property[DEFAULT_KEY].data
        else:
            self.default = None

    def get_data_size(self) -> int:
        return 6

    def serialize_data(self) -> list:
        if self.default is not None:
            rang = self.default.split(";")
            default_from = datetime.strptime(rang[0], "%H:%M:%S")
            default_to = datetime.strptime(rang[1], "%H:%M:%S")
            return [
                default_from.hour,
                default_from.minute,
                default_from.second,
                default_to.hour,
                default_to.minute,
                default_to.second
            ]
        else:
            return [0, 0, 0, 0, 0, 0]

    def generate_safe_getter_code(self) -> Tuple[str, str]:
        signature = SAFE_GETTER_TEMPLATE.format(
            rtype=self.type_name,
            name=self.identifier
        )
        tab = _tab()
        content = f"""{signature} {{
{tab}hh_mm_ss return_val_from = {{
{tab}{tab}{self.identifier}.from.hours,
{tab}{tab}{self.identifier}.from.minutes,
{tab}{tab}{self.identifier}.from.seconds
{tab}}};
{tab}if (return_val_from.hours > 23) {{
{tab}{tab}return_val_from.hours = 23;
{tab}}}
{tab}if (return_val_from.minutes > 59) {{
{tab}{tab}return_val_from.minutes = 59;
{tab}}}
{tab}if (return_val_from.seconds > 59) {{
{tab}{tab}return_val_from.seconds = 59;
{tab}}}
{tab}hh_mm_ss return_val_to = {{
{tab}{tab}{self.identifier}.to.hours,
{tab}{tab}{self.identifier}.to.minutes,
{tab}{tab}{self.identifier}.to.seconds
{tab}}};
{tab}if (return_val_to.hours > 23) {{
{tab}{tab}return_val_to.hours = 23;
{tab}}}
{tab}if (return_val_to.minutes > 59) {{
{tab}{tab}return_val_to.minutes = 59;
{tab}}}
{tab}if (return_val_to.seconds > 59) {{
{tab}{tab}return_val_to.seconds = 59;
{tab}}}
{tab}time_range return_val = {{return_val_from, return_val_to}};
{tab}return return_val;
}}
"""
        return signature + ";", content

class StringProperty(Property):
    """Base class for string properties.
    """

    category = "string"

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.max_len = self.property[MAX_LENGTH_KEY].data
        self.data_len = self.max_len - 1
        self.default = None

    def get_data_size(self) -> int:
        return self.data_len

    def serialize(self) -> list:
        serialized = super().serialize()
        serialized.append(self.max_len)
        return serialized

    def serialize_data(self) -> list:
        return self.default

    def generate_struct_member(self) -> str:
        return _tab(self.depth) + f"uint8_t {self.identifier}[{self.max_len}];\n"

    def generate_read_code(self, current_index: int, parent_member: str) -> str:
        return (_tab(1) + f"for (int i = 0; i < {self.data_len}; i++) {{\n" +
                _tab(2) +
                f"{parent_member}{self.identifier}[i] = *(buf + {current_index} + i);\n" +
                _tab(1) + "}\n")

    def generate_write_code(self, current_index: int, parent_member: str) -> str:
        return (_tab(1) + f"for (int i = 0; i < {self.data_len}; i++) {{\n" +
                _tab(2) +
                f"*(buf + {current_index} + i) = {parent_member}{self.identifier}[i];\n" +
                _tab(1) + "}\n")

class AsciiStringProperty(StringProperty):
    """ASCII string property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10011010
        self.default = []
        if DEFAULT_KEY in self.property:
            default_val = self.property[DEFAULT_KEY].data
            self.default.extend(serialize_ascii(default_val))
            if len(self.default) > self.data_len:
                error(self.property, "Default value must not exceed max_length - 1")
            for _ in range(0, self.data_len - len(self.default)):
                self.default.append(0)
        else:
            for _ in range(0, self.data_len):
                self.default.append(0)

class Utf8StringProperty(StringProperty):
    """UTF8 string property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10011011
        self.default = []
        if DEFAULT_KEY in self.property:
            default_val = self.property[DEFAULT_KEY].data
            self.default.extend(serialize_utf8(default_val))
            if len(self.default) > self.data_len:
                error(self.property, "Default value must not exceed max_length - 1")
            for _ in range(0, self.data_len - len(self.default)):
                self.default.append(0)
        else:
            for _ in range(0, self.data_len):
                self.default.append(0)

class EmailProperty(Utf8StringProperty):
    """Email address property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10011100

class PhoneProperty(Utf8StringProperty):
    """Phone number property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10011101

class UriProperty(Utf8StringProperty):
    """URI property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10011110

class PasswordProperty(Utf8StringProperty):
    """Password property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10011111

class BaseFixedPointProperty(Property):
    """Base class for fixed point numeric properties.
    """

    category = "fixed"

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 0
        self.code = 0b00000000
        self.read_converter = None
        self.write_converter = None
        self.type_name = None
        self.scale = self.property[SCALE_KEY].data
        self.min_val = None
        self.max_val = None
        self.content_type = None
        self.content_type_def = None
        if MIN_VALUE_KEY in self.property:
            self.min_val = self.property[MIN_VALUE_KEY].data
        if MAX_VALUE_KEY in self.property:
            self.max_val = self.property[MAX_VALUE_KEY].data
        if CONTENT_TYPE_KEY in self.property:
            self.content_type = self.property[CONTENT_TYPE_KEY].data
            if CONTENT_TYPE_DEF_KEY in self.property:
                self.content_type_def = self.property[CONTENT_TYPE_DEF_KEY].data
        self.extra_flags = 0x00
        if self.min_val is not None:
            self.extra_flags |= FLAG_MIN_VALUE
        if self.max_val is not None:
            self.extra_flags |= FLAG_MAX_VALUE
        if self.content_type is not None:
            self.extra_flags |= FLAG_CONTENT_TYPE
            if self.content_type_def is not None:
                self.extra_flags |= FLAG_CONT_DEF_TYPE
        if DEFAULT_KEY in self.property:
            self.default = self.property[DEFAULT_KEY].data
        else:
            self.default = 0

    def _val_to_bytes(self, val) -> bytes:
        return val.to_bytes(length=self.data_size, byteorder="big", signed=True)

    def get_data_size(self) -> int:
        return self.data_size

    def serialize(self) -> list:
        serialized = super().serialize()
        serialized.extend(self.scale.to_bytes(length=4, byteorder="big", signed=True))
        serialized.append(self.extra_flags)
        if self.min_val is not None:
            serialized.extend(self._val_to_bytes(self.min_val))
        if self.max_val is not None:
            serialized.extend(self._val_to_bytes(self.max_val))
        if self.content_type is not None:
            serialized.append(NUMBER_CONTENT_TYPES[self.content_type])
            if self.content_type_def is not None:
                try:
                    default_type = NUMBER_CONTENT_TYPE_DEFS[self.content_type][self.content_type_def]
                except KeyError:
                    default_type = 0
                serialized.append(default_type)
        return serialized

    def serialize_data(self) -> list:
        return list(self._val_to_bytes(self.default))

    def generate_struct_member(self) -> str:
        return _tab(self.depth) + f"{self.type_name} {self.identifier};\n"

    def generate_read_code(self, current_index: int, parent_member: str) -> str:
        return f"{_tab(1)}{parent_member}{self.identifier} = {self.read_converter}(buf + {current_index}, {self.scale});\n"

    def generate_write_code(self, current_index: int, parent_member: str) -> str:
        return f"{_tab(1)}{self.write_converter}({parent_member}{self.identifier}, buf + {current_index});\n"

    def generate_safe_getter_code(self) -> Tuple[str, str]:
        signature = SAFE_GETTER_TEMPLATE.format(
            rtype=self.type_name,
            name=self.identifier
        )
        tab = _tab()
        content = signature + " {\n"
        if self.min_val is not None:
            content += f"""{tab}if ({self.identifier} < {self.min_val}) {{
{tab}{tab}return {self.min_val};
{tab}}}
"""
        if self.max_val is not None:
            content += f"""{tab}if ({self.identifier} > {self.max_val}) {{
{tab}{tab}return {self.max_val};
{tab}}}
"""
        content += f"{tab}return {self.identifier};\n}}"
        return signature + ";", content

class FixedPoint32Property(BaseFixedPointProperty):
    """32 bit fixed point property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 4
        self.code = 0b10100000
        self.read_converter = "bytes_to_fixp32"
        self.write_converter = "fixp32_to_bytes"
        self.type_name = "fixp32"

class FixedPoint64Property(BaseFixedPointProperty):
    """64 bit fixed point property.
    """

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.data_size = 8
        self.code = 0b10100001
        self.read_converter = "bytes_to_fixp64"
        self.write_converter = "fixp64_to_bytes"
        self.type_name = "fixp64"

class LanguageProperty(OneOutOfMProperty):
    """Language selection property.
    """

    category = "language_selection"

    def __init__(self, yaml_prop: YAML, id_list: list, depth: int) -> None:
        super().__init__(yaml_prop, id_list, depth)
        self.code = 0b10100010

PROPERTY_TYPES = {
    "divider":            Divider,
    "header":             Header,
    "one_out_of_m":       OneOutOfMProperty,
    "n_out_of_m":         NOutOfMProperty,
    "bool":               BoolProperty,
    "array":              ArrayProperty,
    "uint8_t":            UInt8Property,
    "uint16_t":           UInt16Property,
    "uint32_t":           UInt32Property,
    "uint64_t":           UInt64Property,
    "int8_t":             Int8Property,
    "int16_t":            Int16Property,
    "int32_t":            Int32Property,
    "int64_t":            Int64Property,
    "float":              Float32Property,
    "double":             Float64Property,
    "number_list_int":    IntNumberListProperty,
    "number_list_double": DoubleNumberListProperty,
    "date":               DateProperty,
    "date_time":          DateTimeProperty,
    "time":               TimeProperty,
    "zoned_date_time":    ZonedDateTimeProperty,
    "date_range":         DateRangeProperty,
    "date_time_range":    DateTimeRangeProperty,
    "time_range":         TimeRangeProperty,
    "str_ascii":          AsciiStringProperty,
    "str_utf8":           Utf8StringProperty,
    "str_mail":           EmailProperty,
    "str_phone":          PhoneProperty,
    "str_uri":            UriProperty,
    "str_pwd":            PasswordProperty,
    "fixp32":             FixedPoint32Property,
    "fixp64":             FixedPoint64Property,
    "language":           LanguageProperty
}

NUMBER_CONTENT_TYPES = {
    "none": 0,
    "time": 1,
    "weight": 2,
    "length": 3
}

NUMBER_CONTENT_TYPE_DEFS = {
    "none": {},
    "time": {
        "ms": 0,
        "s": 1,
        "m": 2,
        "h": 3,
        "d": 4
    },
    "weight": {
        "mg": 0,
        "g": 0,
        "kg": 0,
    },
    "length": {
        "mm": 0,
        "cm": 1,
        "dm": 2,
        "m": 3,
        "km": 4
    }
}
