"""Provides functions for generating C library code from YAML descriptors.
"""

try:
    from importlib.resources import files
except ImportError:
    from importlib_resources import files
from os import sep
from . import properties

LIB_H_TEMPLATE = """#ifndef {namespace}
#define {namespace}

#include <stddef.h>{utils_include}
typedef struct {{
{data_struct_content}{tab}time_point data_last_written_timestamp;
}} {data_struct_name};

{enums}
#define DATA_PAYLOAD_LENGTH {data_len}

/**
 * @brief Create the payload of a data record from a data struct.
 *
 * Assumes `buf` is at least `DATA_PAYLOAD_LENGTH` long.
 * 
 * @param buf Buffer to write data to
 * @param config Pointer to the configuration struct
 *
 * @return status code
 */
int generate_payload(uint8_t *buf, {data_struct_name} *config);

/**
 * @brief Parse the payload of a data record into a struct according to the configuration definition.
 * 
 * @param buf Buffer containing the payload from NDEF record
 * @param buf_len Size of payload
 * @param config pointer to an instance of the configuration struct
 *
 * @return status code
 */
int parse_payload(uint8_t *buf, size_t buf_len, {data_struct_name} *config);

/**
 * @brief Parse the contents of NFC memory into a struct according to the configuration definition.
 * 
 * @param buf Buffer containing the data from NFC memory
 * @param buf_len Size of `buf`
 * @param config pointer to an instance of the configuration struct
 *
 * @return status code
 */
int parse_nfc(uint8_t *buf, size_t buf_len, {data_struct_name} *config);

/**
 * @brief Parse an NDEF message into a struct according to the configuration definition.
 * 
 * @param buf Buffer containing the NDEF message
 * @param buf_len Size of buffer
 * @param config pointer to an instance of the configuration struct
 *
 * @return status code
 */
int parse_ndef(uint8_t *buf, size_t buf_len, {data_struct_name} *config);

{getters}

#endif

"""

LIB_C_TEMPLATE = """#include <stdint.h>
#include "{h_filename}"
{utils_include}
int generate_payload(uint8_t *buf, {data_struct_name} *config) {{
{data_generation_snippet}{tab}return SUCCESS;
}}

int parse_payload(uint8_t *buf, size_t buf_len, {data_struct_name} *config) {{
{tab}if (buf_len != {data_length}) {{
{tab}{tab}return ERR_DATA_BUF_WRONG_LENGTH;
{tab}}}
{data_parsing_snippet}{tab}return SUCCESS;
}}

int parse_nfc(uint8_t *buf, size_t buf_len, {data_struct_name} *config) {{
{tab}size_t ndef_offset = 0;
{tab}uint16_t ndef_length = get_ndef_tlv_offset(buf, buf_len, &ndef_offset);
{tab}if (ndef_length == 0 || (ndef_offset + ndef_length) > buf_len) {{
{tab}{tab}return ERR_NO_NDEF_TLV;
{tab}}} else {{
{tab}{tab}ndef_record meta = {{0}};
{tab}{tab}ndef_record data = {{0}};
{tab}{tab}int parse_ret = get_records(
{tab}{tab}{tab}buf + ndef_offset,
{tab}{tab}{tab}ndef_length,
{tab}{tab}{tab}&meta,
{tab}{tab}{tab}&data);
{tab}{tab}if (parse_ret == SUCCESS) {{
{tab}{tab}{tab}return parse_payload(
{tab}{tab}{tab}{tab}data.payload,
{tab}{tab}{tab}{tab}data.payload_length,
{tab}{tab}{tab}{tab}config);
{tab}{tab}}} else {{
{tab}{tab}{tab}return parse_ret;
{tab}{tab}}}
{tab}}}
}}

int parse_ndef(uint8_t *buf, size_t buf_len, {data_struct_name} *config) {{
{tab}ndef_record meta = {{0}};
{tab}ndef_record data = {{0}};
{tab}int record_result = get_records(buf, buf_len, &meta, &data);
{tab}if (record_result == SUCCESS) {{
{tab}{tab}return parse_payload(
{tab}{tab}{tab}data.payload,
{tab}{tab}{tab}data.payload_length,
{tab}{tab}{tab}config);
{tab}}} else {{
{tab}{tab}return record_result;
{tab}}}
}}

{getters}
"""

UTILS_H_FILENAME = "eput_utils.h"
UTILS_C_FILENAME = "eput_utils.c"
H_FILENAME_TEMPLATE = "eput_{lib_name}.h"
C_FILENAME_TEMPLATE = "eput_{lib_name}.c"
NONE_FILTER = lambda lis: filter(lambda x: x is not None, lis)

def generate_lib_header(
        props,
        lib_name,
        generate_enums=False,
        generate_getters=False,
        include_utils=True,
        tab_spaces=None) -> str:
    """Generates library *.h file contents.

    Args:
        props (list): configuration properties
        lib_name (str): Name of the library
        generate_enums (bool): generate enums for property options
        generate_getters (bool): generate safe getters for properties
        include_utils (bool): integrate utility code into file or use seperate file
        tab_spaces (int): Amount of spaces to use in generated code for tabs

    Returns:
        str: Content of the generated *.h file
    """

    if tab_spaces is not None:
        properties.TAB_SPACES = tab_spaces
    else:
        tab_spaces = properties.TAB_SPACES
    namespace = lib_name
    data_struct_name = f"{lib_name}_config"
    if include_utils:
        utils_h = _get_utils_h()
    else:
        utils_h = f"\n#include \"{UTILS_H_FILENAME}\"\n"
    struct_content = "".join(NONE_FILTER([prop.generate_struct_member() for prop in props]))
    enum_snippet = ""
    if generate_enums:
        enums = [prop.generate_enums() for prop in props]
        enum_snippet = "\n".join(NONE_FILTER(enums))
    getter_snippet = ""
    if generate_getters:
        getters = [_build_getter_signature(prop) for prop in props]
        getter_snippet = "\n".join(NONE_FILTER(getters))
    lib_h_content = LIB_H_TEMPLATE.format(
        tab=(" " * tab_spaces),
        namespace=namespace,
        utils_include=utils_h,
        data_len=sum(map(lambda p: p.get_data_size(), props)) + 8, # Add 8 for last written timestamp
        data_struct_content=struct_content,
        data_struct_name=data_struct_name,
        enums=enum_snippet,
        getters=getter_snippet)
    return lib_h_content

def generate_lib_code(
        props,
        lib_name,
        generate_getters=False,
        include_utils=True,
        tab_spaces=None) -> str:
    """Generates library *.c file contents.

    Args:
        props (list): configuration properties
        lib_name (str): Name of the library
        generate_getters (bool): generate safe getters for properties
        include_utils (bool): integrate utility code into file or use seperate file
        tab_spaces (int): Amount of spaces to use in generated code for tabs

    Returns:
        str: Content of the generated *.c file
    """

    if tab_spaces is not None:
        properties.TAB_SPACES = tab_spaces
    else:
        tab_spaces = properties.TAB_SPACES
    h_filename = H_FILENAME_TEMPLATE.format(lib_name=lib_name)
    data_struct_name = f"{lib_name}_config"
    data_index = 0
    data_read_snippet = []
    data_write_snippet = []
    for prop in props:
        data_read_snippet.append(prop.generate_read_code(data_index, "config->"))
        data_write_snippet.append(prop.generate_write_code(data_index, "config->"))
        data_index += prop.get_data_size()
    data_read_snippet.append((" " * tab_spaces) + f"config->data_last_written_timestamp = bytes_to_time_point(buf + {data_index});\n")
    data_write_snippet.append((" " * tab_spaces) + f"time_point_to_bytes(config->data_last_written_timestamp, buf + {data_index});\n")
    data_read_snippet = "".join(NONE_FILTER(data_read_snippet))
    data_write_snippet = "".join(NONE_FILTER(data_write_snippet))
    utils_c = ""
    if include_utils:
        utils_c = _get_utils_c()
    getter_snippet = ""
    if generate_getters:
        getters = [_build_getter_function(prop) for prop in props]
        getter_snippet = "\n".join(NONE_FILTER(getters))
    data_index += 8 # Add 8 for last written timestamp
    lib_c_content = LIB_C_TEMPLATE.format(
        tab=(" " * tab_spaces),
        h_filename=h_filename,
        utils_include=utils_c,
        data_struct_name=data_struct_name,
        data_length=str(data_index),
        data_parsing_snippet=data_read_snippet,
        data_generation_snippet=data_write_snippet,
        getters=getter_snippet)
    return lib_c_content

def copy_utils(destination) -> None:
    """Copy C utility library files to `destination`

    Args:
        destination (str): destination folder
    """
    res = files("eputgen")
    contents_h = (res / "eputgen" / UTILS_H_FILENAME).read_text()
    contents_c = (res / "eputgen" / UTILS_C_FILENAME).read_text()
    if not destination.endswith(sep):
        destination = destination + sep
    with open(destination + UTILS_H_FILENAME, "w") as file_h:
        file_h.write(contents_h)
    with open(destination + UTILS_C_FILENAME, "w") as file_c:
        file_c.write(contents_c)

def _build_getter_function(prop):
    getter = prop.generate_safe_getter_code()
    if getter is None:
        return None
    return getter[1]

def _build_getter_signature(prop):
    getter = prop.generate_safe_getter_code()
    if getter is None:
        return None
    return getter[0]

def _get_utils_h() -> str:
    res = files("eputgen")
    with open(res / "c" / UTILS_H_FILENAME, "r") as file:
        lines = file.readlines()
        lines = lines[2:-2]
        return "".join(lines)

def _get_utils_c() -> str:
    res = files("eputgen")
    with open(res / "c" / UTILS_C_FILENAME, "r") as file:
        lines = file.readlines()
        lines = lines[1:]
        return "".join(lines)
