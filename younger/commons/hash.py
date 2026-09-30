#!/usr/bin/env python3
# -*- encoding=utf8 -*-

########################################################################
# Created time: 2024-10-19 22:08:34
# Author: Jason Young (杨郑鑫).
# E-Mail: AI.Jason.Young@outlook.com
# Last Modified by: Jason Young (杨郑鑫)
# Last Modified time: 2026-09-28 15:17:01
# Copyright (c) 2024 Yangs.AI
# 
# This source code is licensed under the Apache License 2.0 found in the
# LICENSE file in the root directory of this source tree.
########################################################################


import pathlib
import hashlib
import json


def hash_json(serializable_object: object, hash_algorithm: str = "SHA256", digest_size: int | None = None) -> str:
    """Hash a JSON-serializable object using compact, sorted JSON.

    Return the full hexadecimal digest. digest_size is passed to the hash
    algorithm (when supported), not used to truncate the hexadecimal string.
    Default ASCII escaping is preserved, so hash_json(data)[:20] matches the
    former fingerprint(data) cache key.
    """

    serialized_json = json.dumps(serializable_object, sort_keys=True, separators=(',', ':'))
    return hash_string(string=serialized_json, hash_algorithm=hash_algorithm, digest_size=digest_size)


def hash_file(filepath: pathlib.Path | str, block_size: int = 8192, hash_algorithm: str = "SHA256", digest_size: int | None = None) -> str:
    filepath = pathlib.Path(filepath) if isinstance(filepath, str) else filepath
    hasher = hashlib.new(hash_algorithm) if digest_size is None else hashlib.new(hash_algorithm, digest_size=digest_size)
    with open(filepath, 'rb') as file:
        while True:
            block = file.read(block_size)
            if len(block) == 0:
                break
            hasher.update(block)

    return str(hasher.hexdigest())


def hash_bytes(byte_string: bytes, hash_algorithm: str = "SHA256", digest_size: int | None = None) -> str:
    hasher = hashlib.new(hash_algorithm) if digest_size is None else hashlib.new(hash_algorithm, digest_size=digest_size)
    hasher.update(byte_string)

    return str(hasher.hexdigest())


def hash_string(string: str, hash_algorithm: str = "SHA256", digest_size: int | None = None) -> str:
    hasher = hashlib.new(hash_algorithm) if digest_size is None else hashlib.new(hash_algorithm, digest_size=digest_size)
    hasher.update(string.encode('utf-8'))

    return str(hasher.hexdigest())


def hash_strings(strings: list[str], hash_algorithm: str = "SHA256", digest_size: int | None = None) -> str:
    hasher = hashlib.new(hash_algorithm) if digest_size is None else hashlib.new(hash_algorithm, digest_size=digest_size)
    for string in strings:
        hasher.update(string.encode('utf-8'))

    return str(hasher.hexdigest())
