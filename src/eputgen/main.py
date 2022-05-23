"""Entrypoint for CLI of eputgen.
"""

import argparse
from . import export

def main():
    """Parse configuration and export binaries, JSON, and C library files.
    """

    parser = argparse.ArgumentParser(
        "eputgen",
        description="Parse device descriptor and export binary, JSON, and C library files.")
    parser.add_argument(
        "--rom",
        dest="generate_rom",
        action="store_true",
        default=False,
        help="Generate ROM image"
    )
    parser.add_argument(
        "--hash",
        dest="hash_func",
        choices=["md5", "sha1", "sha256", "crc32"],
        default="md5",
        help="Hash function to use; one of 'md5', 'sha1', 'sha256', 'crc32'"
    )
    parser.add_argument(
        "--lang",
        dest="language_sets",
        action="append",
        default=None,
        help="languages to include in one metadata block; comma seperated")
    parser.add_argument(
        "--tab-spaces",
        dest="tab_spaces",
        type=int,
        help="number of spaces to use for tabs in generated code")
    parser.add_argument(
        "--enums",
        dest="generate_enums",
        action="store_true",
        default=False,
        help="generate enums for selection options")
    parser.add_argument(
        "--safe-getter",
        dest="generate_getters",
        action="store_true",
        default=False,
        help="generate safe getter functions for properties")
    parser.add_argument(
        "--include-utils",
        dest="include_utils",
        action="store_true",
        default=False,
        help="include utility library in generated code instead of seperate file")
    parser.add_argument(
        "--no-compress",
        dest="compress_metadata",
        action="store_false",
        default=True,
        help="compress metadata with deflate algorithm"
    )
    parser.add_argument(
        "--tag-size",
        dest="tag_size",
        type=int,
        default=-1,
        help="memory size of used NFC tag - if set, a warning will be shown if generated files are too large for tag"
    )
    parser.add_argument(
        "input_path",
        help="input device descriptor file")
    parser.add_argument(
        "output_path",
        help="output folder")
    parser.add_argument(
        "lib_name",
        help="name of generated C-library")
    args = parser.parse_args()
    if args.generate_rom:
        translation_sets = None
        if args.language_sets is not None:
            translation_sets = [l.split(",") for l in args.language_sets]
        hash_func = export.HASH_MD5
        if args.hash_func.lower() == "md5":
            hash_func = export.HASH_MD5
        if args.hash_func.lower() == "sha1":
            hash_func = export.HASH_SHA1
        if args.hash_func.lower() == "sha256":
            hash_func = export.HASH_SHA256
        if args.hash_func.lower() == "crc32":
            hash_func = export.HASH_CRC32
        export.export_rom_blob(
            args.input_path,
            args.output_path,
            translation_sets,
            args.compress_metadata,
            hash_func,
            tag_size=args.tag_size
        )
    else:
        export.export_all(
            args.input_path,
            args.output_path,
            args.lib_name,
            compress_metadata=args.compress_metadata,
            generate_enums=args.generate_enums,
            generate_getters=args.generate_getters,
            include_utils=args.include_utils,
            tag_size=args.tag_size,
            tab_spaces=args.tab_spaces)
