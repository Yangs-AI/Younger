#!/usr/bin/env python3
# -*- encoding=utf8 -*-

########################################################################
# Created time: 2024-10-19 22:12:17
# Author: Jason Young (杨郑鑫).
# E-Mail: AI.Jason.Young@outlook.com
# Last Modified by: Jason Young (杨郑鑫)
# Last Modified time: 2026-10-23 17:15:13
# Copyright (c) 2024 Yangs.AI
# 
# This source code is licensed under the Apache License 2.0 found in the
# LICENSE file in the root directory of this source tree.
########################################################################


import re
import tqdm
import fsspec
import pathlib
import requests

from typing import Callable, TypeVar
from urllib.parse import urlsplit

from younger.commons.io import create_dir
from younger.commons.utils import retry

T = TypeVar('T')

def is_retryable_http_exception(exception: Exception) -> bool:
    """Return whether an HTTP-related exception should be retried."""
    if isinstance(exception, (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError)):
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


def download(url: str, dirpath: pathlib.Path, filename: str | None = None, force: bool = True, proxy: str | None = None) -> pathlib.Path:
    """Download a file, overwriting when forced or attempting to resume.

    Missing Content-Length means unknown size, not an empty file.
    Local files matching the remote size are treated as complete.
    Callers may additionally verify a checksum.
    """
    dirpath = pathlib.Path(dirpath)

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
    resume_byte_pos = filepath.stat().st_size if not force and filepath.is_file() else 0

    create_dir(dirpath)

    # Request uncompressed data so byte offsets match local file offsets.
    if resume_byte_pos:
        headers = {'Accept-Encoding': 'identity', 'Range': f'bytes={resume_byte_pos}-'}
    else:
        headers = {'Accept-Encoding': 'identity'}

    with requests.Session() as session:
        response = session.get(url, headers=headers, stream=True, allow_redirects=True, proxies=proxies, timeout=(10, 60))

        try:
            can_skip_existing = not force
            expected_response_size = None
            while True:
                if response.status_code == 416 and resume_byte_pos:
                    # A completed file commonly produces "bytes */<total>".
                    match = re.fullmatch(r'bytes \*/(\d+)', response.headers.get('Content-Range', '').strip())
                    if match is not None:
                        remote_size = int(match.group(1))
                        if resume_byte_pos == remote_size:
                            print(f'File is already downloaded: {filename}')
                            return filepath
                        can_skip_existing = False
                    # Some servers omit Content-Range on 416. Obtain a full
                    # response to check its size before replacing the file.
                else:
                    response.raise_for_status()

                    encoding = response.headers.get('Content-Encoding', 'identity').strip().lower()

                    if response.status_code != 206:
                        break

                    # Compressed partial responses cannot safely be appended
                    # because iter_content() automatically decodes their data.
                    if encoding not in ('', 'identity'):
                        raise ValueError('Cannot safely resume a compressed HTTP response.')

                    match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+|\*)', response.headers.get('Content-Range', '').strip())
                    if match is None:
                        raise ValueError('Missing or invalid Content-Range in HTTP 206 response.')

                    start = int(match.group(1))
                    end = int(match.group(2))
                    total_size = (
                        None if match.group(3) == '*'
                        else int(match.group(3))
                    )

                    if (
                        start != resume_byte_pos
                        or end < start
                        or (total_size is not None and end >= total_size)
                    ):
                        raise ValueError('Content-Range does not match the requested download range.')

                    if total_size is not None:
                        expected_response_size = end - start + 1
                        break

                    # A partial response with unknown total size cannot prove
                    # completion. Retry once without Range, before writing.
                    if 'Range' not in headers:
                        raise ValueError('Cannot confirm completion of an HTTP 206 response with unknown total size.')
                    can_skip_existing = False

                # An unusable offset or unknown total requires a full download.
                response.close()
                resume_byte_pos = 0
                headers.pop('Range', None)
                response = session.get(url, headers=headers, stream=True, allow_redirects=True, proxies=proxies, timeout=(10, 60))

            if response.status_code == 206:
                mode = 'ab' if resume_byte_pos else 'wb'
            else:
                # If Range was ignored, the response contains the whole file.
                # Compressed Content-Length counts encoded bytes, while
                # iter_content() yields decoded bytes.
                length = response.headers.get('Content-Length')
                total_size = (
                    int(length)
                    if length is not None and encoding in ('', 'identity')
                    else None
                )

                if (
                    can_skip_existing
                    and filepath.is_file()
                    and total_size is not None
                    and filepath.stat().st_size == total_size
                ):
                    print(f'File is already downloaded: {filename}')
                    return filepath

                resume_byte_pos = 0
                mode = 'wb'

            written_size = resume_byte_pos

            with tqdm.tqdm(
                total=total_size,
                initial=resume_byte_pos,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
                desc=filename,
            ) as progress_bar:
                with fsspec.open(filepath, mode) as file:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            if (
                                expected_response_size is not None
                                and written_size - resume_byte_pos + len(chunk) > expected_response_size
                            ):
                                raise requests.ConnectionError(
                                    f'HTTP response for {filename} exceeds its Content-Range.'
                                )
                            file.write(chunk)
                            written_size += len(chunk)
                            progress_bar.update(len(chunk))

            if expected_response_size is not None and written_size - resume_byte_pos != expected_response_size:
                raise requests.ConnectionError(
                    f'Incomplete HTTP range for {filename}: '
                    f'expected {expected_response_size} bytes, got {written_size - resume_byte_pos}.'
                )

            if total_size is not None and written_size != total_size:
                raise requests.ConnectionError(
                    f'Incomplete download of {filename}: '
                    f'expected {total_size} bytes, got {written_size}.'
                )

        finally:
            response.close()

    return filepath
