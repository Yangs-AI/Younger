#!/usr/bin/env python3
# -*- encoding=utf8 -*-

########################################################################
# Created time: 2025-01-06 19:27:28
# Author: Jason Young (杨郑鑫).
# E-Mail: AI.Jason.Young@outlook.com
# Last Modified by: Jason Young (杨郑鑫)
# Last Modified time: 2026-02-04 10:04:12
# Copyright (c) 2026 Yangs.AI
# 
# This source code is licensed under the Apache License 2.0 found in the
# LICENSE file in the root directory of this source tree.
########################################################################


import pathlib

from younger.commons.cache import CachedChunks


def test_cached_chunks(tmp_path: pathlib.Path):
    itr = CachedChunks(tmp_path / "cached_chunks", range(100000), 1000)

    chunks = list(itr)
    assert len(itr) == 100000
    assert len(chunks) == 100
    assert all(len(c) == 1000 for c in chunks[:])
    assert sum(len(c) for c in chunks) == 100000
