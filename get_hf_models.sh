#!/bin/bash
#
# Copyright (c) Jason Young (杨郑鑫).
#
# E-Mail: <AI.Jason.Young@outlook.com>
# 2024-02-24 23:28
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

. ./constants.sh

# python -m youngbench.dataset.construct.get_hf_models --model-ids-filepath ${HF_PATH}/70K-1-Neat.json --cache-dirpath ${HF_CACHE_PATH} --cache-flag-path ${HF_CACHE_FLAG_PATH}
# python -m youngbench.dataset.construct.get_hf_models --model-ids-filepath ${HF_PATH}/70K-2-Neat.json --cache-dirpath ${HF_CACHE_PATH} --cache-flag-path ${HF_CACHE_FLAG_PATH}
python -m youngbench.dataset.construct.get_hf_models --model-ids-filepath ${HF_PATH}/70K-3-Neat.json --cache-dirpath ${HF_CACHE_PATH} --cache-flag-path ${HF_CACHE_FLAG_PATH}
# python -m youngbench.dataset.construct.get_hf_models --model-ids-filepath ${HF_PATH}/70K-4-Neat.json --cache-dirpath ${HF_CACHE_PATH} --cache-flag-path ${HF_CACHE_FLAG_PATH}
