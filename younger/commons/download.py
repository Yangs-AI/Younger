#!/usr/bin/env python3
# -*- encoding=utf8 -*-

########################################################################
# Created time: 2024-10-19 22:12:17
# Author: Jason Young (杨郑鑫).
# E-Mail: AI.Jason.Young@outlook.com
# Last Modified by: Jason Young (杨郑鑫)
# Last Modified time: 2026-09-28 21:27:23
# Copyright (c) 2024 Yangs.AI
# 
# This source code is licensed under the Apache License 2.0 found in the
# LICENSE file in the root directory of this source tree.
########################################################################


import tqdm
import fsspec
import pathlib
import requests

from typing import Callable, TypeVar

from younger.commons.io import create_dir
from younger.commons.utils import retry

T = TypeVar("T")

def is_retryable_http_exception(exception: Exception) -> bool:
    """Return whether an HTTP-related exception should be retried."""
    if isinstance(exception, (requests.ConnectionError, requests.Timeout)):
        return True

    if not isinstance(exception, requests.HTTPError):
        return False

    if exception.response is None:
        return True

    status_code = exception.response.status_code
    return status_code in (408, 429) or 500 <= status_code < 600


def retry_http(operation: Callable[[], T], max_attempts: int = 4, max_delay: float = 30) -> T:
    """Execute an idempotent HTTP operation with retry."""
    return retry(operation=operation, should_retry=is_retryable_http_exception, max_attempts=max_attempts, max_delay=max_delay)


def download(url: str, dirpath: pathlib.Path, filename: str | None = None, force: bool = True, proxy: str | None = None):
    r"""Downloads the content of an URL to a specific directory path.

    Args:
        url (str): The URL.
        dirpath (pathlib.Path): The folder.
    """
    if filename is None:
        filename = url.rpartition('/')[2]
        filename = filename if filename[0] == '?' else filename.split('?')[0]

    filepath = dirpath.joinpath(filename)

    if proxy:
        print(f'URL Requests Through Proxy {proxy}')
        proxies = dict(
            http = f'http://{proxy}',
            https = f'https://{proxy}',
        )
    else:
        proxies = None

    print(f'Downloading {url}')

    create_dir(dirpath)

    block_size = 1024
    if filepath.is_file():
        resume_byte_pos = filepath.stat().st_size
    else:
        resume_byte_pos = 0

    response = requests.get(url, stream=True, allow_redirects=True, proxies=proxies)
    total_size = int(response.headers.get('Content-Length', '0'))

    headers = {'Content-Length': '0', 'Range': f'bytes={resume_byte_pos}-'}
    response = requests.get(url, stream=True, headers=headers, allow_redirects=True, proxies=proxies)
    if not force and (resume_byte_pos == total_size or total_size == 0):
        print(f'File is already downloaded: {filename}')
        return filepath

    if resume_byte_pos < total_size:
        with tqdm.tqdm(total=total_size, initial=resume_byte_pos, unit="iB", unit_scale=True, unit_divisor=1024, desc=filename) as progress_bar:
            with fsspec.open(filepath, "ab") as f:
                for data in response.iter_content(block_size):
                    f.write(data)
                    progress_bar.update(len(data))

    return filepath
