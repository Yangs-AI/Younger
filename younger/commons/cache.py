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


import json
import stat
import tqdm
import pathlib

from typing import NotRequired, Callable, Iterator, TypedDict, cast

from younger.commons.io import load_pickle, save_pickle, load_json, save_json
from younger.commons.hash import hash_file
from younger.commons.constants import YoungerHandle


CACHE_ROOT: pathlib.Path = pathlib.Path.home().joinpath(f'.cache/{YoungerHandle.MainName}')


class CacheFileMetadata(TypedDict):
    size: int
    hash: str


class CacheMetadata(TypedDict):
    conf: dict
    info: dict
    file: CacheFileMetadata


def _metadata_path_(filepath: pathlib.Path) -> pathlib.Path:
    return filepath.with_name(f'{filepath.name}.metadata.json')


def load_cache_metadata(filepath: pathlib.Path) -> CacheMetadata | None:
    """Load structurally valid metadata, or None if missing or malformed.

    This validates metadata fields only, not the cache file. Other filesystem
    errors propagate. Expected cache misses do not emit error logs.
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
    return cast(CacheMetadata, metadata)


def save_cache_metadata(metadata: CacheMetadata, filepath: pathlib.Path) -> None:
    """Atomically save metadata beside a cache file without modifying the data.

    Use JSON-native values and string keys for round-trip equality.
    """
    save_json(metadata, _metadata_path_(filepath), indent=2, atomic=True)


def build_cache_metadata(filepath: pathlib.Path, conf: dict, info: dict) -> CacheMetadata:
    """Build metadata describing an existing cache file, without saving it.

    conf contains every field required for reuse; info is informational.
    Keep the file unchanged while building and saving metadata, using
    directory_lock when coordinating shared caches.
    """
    file_stat = filepath.stat()

    if not stat.S_ISREG(file_stat.st_mode):
        raise ValueError(f'Cache path is not a regular file: {filepath}')
    file_metadata: CacheFileMetadata = {'size': file_stat.st_size, 'hash': hash_file(filepath)}

    return {'conf': conf, 'info': info, 'file': file_metadata}


def is_cache_valid(filepath: pathlib.Path, expected_conf: dict, validator: Callable[[pathlib.Path], bool] | None = None) -> bool:
    """Check all inputs, file existence/size, hash and optional content.

    Compare inputs exactly, including nested fields; ignore extra. Hash checks
    require a stored SHA-256 digest. Set verify_hash=False for size-only checks.
    The validator runs last and returns False for invalid content; its exceptions
    propagate. Missing files during stat/hash return False; other IO errors
    propagate. Coordinate validation and subsequent use with cache writers.
    """
    metadata = load_cache_metadata(filepath)
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


def set_cache_root(dirpath: pathlib.Path) -> None:
    assert isinstance(dirpath, pathlib.Path)
    global CACHE_ROOT
    CACHE_ROOT = dirpath
    return


def get_cache_root() -> pathlib.Path:
    return CACHE_ROOT


class CachedChunks(object):
    _status_cache_filename_ = 'status'
    _config_cache_filename_ = 'config'
    _chunks_cache_filename_ = 'chunks'
    def __init__(self, cache_dirpath: pathlib.Path, iterator: Iterator, size_of_chunk: int):
        """
        Cache an iterator to disk in fixed-size chunks and resume later.

        Behavior notes:
        - __len__() returns the total number of items in the original iterator
            (not the number of chunks).
        - Iteration yields chunks (lists) of items, each with size <= size_of_chunk.
            This reduces IO overhead and supports large datasets.

        Typical use cases:
        - Datasets too large to fit in memory.
        - Long-running data collection with resumable progress.

        :param cache_dirpath: Directory path where cache files will be stored.
        :type cache_dirpath: pathlib.Path
        :param iterator: The iterator whose chunks are to be cached.
        :type iterator: Iterator
        :param size_of_chunk: The number of items in each chunk.
        :type size_of_chunk: int
        """
        self._cache_dirpath = cache_dirpath
        self._status_filepath = self._cache_dirpath.joinpath(self.__class__._status_cache_filename_)
        self._config_filepath = self._cache_dirpath.joinpath(self.__class__._config_cache_filename_)
        self._chunks_filepath = self._cache_dirpath.joinpath(self.__class__._chunks_cache_filename_)

        if self._config_filepath.is_file():
            config = load_pickle(self._config_filepath)
            self._size_of_chunk = config['size_of_chunk']
            self._length_of_itr = config['length_of_itr']
            self._num_of_chunks = config['num_of_chunks']

            self._current_index = load_pickle(self._status_filepath)
        else:
            self._size_of_chunk = size_of_chunk
            self._length_of_itr = 0
            self._num_of_chunks = 0

            self._current_index = 0

            chunk = list()
            for item in tqdm.tqdm(iterator):
                chunk.append(item)
                if len(chunk) == self._size_of_chunk:
                    save_pickle(chunk, self._chunks_filepath.with_suffix(f'.{self._num_of_chunks}'))
                    chunk.clear()
                    self._num_of_chunks += 1
                self._length_of_itr += 1

            if len(chunk) != 0:
                save_pickle(chunk, self._chunks_filepath.with_suffix(f'.{self._num_of_chunks}'))
                self._num_of_chunks += 1

            config = dict(
                size_of_chunk = self._size_of_chunk,
                length_of_itr = self._length_of_itr,
                num_of_chunks = self._num_of_chunks,
            )
            save_pickle(config, self._config_filepath)
            save_pickle(self._current_index, self._status_filepath)

    def __iter__(self):
        return self

    def __next__(self):
        if self._current_index >= self._num_of_chunks:
            raise StopIteration

        chunk = load_pickle(self._chunks_filepath.with_suffix(f'.{self._current_index}'))
        self._current_index += 1
        save_pickle(self._current_index, self._status_filepath)
        return chunk

    def __len__(self):
        return self._length_of_itr

    @property
    def current_position(self):
        return min(self._current_index * self._size_of_chunk, self._length_of_itr)

    @property
    def current_chunk_id(self):
        return self._current_index
