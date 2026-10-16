#!/usr/bin/env python3
# -*- encoding=utf8 -*-

########################################################################
# Created time: 2024-08-27 18:03:44
# Author: Jason Young (杨郑鑫).
# E-Mail: AI.Jason.Young@outlook.com
# Last Modified by: Jason Young (杨郑鑫)
# Last Modified time: 2026-09-28 23:04:53
# Copyright (c) 2024 Yangs.AI
# 
# This source code is licensed under the Apache License 2.0 found in the
# LICENSE file in the root directory of this source tree.
########################################################################


"""Sidecar metadata and integrity validation for ordinary files."""

import json
import pathlib
import stat

from typing import Callable, TypedDict, cast

from younger.commons.hash import hash_file
from younger.commons.io import load_json, save_json


class FileIntegrityMetadata(TypedDict):
    size: int
    hash: str


class FileMetadata(TypedDict):
    conf: dict
    info: dict
    file: FileIntegrityMetadata


def _metadata_path_(filepath: pathlib.Path) -> pathlib.Path:
    return filepath.with_name(f'{filepath.name}.metadata.json')


def load_file_metadata(filepath: pathlib.Path) -> FileMetadata | None:
    """Load metadata with valid conf and file fields, or None if invalid.

    This validates metadata fields only, not the data file. Other filesystem
    errors propagate.
    """
    try:
        metadata = load_json(_metadata_path_(filepath))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return None

    if not isinstance(metadata, dict):
        return None
    if not isinstance(metadata.get('conf'), dict):
        return None

    file_metadata = metadata.get('file')
    if not isinstance(file_metadata, dict):
        return None

    file_size = file_metadata.get('size')
    if not isinstance(file_size, int) or isinstance(file_size, bool) or file_size < 0:
        return None
    file_hash = file_metadata.get('hash')
    if not isinstance(file_hash, str):
        return None
    return cast(FileMetadata, metadata)


def save_file_metadata(metadata: FileMetadata, filepath: pathlib.Path) -> None:
    """Atomically save metadata beside a file without modifying the data.

    Use JSON-native values and string keys for round-trip equality.
    """
    save_json(metadata, _metadata_path_(filepath), indent=2, atomic=True)


def build_file_metadata(filepath: pathlib.Path, conf: dict, info: dict) -> FileMetadata:
    """Build metadata describing an existing file, without saving it.

    conf contains the configuration to match; info is informational.
    Keep the file unchanged while building and saving metadata, using
    directory_lock when coordinating shared files.
    """
    file_stat = filepath.stat()

    if not stat.S_ISREG(file_stat.st_mode):
        raise ValueError(f'File path is not a regular file: {filepath}')
    file_metadata: FileIntegrityMetadata = {'size': file_stat.st_size, 'hash': hash_file(filepath)}

    return {'conf': conf, 'info': info, 'file': file_metadata}


def is_file_valid(filepath: pathlib.Path, expected_conf: dict, validator: Callable[[pathlib.Path], bool] | None = None) -> bool:
    """Check all inputs, file existence/size, hash and optional content.

    Compare conf exactly, including nested fields; ignore info. Hash checks
    require a stored SHA-256 digest.
    The validator runs last and returns False for invalid content; its exceptions
    propagate. Missing files during stat/hash return False; other IO errors
    propagate. Coordinate validation and subsequent use with file writers.
    """
    metadata = load_file_metadata(filepath)
    if metadata is None or metadata['conf'] != expected_conf:
        return False
    file_metadata = metadata['file']
    try:
        file_stat = filepath.stat()
        if not stat.S_ISREG(file_stat.st_mode):
            return False
        if file_stat.st_size != file_metadata['size']:
            return False
        if hash_file(filepath) != file_metadata['hash']:
            return False
    except FileNotFoundError:
        return False
    return validator(filepath) if validator is not None else True


