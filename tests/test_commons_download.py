import io
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import requests

from younger.commons.download import download


def make_response(status, headers=None, body=b''):
    response = requests.Response()
    response.status_code = status
    response.headers.update(headers or {})
    response.raw = io.BytesIO(body)
    response.url = 'https://example.test/file.bin'
    return response


class DownloadTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = pathlib.Path(directory.name)
        self.filepath = self.directory / 'file.bin'
        self.request_headers = []

    def run_download(self, *responses, force=False):
        pending = iter(responses)

        def get(url, **kwargs):
            self.request_headers.append(dict(kwargs['headers']))
            return next(pending)

        with (
            patch('younger.commons.download.requests.Session') as session_type,
            patch('younger.commons.download.tqdm.tqdm'),
        ):
            session_type.return_value.__enter__.return_value.get.side_effect = get
            return download('https://example.test/file.bin', self.directory, force=force)

    def test_416_restart_truncates_old_file_when_remote_is_empty(self):
        self.filepath.write_bytes(b'old content')
        partial = make_response(416, {'Content-Range': 'bytes */0'})
        self.run_download(partial, make_response(200, {'Content-Length': '0'}))
        self.assertEqual(self.filepath.read_bytes(), b'')
        self.assertEqual(self.request_headers[0]['Range'], 'bytes=11-')
        self.assertNotIn('Range', self.request_headers[1])
        self.assertTrue(partial.raw.closed)

    def test_416_matching_size_preserves_completed_file(self):
        self.filepath.write_bytes(b'abc')
        self.run_download(make_response(416, {'Content-Range': 'bytes */3'}))
        self.assertEqual(self.filepath.read_bytes(), b'abc')
        self.assertEqual(len(self.request_headers), 1)

    def test_416_oversized_local_file_is_replaced(self):
        self.filepath.write_bytes(b'old content')
        self.run_download(
            make_response(416, {'Content-Range': 'bytes */3'}),
            make_response(200, {'Content-Length': '3'}, b'abc'),
        )
        self.assertEqual(self.filepath.read_bytes(), b'abc')

    def test_416_without_valid_content_range_checks_full_response_size(self):
        for headers in ({}, {'Content-Range': 'invalid'}):
            with self.subTest(headers=headers):
                self.filepath.write_bytes(b'abc')
                partial = make_response(416, headers, b'Illegal Range request\n')
                with patch('younger.commons.download.fsspec.open') as open_file:
                    self.run_download(partial, make_response(200, {'Content-Length': '3'}, b'abc'))
                    open_file.assert_not_called()
                self.assertEqual(self.filepath.read_bytes(), b'abc')
                self.assertNotIn('Range', self.request_headers[-1])
                self.assertTrue(partial.raw.closed)

    def test_416_without_content_range_replaces_oversized_local_file(self):
        self.filepath.write_bytes(b'old content')
        self.run_download(
            make_response(416, {'Content-Length': '22'}, b'Illegal Range request\n'),
            make_response(200, {'Content-Length': '3'}, b'abc'),
        )
        self.assertEqual(self.filepath.read_bytes(), b'abc')

    def test_416_without_content_range_and_unknown_size_downloads_full_file(self):
        self.filepath.write_bytes(b'ab')
        self.run_download(make_response(416), make_response(200, {}, b'abc'))
        self.assertEqual(self.filepath.read_bytes(), b'abc')

    def test_416_without_content_range_replaces_local_file_with_empty_file(self):
        self.filepath.write_bytes(b'old content')
        self.run_download(make_response(416), make_response(200, {'Content-Length': '0'}))
        self.assertEqual(self.filepath.read_bytes(), b'')

    def test_416_without_content_range_does_not_hide_full_request_errors(self):
        self.filepath.write_bytes(b'abc')
        with self.assertRaises(requests.HTTPError):
            self.run_download(make_response(416), make_response(404))
        self.assertEqual(self.filepath.read_bytes(), b'abc')

    def test_unknown_partial_total_restarts_with_full_download(self):
        self.filepath.write_bytes(b'ab')
        partial = make_response(206, {'Content-Range': 'bytes 2-3/*'}, b'cd')
        with patch.object(partial, 'iter_content') as iter_content:
            self.run_download(partial, make_response(200, {}, b'abcdef'))
            iter_content.assert_not_called()
        self.assertEqual(self.filepath.read_bytes(), b'abcdef')
        self.assertNotIn('Range', self.request_headers[1])
        self.assertTrue(partial.raw.closed)

    def test_unknown_partial_total_does_not_skip_replacement_of_same_size(self):
        self.filepath.write_bytes(b'ab')
        self.run_download(
            make_response(206, {'Content-Range': 'bytes 2-3/*'}, b'cd'),
            make_response(200, {'Content-Length': '2'}, b'xy'),
        )
        self.assertEqual(self.filepath.read_bytes(), b'xy')

    def test_repeated_unknown_partial_total_is_rejected_without_writing(self):
        self.filepath.write_bytes(b'ab')
        with self.assertRaisesRegex(ValueError, 'unknown total size'):
            self.run_download(
                make_response(206, {'Content-Range': 'bytes 2-3/*'}, b'cd'),
                make_response(206, {'Content-Range': 'bytes 0-3/*'}, b'abcd'),
            )
        self.assertEqual(self.filepath.read_bytes(), b'ab')
        self.assertEqual(len(self.request_headers), 2)

    def test_valid_range_is_appended(self):
        self.filepath.write_bytes(b'ab')
        self.run_download(make_response(206, {'Content-Range': 'bytes 2-4/5'}, b'cde'))
        self.assertEqual(self.filepath.read_bytes(), b'abcde')

    def test_short_range_body_is_rejected(self):
        self.filepath.write_bytes(b'ab')
        with self.assertRaisesRegex(requests.ConnectionError, 'Incomplete HTTP range'):
            self.run_download(make_response(206, {'Content-Range': 'bytes 2-4/5'}, b'cd'))

    def test_excess_range_body_is_rejected_before_appending(self):
        self.filepath.write_bytes(b'ab')
        with self.assertRaisesRegex(requests.ConnectionError, 'exceeds its Content-Range'):
            self.run_download(make_response(206, {'Content-Range': 'bytes 2-3/5'}, b'cde'))
        self.assertEqual(self.filepath.read_bytes(), b'ab')

    def test_valid_subrange_does_not_claim_whole_file_is_complete(self):
        self.filepath.write_bytes(b'ab')
        with self.assertRaisesRegex(requests.ConnectionError, 'Incomplete download'):
            self.run_download(make_response(206, {'Content-Range': 'bytes 2-3/5'}, b'cd'))

    def test_full_response_with_unknown_length_is_downloaded(self):
        self.run_download(make_response(200, {}, b'abc'))
        self.assertEqual(self.filepath.read_bytes(), b'abc')

    def test_force_overwrites_existing_file_without_range(self):
        self.filepath.write_bytes(b'old content')
        self.run_download(make_response(200, {'Content-Length': '3'}, b'abc'), force=True)
        self.assertEqual(self.filepath.read_bytes(), b'abc')
        self.assertNotIn('Range', self.request_headers[0])

    def test_ignored_range_overwrites_existing_file(self):
        self.filepath.write_bytes(b'ab')
        self.run_download(make_response(200, {'Content-Length': '5'}, b'abcde'))
        self.assertEqual(self.filepath.read_bytes(), b'abcde')


if __name__ == '__main__':
    unittest.main()
