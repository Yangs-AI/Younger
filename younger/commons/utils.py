#!/usr/bin/env python3
# -*- encoding=utf8 -*-

########################################################################
# Created time: 2025-04-13 14:06:21
# Author: Jason Young (杨郑鑫).
# E-Mail: AI.Jason.Young@outlook.com
# Last Modified by: Jason Young (杨郑鑫)
# Last Modified time: 2025-04-24 10:12:35
# Copyright (c) 2025 Yangs.AI
# 
# This source code is licensed under the Apache License 2.0 found in the
# LICENSE file in the root directory of this source tree.
########################################################################


def split_sequence(sequence: list, chunk_count: int) -> list[list]:
    """
    Split a sequence into multiple chunks as evenly as possible.

    :param sequence: The input sequence to be split.
    :param chunk_count: The number of chunks to split into.
    :return: A list of chunks (sublists).

    Example:
        >>> split_sequence([1, 2, 3, 4, 5], 2)
        [[1, 2, 3], [4, 5]]
        >>> split_sequence([1, 2, 3, 4, 5, 6], 3)
        [[1, 2], [3, 4], [5, 6]]
    """

    assert 0 < chunk_count and chunk_count <= len(sequence), "chunk_count must be in the range (0, len(sequence)]"

    q, r = divmod(len(sequence), chunk_count)

    chunks = list()
    start = 0
    for i in range(chunk_count):
        end = start + q + (1 if i < r else 0)
        chunks.append(sequence[start:end])
        start = end
    return chunks


def shuffle_sequence(sequence: Iterable) -> Iterable:
    indices = list(range(len(sequence)))
    random.shuffle(indices)
    shuffled_sequence = ( sequence[index] for index in indices )
    return shuffled_sequence


def no_operation(*args, **kwargs) -> None:
    return None

