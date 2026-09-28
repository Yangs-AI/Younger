import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

from younger.commons.cache import load_cache_metadata, save_cache_metadata
from younger.commons.download import retry_http
from younger.commons.hash import hash_json
from younger.commons.io import atomic_write_path, directory_lock, save_json


class StorageTests(unittest.TestCase):
    def test_atomic_output_preserves_target_and_cleans_up_on_failure(self):
        with tempfile.TemporaryDirectory() as root:
            target = pathlib.Path(root) / 'data'
            target.write_text('old')
            with self.assertRaises(ValueError):
                with atomic_write_path(target) as part:
                    part.write_text('partial')
                    raise ValueError('failed writer')
            self.assertEqual(target.read_text(), 'old')
            self.assertEqual(list(target.parent.iterdir()), [target])
            with atomic_write_path(target) as part:
                part.write_text('new')
                self.assertEqual(target.read_text(), 'old')
            self.assertEqual(target.read_text(), 'new')

    def test_atomic_json_and_fingerprint_compatibility(self):
        data = {'z': ['中文', 1], 'a': {'b': True}}
        serialized = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
        expected = hashlib.sha256(serialized).hexdigest()
        self.assertEqual(hash_json(data), expected)
        self.assertEqual(hash_json(data)[:20], expected[:20])
        self.assertEqual(hash_json(data), hash_json(dict(reversed(list(data.items())))))
        self.assertEqual(hash_json(data, hash_algorithm='sha512'), hashlib.sha512(serialized).hexdigest())
        self.assertEqual(hash_json(data, hash_algorithm='blake2b', digest_size=16),
                         hashlib.blake2b(serialized, digest_size=16).hexdigest())
        with self.assertRaises(TypeError):
            hash_json(object())
        with tempfile.TemporaryDirectory() as root:
            target = pathlib.Path(root) / 'nested' / 'data.json'
            save_json(data, target, indent=2, atomic=True)
            self.assertEqual(target.read_text(), json.dumps(data, indent=2))
            regular = target.with_name('regular.json')
            save_json(data, regular, indent=2)
            self.assertEqual(target.read_bytes(), regular.read_bytes())
            with self.assertRaises(TypeError):
                save_json(object(), target, atomic=True)
            self.assertEqual(json.loads(target.read_text(encoding='utf-8')), data)

    def test_cache_metadata_round_trip_and_caller_comparison(self):
        with tempfile.TemporaryDirectory() as root:
            target = pathlib.Path(root) / 'data.nc'
            expected = {'inputs': {'version': 1, 'options': ['中文', True, None]}, 'file': {'size': 0}, 'extra': {}}
            self.assertIsNone(load_cache_metadata(target))
            save_cache_metadata(expected, target)
            self.assertFalse(target.exists())
            self.assertEqual(load_cache_metadata(target), expected)
            self.assertNotEqual(load_cache_metadata(target), {'version': 2})
            target.write_bytes(b'cache content')
            self.assertEqual(load_cache_metadata(target), expected)
            other = target.with_suffix('.csv')
            save_cache_metadata({'inputs': {}, 'file': {'size': 0}, 'extra': {}}, other)
            self.assertEqual(load_cache_metadata(other), {'inputs': {}, 'file': {'size': 0}, 'extra': {}})
            self.assertEqual(load_cache_metadata(target), expected)
            with self.assertRaises(TypeError):
                save_cache_metadata({'unsupported': object()}, target)
            self.assertEqual(load_cache_metadata(target), expected)

    def test_cache_metadata_missing_or_malformed(self):
        with tempfile.TemporaryDirectory() as root:
            target = pathlib.Path(root) / 'data'
            metadata_path = target.with_name(target.name + '.metadata.json')
            for malformed in (b'{', b'[]', b'null', b'42', b'\xff'):
                metadata_path.write_bytes(malformed)
                self.assertIsNone(load_cache_metadata(target))
            with patch.object(pathlib.Path, 'read_text', side_effect=PermissionError):
                with self.assertRaises(PermissionError):
                    load_cache_metadata(target)

    def test_lock_contention_and_release_after_exception(self):
        script = (
            'import sys\n'
            'from younger.commons.io import directory_lock\n'
            'try:\n'
            '    with directory_lock(sys.argv[1]): pass\n'
            'except RuntimeError:\n'
            '    sys.exit(7)\n'
        )
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                with directory_lock(root):
                    result = subprocess.run([sys.executable, '-c', script, root], timeout=10, capture_output=True)
                    self.assertEqual(result.returncode, 7, result.stderr)
                    raise ValueError('interruption')
            result = subprocess.run([sys.executable, '-c', script, root], timeout=10, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((pathlib.Path(root) / '.lock').exists())

    def test_retry_scope_and_exhaustion(self):
        with patch('younger.commons.download.time.sleep') as sleep:
            operation = Mock(side_effect=[requests.Timeout(), requests.ConnectionError(), 'ok'])
            self.assertEqual(retry_http(operation), 'ok')
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])
            for status, calls in ((403, 1), (429, 3), (503, 3)):
                response = requests.Response()
                response.status_code = status
                operation = Mock(side_effect=requests.HTTPError(response=response))
                with self.assertRaises(requests.HTTPError):
                    retry_http(operation, attempts=3)
                self.assertEqual(operation.call_count, calls)
            operation = Mock(side_effect=ValueError('bad catalogue'))
            with self.assertRaises(ValueError):
                retry_http(operation)
            self.assertEqual(operation.call_count, 1)

    def test_lock_released_when_owner_is_killed(self):
        script = (
            'import sys, time\n'
            'from younger.commons.io import directory_lock\n'
            'with directory_lock(sys.argv[1]):\n'
            '    print("locked", flush=True)\n'
            '    time.sleep(30)\n'
        )
        with tempfile.TemporaryDirectory() as root:
            owner = subprocess.Popen([sys.executable, '-c', script, root], stdout=subprocess.PIPE, text=True)
            try:
                self.assertEqual(owner.stdout.readline().strip(), 'locked')
                with self.assertRaises(RuntimeError):
                    with directory_lock(root):
                        pass
                owner.kill()
                owner.wait(timeout=10)
                with directory_lock(root, wait=True):
                    pass
            finally:
                if owner.poll() is None:
                    owner.kill()
                    owner.wait(timeout=10)
                owner.stdout.close()


if __name__ == '__main__':
    unittest.main()
