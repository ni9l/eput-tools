"""Utility functions.
"""
import sys
from strictyaml import YAML

def serialize_ascii(text: str) -> bytes:
    """Serialize ASCII string to byte array.
    Adds trailing 0 to string.

    Args:
        text (str): String to serialize

    Returns:
        bytes: Serialized string
    """

    string = '\0'
    if text is not None:
        string = text + string
    return string.encode("ascii", "strict")

def serialize_utf8(text: str) -> bytes:
    """Serialize UTF8 string to byte array.
    Adds trailing 0 to string.

    Args:
        text (str): String to serialize

    Returns:
        bytes: Serialized string
    """

    string = '\0'
    if text is not None:
        string = text + string
    return (string).encode("utf8", "strict")

def generate_device_id(config) -> bytes:
    """Generate a packed binary representation of all device IDs.

    Args:
        config (YAML): YAML object containing the configuration definition

    Returns:
        bytes: The IDs in a binary format
    """

    data = []
    manufacturer_id = config["manufacturer_id"].data
    device_id = config["device_id"].data
    firmware_version = config["firmware_version"].data
    protocol_version = config["protocol_version"].data
    data.extend(manufacturer_id.to_bytes(length=3, byteorder="big", signed=False))
    data.extend(device_id.to_bytes(length=3, byteorder="big", signed=False))
    data.extend(firmware_version.to_bytes(length=1, byteorder="big", signed=False))
    data.extend(protocol_version.to_bytes(length=1, byteorder="big", signed=False))
    return bytes(data)

def error(yaml_prop: YAML, message: str) -> None:
    print("Error in")
    print("-" * 20)
    if yaml_prop is not None:
        print(yaml_prop.as_yaml())
    print(message)
    print("-" * 20)
    print()
    sys.exit()

def warn(yaml_prop: YAML, message: str) -> None:
    print("Warning:")
    print("-" * 20)
    if yaml_prop is not None:
        print(yaml_prop.as_yaml())
    print(message)
    print("-" * 20)
    print()
