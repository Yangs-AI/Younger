#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) Jason Young (杨郑鑫).
#
# E-Mail: <AI.Jason.Young@outlook.com>
# 2023-10-02 13:57
#
# This source code is licensed under the Apache-2.0 license found in the
# LICENSE file in the root directory of this source tree.


import onnx
import pathlib
import argparse
import semantic_version

from onnx import hub
from typing import Generator, Tuple

from youngbench.dataset.modules import Dataset
from youngbench.dataset.modules import Instance

from youngbench.dataset.utils.io import load_model
from youngbench.dataset.utils.cache import set_cache_root, get_cache_root
from youngbench.logging import set_logger, logger


def get_onnx_official_onnx_models() -> Generator[Tuple[str, onnx.ModelProto], None, None]:
    all_models = sorted(hub.list_models(), key=lambda x: x.metadata['model_bytes'])
    for model_info in all_models:
        # onnx_model = hub.load(model=model_info.model, opset=model_info.opset)
        total_try = 10
        for i in range(total_try):
            try:
                onnx_model = hub.load(model=model_info.model, opset=model_info.opset)
                break
            except:
                print(f'Try No. {i+1}/{total_try} to re-load.')
        yield (model_info.model, onnx_model)


def get_pytorch_official_onnx_models() -> Generator[Tuple[str, onnx.ModelProto], None, None]:
    yield


def get_tensorflow_official_onnx_models() -> Generator[Tuple[str, onnx.ModelProto], None, None]:
    yield


def get_official_onnx_models(onnx: bool = False, pytorch: bool = False, tensorflow: bool = False) -> Generator[Tuple[str, onnx.ModelProto], None, None]:
    if onnx:
        yield from get_onnx_official_onnx_models()
    if pytorch:
        yield from get_pytorch_official_onnx_models()
    if tensorflow:
        yield from get_tensorflow_official_onnx_models()


def get_provided_onnx_models(onnx_path: pathlib.Path) -> Generator[Tuple[str, onnx.ModelProto], None, None]:
    for filepath in onnx_path.iterdir():
        onnx_model = load_model(filepath)
        yield (filepath.stem, onnx_model)


def get_opset_version(onnx_model: onnx.ModelProto):
    for opset_info in onnx_model.opset_import:
        if opset_info.domain == "":
            opset_version = opset_info.version
            break
    return opset_version


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create/Update The Young Neural Network Architecture Dataset (YoungBench - Dataset).")

    # Dataset Release Version.
    parser.add_argument('--version', type=str, required=True)

    # ONNX Models' Dir
    parser.add_argument('--onnx-hub-path', type=str, default='')

    # Dataset Save/Load Path.
    parser.add_argument('--load-path', type=str, default='')
    parser.add_argument('--save-path', type=str, default='')
    parser.add_argument('--cache-dir', type=str, default='')

    parser.add_argument('--logging-path', type=str, default='')

    # Mode - Create / Update
    parser.add_argument('--mode', type=str, default='Update', choices=['Update', 'Create'])

    args = parser.parse_args()

    assert semantic_version.validate(args.version), f'The version provided must follow the SemVer 2.0.0 Specification.'
    version = semantic_version.Version(args.version)

    set_logger(path=args.logging_path)

    if args.cache_dir == '':
        pass
    else:
        cache_dir = pathlib.Path(args.cache_dir)
        set_cache_root(cache_dir)

    cache_dir = get_cache_root()
    logger.info(f'Cache directory is set to be: {cache_dir.absolute()}')
    cache_dir.mkdir(parents=True, exist_ok=True)

    dataset = Dataset()

    if args.mode == 'Create':
        if len(args.onnx_hub_path) == 0:
            logger.info(f'Using default ONNX Hub cache location.')
        else:
            onnx_hub_path = pathlib.Path(args.onnx_hub_path)
            assert onnx_hub_path.is_dir(), f'Directory does not exists at the specified \"ONNX Path\": {onnx_hub_path}.'
            hub.set_dir(str(onnx_hub_path.absolute()))
            logger.info(f'ONNX Hub cache location is set to: {hub.get_dir()}')

        save_path = pathlib.Path(args.save_path)
        assert not save_path.is_dir(), f'Directory exists at the specified \"Save Path\": {save_path}.'

        onnx_models = get_official_onnx_models(onnx=True, pytorch=False, tensorflow=False)

    if args.mode == 'Update':
        onnx_hub_path = pathlib.Path(args.onnx_hub_path)
        assert onnx_hub_path.is_dir(), f'Directory does not exists at the specified \"ONNX Path\": {onnx_hub_path}.'

        if args.load_path == '':
            load_path = pathlib.Path('.')
        else:
            load_path = pathlib.Path(args.load_path)
        assert load_path.is_dir(), f'Directory does not exists at the specified \"Load Path\": {load_path}.'

        if args.save_path == '':
            save_path = load_path
        else:
            save_path = pathlib.Path(args.save_path)
        assert not save_path.is_dir(), f'Directory exists at the specified \"Save Path\": {save_path}.'

        dataset.load(load_path)

        onnx_models = get_provided_onnx_models(onnx_hub_path)

    logger.info(f'-> Dataset Initialized.')

    logger.info(f'-> Dataset Creating ...')
    for index, (onnx_model_name, onnx_model) in enumerate(onnx_models):
        opset = get_opset_version(onnx_model)
        logger.info(f' # {index+1}: Now processing the model: {onnx_model_name} (ONNX opset={opset})')
        dataset.insert(Instance(model=onnx_model, labels=dict(name=onnx_model_name)))
    logger.info(f'-> Created.')

    logger.info(f'-> Dataset Releasing ...')
    dataset.release(version)
    logger.info(f'-> Released.')

    logger.info(f'-> Dataset Saving ...')
    dataset.save(save_path)
    logger.info(f'-> Saved: {save_path}.')