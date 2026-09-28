#!/usr/bin/env python3
# -*- encoding=utf8 -*-

########################################################################
# Created time: 2025-04-13 14:06:21
# Author: Jason Young (杨郑鑫).
# E-Mail: AI.Jason.Young@outlook.com
# Last Modified by: Jason Young (杨郑鑫)
# Last Modified time: 2026-09-28 21:26:47
# Copyright (c) 2025 Yangs.AI
# 
# This source code is licensed under the Apache License 2.0 found in the
# LICENSE file in the root directory of this source tree.
########################################################################


import time
import random
from typing import Iterable, Callable, TypeVar

T = TypeVar("T")


def retry(operation: Callable[[], T], should_retry: Callable[[Exception], bool], max_attempts: int = 4, max_delay: float = 30) -> T:
    """Execute an operation with capped exponential backoff.

    Args:
        operation: Operation to execute.
        should_retry: Predicate deciding whether an exception is retryable.
        max_attempts: Maximum number of execution attempts, including the first.
        max_delay: Maximum delay between attempts, in seconds.

    Returns:
        The result returned by ``operation``.

    Raises:
        ValueError: If ``max_attempts`` or ``max_delay`` is invalid.
        Exception: The last exception raised by ``operation``.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if max_delay < 0:
        raise ValueError("max_delay must be at least 0")

    for attempt in range(max_attempts):
        try:
            return operation()
        except Exception as exception:
            if not should_retry(exception) or attempt == max_attempts - 1:
                raise

            delay = min(max_delay, 2**attempt)
            time.sleep(delay)

    raise RuntimeError("unreachable")



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
