#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) Jason Young (杨郑鑫).
#
# E-Mail: <AI.Jason.Young@outlook.com>
# 2024-04-05 09:41
#
# This source code is licensed under the Apache-2.0 license found in the
# LICENSE file in the root directory of this source tree.


import pandas
import pathlib

from typing import Literal
from huggingface_hub import list_metrics

from younger.commons.io import save_json
from younger.commons.logging import logger

from younger.datasets.constructors.huggingface.utils import get_huggingface_model_ids


def save_huggingface_metrics(save_dirpath: pathlib.Path):
    metrics = list_metrics()
    ids = [metric.id for metric in metrics]
    descriptions = [metric.description for metric in metrics]
    data_frame = pandas.DataFrame({'Metric Names': ids, 'Descriptions': descriptions})
    save_filepath = save_dirpath.joinpath('huggingface_metrics.xlsx')
    data_frame.to_excel(save_filepath, index=False)


def save_huggingface_models(save_dirpath: pathlib.Path, cache_dirpath: pathlib.Path):
    pass


def save_huggingface_model_ids(save_dirpath: pathlib.Path, library: str | None = None):
    model_ids = get_huggingface_model_ids(library)
    suffix = f'_{library}.json' if library else '.json'
    save_filepath = save_dirpath.joinpath(f'model_ids{suffix}')
    save_json(model_ids, save_filepath)
    logger.info(f'Total {len(model_ids)} Model IDs{f" (Library - {library})" if library else ""}. Results Saved In: \'{save_filepath}\'.')


def main(mode: Literal['Models', 'Model_Infos', 'Model_IDs', 'Metrics'], save_dirpath: pathlib.Path, cache_dirpath: pathlib.Path, **kwargs):
    assert mode in {'Models', 'Model_Infos', 'Model_IDs', 'Metrics'}

    if mode == 'Models':
        save_huggingface_models(save_dirpath, cache_dirpath)
        return
    
    if mode == 'Model_IDs':
        save_huggingface_model_ids(save_dirpath, library=kwargs['library'])
        return
    
    if mode == 'Metrics':
        save_huggingface_metrics(save_dirpath)
        return