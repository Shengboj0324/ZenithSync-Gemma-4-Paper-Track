"""Fault-injected object transport tests, separate from live R2 evidence."""

import io
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from zenithsync.artifacts import inventory, verify
from zenithsync.object_store import ArtifactStore, IntegrityError


class Missing(Exception):
    response = {"Error": {"Code": "NoSuchKey"}}


class MemoryClient:
    def __init__(self):
        self.objects = {}
        self.corrupt_upload = False
        self.uploads = 0

    def get_object(self, *, Bucket, Key):
        if Key not in self.objects:
            raise Missing()
        data = self.objects[Key]
        return {"ContentLength": len(data), "Body": io.BytesIO(data)}

    def upload_file(self, filename, bucket, key):
        self.uploads += 1
        data = Path(filename).read_bytes()
        self.objects[key] = b"X" * len(data) if self.corrupt_upload else data

    def put_object(self, *, Bucket, Key, Body, ContentType):
        self.objects[Key] = Body


class ObjectStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "a").write_bytes(b"synthetic fixture")
        (self.source / "empty").write_bytes(b"")
        self.manifest = inventory(self.source, kind="fixture", source="test", revision="1")
        self.client = MemoryClient()
        self.store = ArtifactStore(self.client, "test-bucket")

    def test_roundtrip_and_idempotent_retry(self):
        first = self.store.publish(self.source, self.manifest)
        second = self.store.publish(self.source, self.manifest)
        self.assertEqual(first["uploaded_files"], 2)
        self.assertEqual(second["reused_files"], 2)
        self.assertEqual(self.client.uploads, 2)
        dest = self.root / "restored"
        result = self.store.restore(self.manifest, dest, max_bytes=100)
        self.assertEqual(result["destination"], str(dest.resolve()))
        self.assertTrue(result["destination_verified"])
        verify(dest, self.manifest)

    def test_removed_promoted_destination_is_not_reported_as_verified(self):
        self.store.publish(self.source, self.manifest)
        dest = self.root / 'removed-after-promotion'
        original = Path.rename

        def remove_after_rename(source, target):
            result = original(source, target)
            shutil.rmtree(target)
            return result

        with patch.object(Path, 'rename', remove_after_rename):
            with self.assertRaises(ValueError):
                self.store.restore(self.manifest, dest, max_bytes=100)
        self.assertFalse(dest.exists())

    def test_relative_destination_does_not_follow_callback_cwd_change(self):
        self.store.publish(self.source, self.manifest)
        original = self.client.get_object
        alternate = self.root / 'other'
        alternate.mkdir()
        previous = Path.cwd()

        def change_cwd(**kwargs):
            os.chdir(alternate)
            return original(**kwargs)

        try:
            os.chdir(self.root)
            self.client.get_object = change_cwd
            result = self.store.restore(self.manifest, Path('restored'), max_bytes=100)
        finally:
            os.chdir(previous)
        verify(self.root / 'restored', self.manifest)
        self.assertFalse((alternate / 'restored').exists())
        self.assertEqual(result['destination'], str(self.root.resolve() / 'restored'))

    def test_corrupt_upload_cannot_commit_manifest(self):
        self.client.corrupt_upload = True
        with self.assertRaises(IntegrityError):
            self.store.publish(self.source, self.manifest)
        self.assertFalse(any("/manifests/" in k for k in self.client.objects))

    def test_corrupt_restore_cannot_expose_partial_bundle(self):
        self.store.publish(self.source, self.manifest)
        row = self.manifest["files"][0]
        self.client.objects[self.store.blob_key(row["sha256"])] = b"X" * row["size_bytes"]
        dest = self.root / "restored"
        with self.assertRaises(IntegrityError):
            self.store.restore(self.manifest, dest, max_bytes=100)
        self.assertFalse(dest.exists())
        self.assertEqual(list(self.root.glob(".restore-*")), [])

    def test_existing_output_and_budget_protected(self):
        with self.assertRaises(FileExistsError):
            self.store.restore(self.manifest, self.source, max_bytes=100)
        with self.assertRaises(ValueError):
            self.store.restore(self.manifest, self.root / "too-large", max_bytes=1)
        self.assertEqual(self.client.uploads, 0)

    def test_source_drift_is_rejected_before_upload(self):
        (self.source / "a").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.store.publish(self.source, self.manifest)
        self.assertEqual(self.client.objects, {})

    def test_credential_paths_rejected(self):
        (self.source / ".env").write_bytes(b"synthetic excluded file")
        manifest = inventory(self.source, kind="fixture", source="test", revision="1")
        with self.assertRaises(ValueError):
            self.store.publish(self.source, manifest)
        self.assertEqual(self.client.objects, {})

    def test_access_error_does_not_trigger_overwrite(self):
        def denied(**kwargs):
            raise PermissionError("synthetic denial")
        self.client.get_object = denied
        with self.assertRaises(PermissionError):
            self.store.publish(self.source, self.manifest)
        self.assertEqual(self.client.uploads, 0)

    def test_interrupted_publication_reuses_only_verified_completed_objects(self):
        original = self.client.upload_file

        def interrupted(filename, bucket, key):
            original(filename, bucket, key)
            raise ConnectionError('synthetic failure after remote object completion')

        self.client.upload_file = interrupted
        with self.assertRaises(ConnectionError):
            self.store.publish(self.source, self.manifest)
        self.assertEqual(len(self.client.objects), 1)
        self.assertFalse(any('/manifests/' in key for key in self.client.objects))
        self.client.upload_file = original
        # A fresh transport instance has no in-process knowledge of prior progress.
        retry = ArtifactStore(self.client, 'test-bucket')
        result = retry.publish(self.source, self.manifest)
        self.assertEqual(result['reused_files'], 1)
        self.assertEqual(result['uploaded_files'], 1)
        self.assertEqual(self.client.uploads, 2)
        retry.restore(self.manifest, self.root / 'recovered', max_bytes=100)
        verify(self.root / 'recovered', self.manifest)

    def test_lost_manifest_acknowledgement_is_idempotent(self):
        original = self.client.put_object
        calls = []

        def lost_ack(**kwargs):
            calls.append(kwargs['Key'])
            original(**kwargs)
            raise ConnectionError('synthetic lost acknowledgement after commit')

        self.client.put_object = lost_ack
        with self.assertRaises(ConnectionError):
            self.store.publish(self.source, self.manifest)
        self.assertEqual(len(calls), 1)
        retry = ArtifactStore(self.client, 'test-bucket')
        result = retry.publish(self.source, self.manifest)
        self.assertEqual(result['uploaded_files'], 0)
        self.assertEqual(result['reused_files'], 2)
        self.assertEqual(len(calls), 1)
        self.assertIn(result['manifest_key'], self.client.objects)


if __name__ == "__main__":
    unittest.main()
