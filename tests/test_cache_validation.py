import pathlib
import tempfile
import unittest
from unittest.mock import Mock, patch

from younger.commons.cache import (
    build_cache_metadata, load_cache_metadata, save_cache_metadata, is_cache_valid,
)


class CacheValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = pathlib.Path(self.directory.name) / 'data.bin'
        self.path.write_bytes(b'abc')
        self.inputs = {'request': {'variables': ['temperature']}, 'version': 1}
        self.metadata = build_cache_metadata(self.path, self.inputs, extra={'elapsed': 2})
        save_cache_metadata(self.metadata, self.path)

    def test_all_inputs_must_match_extra_is_ignored(self):
        self.assertTrue(is_cache_valid(self.path, self.inputs))
        for changed in ({'version': 1}, {**self.inputs, 'version': 2},
                        {**self.inputs, 'request': {'variables': ['wind']}}):
            self.assertFalse(is_cache_valid(self.path, changed))
        self.metadata['extra'] = {'elapsed': 10}
        save_cache_metadata(self.metadata, self.path)
        self.assertTrue(is_cache_valid(self.path, self.inputs))

    def test_content_corruption_and_missing_file(self):
        self.path.write_bytes(b'xyz')
        self.assertFalse(is_cache_valid(self.path, self.inputs))
        self.assertTrue(is_cache_valid(self.path, self.inputs, verify_hash=False))
        self.path.write_bytes(b'abcd')
        self.assertFalse(is_cache_valid(self.path, self.inputs, verify_hash=False))
        self.path.unlink()
        self.assertFalse(is_cache_valid(self.path, self.inputs))

    def test_hash_omission_requires_explicit_opt_out(self):
        metadata = build_cache_metadata(self.path, self.inputs, include_hash=False)
        save_cache_metadata(metadata, self.path)
        self.assertFalse(is_cache_valid(self.path, self.inputs))
        self.assertTrue(is_cache_valid(self.path, self.inputs, verify_hash=False))

    def test_content_validator_runs_after_generic_checks(self):
        validator = Mock(return_value=False)
        self.assertFalse(is_cache_valid(self.path, self.inputs, validator=validator))
        validator.assert_called_once_with(self.path)
        validator.reset_mock()
        self.assertFalse(is_cache_valid(self.path, {}, validator=validator))
        validator.assert_not_called()
        self.assertTrue(is_cache_valid(self.path, self.inputs, validator=lambda p: p.read_bytes() == b'abc'))
        with self.assertRaises(RuntimeError):
            is_cache_valid(self.path, self.inputs, validator=Mock(side_effect=RuntimeError))

    def test_invalid_metadata_and_non_file_cache(self):
        for metadata in ({}, {'inputs': self.inputs, 'file': None},
                         {'inputs': self.inputs, 'file': {'size': True}},
                         {'inputs': self.inputs, 'file': {'size': -1}}):
            save_cache_metadata(metadata, self.path)
            self.assertFalse(is_cache_valid(self.path, self.inputs))
        save_cache_metadata(self.metadata, self.path)
        self.path.unlink()
        self.path.mkdir()
        self.assertFalse(is_cache_valid(self.path, self.inputs))
        with self.assertRaises(ValueError):
            build_cache_metadata(self.path, self.inputs)

    def test_create_does_not_publish_metadata(self):
        other = self.path.with_name('other.bin')
        other.write_bytes(b'abc')
        self.assertEqual(build_cache_metadata(other, self.inputs)['file'], self.metadata['file'])
        self.assertIsNone(load_cache_metadata(other))

    def test_file_disappearing_during_hash_is_invalid(self):
        with patch('younger.commons.cache.hash_file', side_effect=FileNotFoundError):
            self.assertFalse(is_cache_valid(self.path, self.inputs))
        with patch('younger.commons.cache.hash_file', side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                is_cache_valid(self.path, self.inputs)

    def test_metadata_schema_and_quiet_misses(self):
        invalid = [None, {}, {**self.metadata, 'inputs': []},
                   {**self.metadata, 'extra': None},
                   {**self.metadata, 'file': {}},
                   {**self.metadata, 'file': {'size': True}},
                   {**self.metadata, 'file': {'size': -1}},
                   {**self.metadata, 'file': {'size': 3, 'sha256': 42}}]
        for metadata in invalid:
            save_cache_metadata(metadata, self.path)
            self.assertIsNone(load_cache_metadata(self.path))
        metadata_path = self.path.with_name(self.path.name + '.metadata.json')
        with patch('younger.commons.io.logger.error') as error:
            metadata_path.unlink()
            self.assertIsNone(load_cache_metadata(self.path))
            metadata_path.write_text('{')
            self.assertIsNone(load_cache_metadata(self.path))
            error.assert_not_called()

    def test_empty_extra_is_preserved(self):
        extra = {}
        self.assertIs(build_cache_metadata(self.path, self.inputs, extra=extra)['extra'], extra)


if __name__ == '__main__':
    unittest.main()
