"""Provides methods for exporting data generated from YAML descriptor documents.
"""

import hashlib
import json
import base64
from os import sep
import zlib
from .yaml_parser import get_device_info, get_properties, get_ids, parse
from .blob_generator import generate_metadata, generate_data
from .lib_generator import generate_lib_header, generate_lib_code, copy_utils, H_FILENAME_TEMPLATE, C_FILENAME_TEMPLATE
from .util import error, generate_device_id, warn

class CRC32Hash:
    @property
    def digest_size(self) -> int:
        return 4

    @property
    def block_size(self) -> int:
        return 4

    @property
    def name(self) -> str:
        return "md5"

    def __init__(self, data=None) -> None:
        self._result = 0
        if data is not None:
            self.update(data)

    def copy(self):
        hasher = CRC32Hash()
        hasher._result = self._result
        return hasher

    def digest(self) -> bytes:
        res = self._result.to_bytes(length=4, byteorder="big", signed=False)
        self._result = 0
        return res

    def hexdigest(self) -> str:
        dig = self.digest()
        return dig.hex()

    def update(self, data) -> None:
        self._result = zlib.crc32(data, self._result)

def encode_base64(data) -> str:
    """Encode a series of bytes into a Base64 ASCII string
    """
    return base64.urlsafe_b64encode(data).decode("ascii")

def _check_size(length, max_size):
    if max_size > -1:
        total_length = length + 9 + 18 # length plus memctr, lock and end TLVs and record header x2
        if total_length > max_size:
            warn(None, f"Combined size of largest images is larger than {max_size} bytes. Ensure NFC-Tag has enough memory for all data.")

HASH_MD5 = hashlib.md5()
HASH_SHA1 = hashlib.sha1()
HASH_SHA256 = hashlib.sha256()
HASH_CRC32 = CRC32Hash()

def export_rom_blob(
        config_file,
        output_path,
        translation_sets,
        compress_metadata,
        hash_func,
        tag_size=-1) -> None:
    """Export a blob containing data and metadata.
    If translation_sets is None, only one set will be included with all translations contained in the main configuration file.
    Otherwise translations in the main configuration file will be ignored.

    Args:
        config_file (str): the file to read the YAML configuration definition from
        output_path (str): folder to write output file to
        translation_sets (list): a list of lists, that contain the languages to be included in each metadata set.
        compress_metadata (bool): compress metadata with deflate
        hash_func: The hash function to use (one of HASH_MD5, HASH_SHA1, HASH_SHA256, HASH_CRC32)
        tag_size (int): memory size of used tag
    """

    doc = parse(config_file)
    props = get_properties(doc)
    ids = get_ids(doc)
    dev_info = get_device_info(doc)
    data = generate_data(props)
    metadata_sets = []
    if translation_sets is None:
        translation_data = None
        if "translation_data" in doc:
            translation_data = doc["translation_data"]
        metadata = generate_metadata(dev_info, ids, props, translation_data, compress_metadata)
        metadata_sets.append(metadata)
    else:
        if "translation_data" in doc:
            translations = {translation["language"]: translation for translation in doc["translation_data"]}
            for trans_set in translation_sets:
                used_translations = [v for k, v in translations.items() if k in trans_set]
                metadata = generate_metadata(dev_info, ids, props, used_translations, compress_metadata)
                metadata_sets.append(metadata)
        else:
            error(doc, "Translation keys to include were provided, but no translation data in descriptor.")
    _check_size(max(map(len, metadata_sets)) + len(data), tag_size)
    output = []
    output.append(1 + len(metadata_sets))
    output.append(hash_func.digest_size)
    start_addr = 2
    output.extend(_create_blob_descriptor(data, hash_func, start_addr))
    for meta in metadata_sets:
        output.extend(_create_blob_descriptor(meta, hash_func, start_addr))
        start_addr += 8 + hash_func.digest_size
    output.extend(data)
    for meta in metadata_sets:
        output.extend(meta)
    if not output_path.endswith(sep):
        output_path = output_path + sep
    blob_file = output_path + "rom_blob.bin"
    with open(blob_file, "wb") as file:
        file.write(bytes(output))

def _create_blob_descriptor(data, hash_func, start_addr) -> bytes:
    hash_func.update(data)
    digest = hash_func.digest()
    arr = []
    arr.extend(digest)
    start = start_addr.to_bytes(length=4, byteorder="big", signed=False)
    arr.extend(start)
    length = len(data).to_bytes(length=4, byteorder="big", signed=False)
    arr.extend(length)
    return arr

def export_all(
        config_file,
        output_path,
        lib_name,
        compress_metadata,
        generate_enums=False,
        generate_getters=False,
        include_utils=True,
        tag_size=-1,
        tab_spaces=None) -> None:
    """Export all files at once -  Binary data and metadata, C library files, and JSON.

    Args:
        config_file (str): the file to read the YAML configuration definition from
        output_path (str): path to output files to
        lib_name (str): name to use for C library
        compress_metadata (bool): compress metadata with deflate
        generate_enums (bool): generate C enums for selection properties
        generate_getters (bool): generate safe getter functions for properties
        include_utils (bool): include utility code in generated files or use seperate files
        tag_size (int): memory size of used tag
        tab_spaces (int): number of spaces to use for tabs in code
    """

    doc = parse(config_file)
    translations = None
    if "translation_data" in doc:
        translations = doc["translation_data"]
    props = get_properties(doc)
    ids = get_ids(doc)
    dev_info = get_device_info(doc)
    metadata = generate_metadata(dev_info, ids, props, translations, compress_metadata)
    data = generate_data(props)
    data_len = sum(map(lambda p: p.get_data_size(), props)) + 8
    _check_size(len(metadata) + len(data), tag_size)
    lib_h_content = generate_lib_header(
        props,
        lib_name,
        generate_enums=generate_enums,
        generate_getters=generate_getters,
        include_utils=include_utils,
        tab_spaces=tab_spaces)
    lib_c_content = generate_lib_code(
        props,
        lib_name,
        generate_getters=generate_getters,
        include_utils=include_utils,
        tab_spaces=tab_spaces)
    json_content = {
        "metadata": {
            "compressed": compress_metadata,
            "device_id": encode_base64(generate_device_id(doc)),
            "payload": encode_base64(metadata)
        },
        "data": {
            "size": data_len,
            "payload": encode_base64(data)
        }
    }
    if not output_path.endswith(sep):
        output_path = output_path + sep
    meta_file = output_path + f"{lib_name}_meta.bin"
    data_file = output_path + f"{lib_name}_data.bin"
    h_file = output_path + H_FILENAME_TEMPLATE.format(lib_name=lib_name)
    c_file = output_path + C_FILENAME_TEMPLATE.format(lib_name=lib_name)
    json_file = output_path + f"{lib_name}_export.json"
    with open(meta_file, "wb") as file:
        file.write(metadata)
    with open(data_file, "wb") as file:
        file.write(data)
    with open(h_file, "w") as file:
        file.write(lib_h_content)
    with open(c_file, "w") as file:
        file.write(lib_c_content)
    with open(json_file, "w") as file:
        json.dump(json_content, file)
    if not include_utils:
        copy_utils(output_path)

def export_lib(
        config_file,
        output_path,
        lib_name,
        generate_enums=False,
        generate_getters=False,
        include_utils=True,
        tab_spaces=None) -> None:
    """Export C library files.

    Args:
        config_file (str): the file to read the YAML configuration definition from
        output_path (str): path to output files to
        lib_name (str): name to use for C library
        generate_enums (bool): generate C enums for selection properties
        generate_getters (bool): generate safe getter functions for properties
        include_utils (bool): include utility code in generated files or use seperate files
        tab_spaces (int): number of spaces to use for tabs in code
    """

    doc = parse(config_file)
    props = get_properties(doc)
    lib_h_content = generate_lib_header(
        props,
        lib_name,
        generate_enums=generate_enums,
        generate_getters=generate_getters,
        include_utils=include_utils,
        tab_spaces=tab_spaces)
    lib_c_content = generate_lib_code(
        props,
        lib_name,
        generate_getters=generate_getters,
        include_utils=include_utils,
        tab_spaces=tab_spaces)
    if not output_path.endswith(sep):
        output_path = output_path + sep
    h_file = output_path + H_FILENAME_TEMPLATE.format(lib_name=lib_name)
    c_file = output_path + C_FILENAME_TEMPLATE.format(lib_name=lib_name)
    with open(h_file, "w") as file:
        file.write(lib_h_content)
    with open(c_file, "w") as file:
        file.write(lib_c_content)
    if not include_utils:
        copy_utils(output_path)
