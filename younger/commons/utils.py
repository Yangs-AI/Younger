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


def split_sequence(sequence: list, split_count: int) -> list[list]:
    avg, rmd = divmod(len(sequence), split_count)
    splits = list()
    start = 0
    for i in range(split_count):
        end = start + avg + (1 if i < rmd else 0)
        splits.append(sequence[start:end])
        start = end
    return splits


def no_operation(*args, **kwargs):
    pass
