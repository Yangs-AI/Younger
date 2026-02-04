#!/usr/bin/env python3
# -*- encoding=utf8 -*-

########################################################################
# Created time: 2024-08-27 18:03:44
# Author: Jason Young (杨郑鑫).
# E-Mail: AI.Jason.Young@outlook.com
# Last Modified by: Jason Young (杨郑鑫)
# Last Modified time: 2026-02-04 10:00:59
# Copyright (c) 2024 Yangs.AI
# 
# This source code is licensed under the Apache License 2.0 found in the
# LICENSE file in the root directory of this source tree.
########################################################################


import tqdm
import pathlib


from typing import Iterator

from younger.commons.io import load_pickle, save_pickle
from younger.commons.constants import YoungerHandle


CACHE_ROOT: pathlib.Path = pathlib.Path.home().joinpath(f'.cache/{YoungerHandle.MainName}')


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
