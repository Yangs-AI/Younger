# Younger

This repository maintains all code related to using the Younger dataset and its related applications.

Go to the website "[Datasets - Yangs AI](https://datasets.yangs.ai/)" for [Detailed Documentation](https://datasets.yangs.ai/younger/) of Younger's Applications.

Due to ongoing updates to this branch, the code may not match the initial version presented in the paper. Therefore, if you need the version that corresponds to what is mentioned in the paper, please switch to the `paper` [branch](https://github.com/Yangs-AI/Younger/tree/paper) for reference.

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
```

Core and Bench publication is deferred. Extras for those packages will be added
after their releases; `younger[logics]` currently installs IR only.

### Option B: Install from source (recommended for developers)
This repo includes multiple sub-packages. Use editable installs for local development.

```bash
git clone --recursive git@github.com:Yangs-AI/Younger.git
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

Younger is maintained in independent repositories connected by Git submodules.
Each package owns its version and publishes independently to GitHub and PyPI:

- `younger` (kernel)
- `younger-logics-core` (publication deferred)
- `younger-logics-ir`
- `younger-apps-dl`
- `younger-tools-bench` (planned)

The current release scope is `younger`, `younger-logics-ir`, and `younger-apps-dl`
at `0.1.0`; subsequent versions do not need to match. Internal dependency ranges
declare compatibility. When new dependency
versions are needed, publish the kernel first, then logics, then apps/tools.
Kernel extras install compatible components. `releases/current.txt` records the
candidate combination checked by CI; named files in `releases/` preserve specific
combinations. See [RELEASE.md](RELEASE.md) for CI validation,
Trusted Publishing setup, release tags, and the coordinated release procedure.
Conda distribution is deferred.

## Dependency Map

- `younger`: kernel, with optional extras for components
- `younger-logics-core` and `younger-logics-ir`: depend on `younger`
- `younger-apps-dl` and `younger-tools-bench`: depend on `younger` and `younger-logics-ir`
- `younger-apps-dl` will also depend on `younger-logics-core` when that integration
  is implemented and a compatible Core release is available.

## Runtime Dependencies (Summary)
- `younger`: tqdm, click, fsspec, psutil, tomlkit, requests, python-semantic-release
- `younger-logics-core`: tqdm, click, psutil, pandas, networkx
- `younger-logics-ir`: onnx, tqdm, click, networkx
- `younger-apps-dl`: torch, pandas, scikit-learn, networkx, torch-geometric, tabulate, pydantic, younger-logics-ir
- `younger-tools-bench`: tqdm, click, psutil, pandas, networkx, younger-logics-ir

## Development & Contributing
Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, branching, testing, and contribution workflow.

## Release
Maintainers can follow [RELEASE.md](RELEASE.md) for publishing order and release checklist.

## Datasets
Browse and download the datasets at [here](https://datasets.yangs.ai/younger/dataset_series).
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
