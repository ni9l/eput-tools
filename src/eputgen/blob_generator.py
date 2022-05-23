"""Provides functions for generating binary blobs from YAML descriptors.
"""

import zlib
from . import util

DEVICE_TYPE_CODE = {
    "Custom": 0b00000000,
    "Light": 0b00000001,
    "Washing Machine": 0b00000010,
    "Heater": 0b00000011,
    "Custom_NoTruncate": 0b10000000
}

def generate_metadata(dev_info, ids, properties, translations, compress) -> bytes:
    """Generates the binary representation of the provided configuration's metadata.

    Args:
        dev_info: device info
        ids (list): all IDs in configuration
        properties (list): all properties in configuration
        translations (YAML): the translation data
        compress_metadata (bool): compress metadata with deflate

    Returns:
        bytes: the binary metadata
    """

    metadata = []
    metadata.extend(_serialize_device_info(dev_info))
    for prop in properties:
        metadata.extend(prop.serialize())
    metadata.append(0xFF)
    metadata.extend(_serialize_translations(ids, translations))
    metadata_bytes = bytes(metadata)
    if compress:
        old_len = len(metadata_bytes)
        metadata_bytes = compress_metadata(metadata_bytes)
        new_len = len(metadata_bytes)
        print(f"Requested compression of metadata: {old_len} -> {new_len}, {new_len // (old_len / 100)}%")
    else:
        print("Compression disabled, remember to add 'zip=0' argument to NDEF metadata type URI")
    return metadata_bytes

def generate_data(properties) -> bytes:
    data = []
    for prop in properties:
        res = prop.serialize_data()
        if res is not None:
            data.extend(res)
    for _ in range(0, 8): # add 8 bytes for last written timestamp
        data.append(0)
    return bytes(data)

def compress_metadata(metadata) -> bytes:
    return zlib.compress(metadata, zlib.Z_BEST_COMPRESSION)

def _serialize_device_info(dev_info) -> list:
    serialized = []
    serialized.append(DEVICE_TYPE_CODE[dev_info["device_type"]])
    serialized.extend(dev_info["manufacturer_id"].to_bytes(length=3, byteorder="big", signed=False))
    serialized.extend(dev_info["device_id"].to_bytes(length=3, byteorder="big", signed=False))
    serialized.extend(dev_info["firmware_version"].to_bytes(length=1, byteorder="big", signed=False))
    serialized.extend(dev_info["protocol_version"].to_bytes(length=1, byteorder="big", signed=False))
    serialized.extend(util.serialize_ascii(dev_info["device_name"]))
    return serialized

def _serialize_translations(ids, translations) -> list:
    serialized = []
    if translations is not None:
        for translation in translations:
            lang = translation["language"].data
            serialized.extend(util.serialize_ascii(lang))
            for i in ids:
                try:
                    translated_str = translation["translations"][i].data
                    serialized.extend(util.serialize_utf8(translated_str))
                except KeyError:
                    serialized.append(0x00)
    serialized.append(0x00)
    serialized.append(0x00)
    return serialized
