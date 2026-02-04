# Younger

This repository maintains all code related to using the Younger dataset and its related applications.

Go to the website "[Datasets - Yangs Cloud](https://datasets.yangs.cloud/)" for [Detailed Documentation](https://datasets.yangs.cloud/younger/) of Younger's Applications.

Due to ongoing updates to this branch, the code may not match the initial version presented in the paper. Therefore, if you need the version that corresponds to what is mentioned in the paper, please switch to the `paper` [branch](https://github.com/YangsCloud/Younger/tree/paper) for reference.

## Installation

### Option A: Install from PyPI (recommended for users)
Install the core package:

```bash
pip install younger
```

Install optional feature groups as needed (these pull sub-packages published to PyPI):

```bash
# Logic toolchains
pip install "younger[logics]"

# Deep-learning apps
pip install "younger[apps]"

# Bench tools (when ready)
pip install "younger[tools]"
```

### Option B: Install from source (recommended for developers)
This repo includes multiple sub-packages. Use editable installs for local development.

```bash
git clone --recursive git@github.com:Jason-Young-AI/Younger.git
cd Younger
git checkout dev
git submodule update --init --recursive

# kernel
pip install -e .

# apps: younger_apps_dl
pip install -e younger/apps/dl

# logics: younger_logics_core + younger_logics_ir
pip install -e younger/logics/core
pip install -e younger/logics/ir
```

## Publishing Strategy (for maintainers)
The repository is a monorepo that ships multiple Python packages:

- `younger` (kernel)
- `younger-logics-core`
- `younger-logics-ir`
- `younger-apps-dl`
- `younger-tools-bench` (planned)

Recommended release order:
1) Publish `younger-logics-core` and `younger-logics-ir` to PyPI.
2) Publish `younger-apps-dl` (depends on kernel + logics).
3) Publish `younger` (kernel) with extras that depend on the above.
Make sure each sub-package has a proper `pyproject.toml` with PEP 440 versions and compatible dependency ranges.

## Dependency Map
- `younger`: kernel
- `younger-logics-core` and `younger-logics-ir`: depend on `younger`
- `younger-apps-dl`: depends on `younger` + `younger-logics-core` + `younger-logics-ir`
- `younger-tools-bench`: tools (planned)

## Runtime Dependencies (Summary)
- `younger`: tqdm, click, fsspec, psutil, tomlkit
- `younger-logics-core`: tqdm, click, psutil, pandas, networkx
- `younger-logics-ir`: onnx, tqdm, click, networkx
- `younger-apps-dl`: torch, pandas, scikit-learn, networkx, torch-geometric, tabulate, younger-logics-core, younger-logics-ir
- `younger-tools-bench`: tqdm, click, psutil, pandas, networkx

## Development & Contributing
Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, branching, testing, and contribution workflow.

## Release
Maintainers can follow [RELEASE.md](RELEASE.md) for publishing order and release checklist.

## Datasets
Browse and download the datasets at [here](https://datasets.yangs.cloud/younger/dataset_series).
It may take some time to prepare the datasets for the first release. Please stay tuned.
In future releases, we will provide features to automatically download and preprocess the datasets.

## Citation
If you need to use our code or dataset, please cite the following paper:

1. Yang, Z., Gao, W., Peng, L., Huang, Y., Tang, F., & Zhan, J. (2024). Younger: The First Dataset for Artificial Intelligence-Generated Neural Network Architecture. [arXiv](https://arxiv.org/abs/2406.15132)
```bibtex
@misc{yang2024youngerdatasetartificialintelligencegenerated,
      title={Younger: The First Dataset for Artificial Intelligence-Generated Neural Network Architecture}, 
      author={Zhengxin Yang and Wanling Gao and Luzhou Peng and Yunyou Huang and Fei Tang and Jianfeng Zhan},
      year={2024},
      eprint={2406.15132},
      archivePrefix={arXiv},
      primaryClass={cs.LG},
      url={https://arxiv.org/abs/2406.15132}, 
}
```
