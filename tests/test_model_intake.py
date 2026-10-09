"""Adversarial storage fixtures; no model quality claims."""

import json
from pathlib import Path
import tempfile
import unittest

from zenithsync.model_intake import MAX_HEADER_BYTES, inspect_safetensors


def tensor(dtype="U8", shape=None, offsets=None):
    return {"dtype": dtype, "shape": [2] if shape is None else shape,
            "data_offsets": [0, 2] if offsets is None else offsets}


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "fixture.safetensors"

    def write(self, header, body=b"ab"):
        raw = header if isinstance(header, bytes) else json.dumps(header).encode()
        self.path.write_bytes(len(raw).to_bytes(8, "little") + raw + body)

    def test_valid_scalar_empty_and_nonempty(self):
        self.write({"scalar": tensor(shape=[], offsets=[0, 1]),
                    "empty": tensor(shape=[0, 5], offsets=[1, 1]),
                    "vector": tensor(shape=[1], offsets=[1, 2]),
                    "__metadata__": {"source": "synthetic"}})
        result = inspect_safetensors(self.path)
        self.assertEqual(result["tensor_count"], 3)
        self.assertEqual(result["data_size_bytes"], 2)
        self.assertFalse(result["gpu_loader_checked"])

    def test_invalid_descriptors(self):
        cases = [tensor(dtype="W4"), tensor(dtype=[]), tensor(shape=[True]),
                 tensor(shape=[-1]), tensor(shape=[1.0]), tensor(shape=[2**64]),
                 tensor(shape=[1] * 65), tensor(shape=[3]),
                 tensor(offsets=[True, 2]), tensor(offsets=[0, 3]),
                 tensor(offsets=[2, 0]), tensor(offsets=[0]),
                 {**tensor(), "extra": 1}]
        for value in cases:
            with self.subTest(value=value):
                self.write({"x": value})
                with self.assertRaises(ValueError):
                    inspect_safetensors(self.path)

    def test_gaps_overlaps_and_trailing_bytes(self):
        cases = [{"x": tensor(shape=[1], offsets=[1, 2])},
                 {"x": tensor(), "y": tensor()},
                 {"x": tensor(shape=[1], offsets=[0, 1])},
                 {"x": tensor(), "empty": tensor(shape=[0], offsets=[1, 1])}]
        for header in cases:
            with self.subTest(header=header):
                self.write(header)
                with self.assertRaises(ValueError):
                    inspect_safetensors(self.path)

    def test_invalid_json_and_metadata(self):
        for raw in (b'{"x":{},"x":{}}', b'{"__metadata__":{"x":2}}',
                    b'{"x":NaN}', b' {}', b'[]', b'{"x":"\xff"}',
                    b'{"__metadata__":null}', b'{}garbage'):
            with self.subTest(raw=raw):
                self.write(raw)
                with self.assertRaises(ValueError):
                    inspect_safetensors(self.path)

    def test_bounded_header_and_truncation(self):
        for raw in (b"", b"1234567", (MAX_HEADER_BYTES + 1).to_bytes(8, "little"),
                    (100).to_bytes(8, "little") + b"{}"):
            self.path.write_bytes(raw)
            with self.assertRaises(ValueError):
                inspect_safetensors(self.path)

    def test_symlink_rejected(self):
        self.write({"x": tensor()})
        link = self.path.with_name("link")
        link.symlink_to(self.path)
        with self.assertRaises(ValueError):
            inspect_safetensors(link)

    def test_storage_widths_use_exact_arithmetic(self):
        # Independent enumeration of byte positions for a small matrix.
        for dtype, width in (("BF16", 2), ("I32", 4), ("I64", 8)):
            length = len([byte for row in range(3) for col in range(5)
                          for byte in range(width)])
            self.write({"x": tensor(dtype, [3, 5], [0, length])}, bytes(length))
            self.assertEqual(inspect_safetensors(self.path)["data_size_bytes"], length)


if __name__ == "__main__":
    unittest.main()
