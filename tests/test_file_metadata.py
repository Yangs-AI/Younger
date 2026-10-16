import pathlib
import tempfile
import unittest
from unittest.mock import Mock, patch

from younger.commons.metadata import (
    build_file_metadata, load_file_metadata, save_file_metadata, is_file_valid,
)


class FileValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = pathlib.Path(self.directory.name) / 'data.bin'
        self.path.write_bytes(b'abc')
        self.inputs = {'request': {'variables': ['temperature']}, 'version': 1}
        self.metadata = build_file_metadata(self.path, self.inputs, info={'elapsed': 2})
        save_file_metadata(self.metadata, self.path)

    def test_all_inputs_must_match_info_is_ignored(self):
        self.assertTrue(is_file_valid(self.path, self.inputs))
        for changed in ({'version': 1}, {**self.inputs, 'version': 2},
                        {**self.inputs, 'request': {'variables': ['wind']}}):
            self.assertFalse(is_file_valid(self.path, changed))
        self.metadata['info'] = {'elapsed': 10}
        save_file_metadata(self.metadata, self.path)
        self.assertTrue(is_file_valid(self.path, self.inputs))

    def test_content_corruption_and_missing_file(self):
        self.path.write_bytes(b'xyz')
        self.assertFalse(is_file_valid(self.path, self.inputs))
        self.path.write_bytes(b'abcd')
        self.assertFalse(is_file_valid(self.path, self.inputs))
        self.path.unlink()
        self.assertFalse(is_file_valid(self.path, self.inputs))

    def test_content_validator_runs_after_generic_checks(self):
        validator = Mock(return_value=False)
        self.assertFalse(is_file_valid(self.path, self.inputs, validator=validator))
        validator.assert_called_once_with(self.path)
        validator.reset_mock()
        self.assertFalse(is_file_valid(self.path, {}, validator=validator))
        validator.assert_not_called()
        self.assertTrue(is_file_valid(self.path, self.inputs, validator=lambda p: p.read_bytes() == b'abc'))
        with self.assertRaises(RuntimeError):
            is_file_valid(self.path, self.inputs, validator=Mock(side_effect=RuntimeError))

    def test_invalid_metadata_and_non_regular_file(self):
        for metadata in ({}, {'conf': self.inputs, 'file': None},
                         {'conf': self.inputs, 'file': {'size': True}},
                         {'conf': self.inputs, 'file': {'size': -1}}):
            save_file_metadata(metadata, self.path)
            self.assertFalse(is_file_valid(self.path, self.inputs))
        save_file_metadata(self.metadata, self.path)
        self.path.unlink()
        self.path.mkdir()
        self.assertFalse(is_file_valid(self.path, self.inputs))
        with self.assertRaises(ValueError):
            build_file_metadata(self.path, self.inputs, info={})

    def test_create_does_not_publish_metadata(self):
        other = self.path.with_name('other.bin')
        other.write_bytes(b'abc')
        self.assertEqual(build_file_metadata(other, self.inputs, info={})['file'], self.metadata['file'])
        self.assertIsNone(load_file_metadata(other))

    def test_file_disappearing_during_hash_is_invalid(self):
        with patch('younger.commons.metadata.hash_file', side_effect=FileNotFoundError):
            self.assertFalse(is_file_valid(self.path, self.inputs))
        with patch('younger.commons.metadata.hash_file', side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                is_file_valid(self.path, self.inputs)

    def test_metadata_schema_and_missing_or_malformed_json(self):
        invalid = [None, {}, {**self.metadata, 'conf': []},
                   {**self.metadata, 'file': {}},
                   {**self.metadata, 'file': {'size': True}},
                   {**self.metadata, 'file': {'size': -1}},
                   {**self.metadata, 'file': {'size': 3, 'hash': 42}}]
        for metadata in invalid:
            save_file_metadata(metadata, self.path)
            self.assertIsNone(load_file_metadata(self.path))
        metadata_path = self.path.with_name(self.path.name + '.metadata.json')
        metadata_path.unlink()
        self.assertIsNone(load_file_metadata(self.path))
        metadata_path.write_text('{')
        self.assertIsNone(load_file_metadata(self.path))

    def test_empty_info_is_preserved(self):
        info = {}
        self.assertIs(build_file_metadata(self.path, self.inputs, info=info)['info'], info)


if __name__ == '__main__':
    unittest.main()
