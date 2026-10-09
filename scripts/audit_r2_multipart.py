"""Read-only audit of incomplete multipart uploads in our artifact namespace.

Age or a matching object hash does not prove an upload is abandoned. This tool
never aborts uploads or changes bucket lifecycle settings.
"""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zenithsync.artifacts import canonical_json, file_record, load_json, validate_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    identities = {str(p): file_record(p) for p in args.manifest}
    known = set()
    prefix = 'artifacts/v1/blobs/sha256/'
    for path in args.manifest:
        known.update(prefix + row['sha256'] for row in validate_manifest(load_json(path))['files'])
    from dotenv import dotenv_values
    import boto3
    from botocore.config import Config
    credentials = {**dotenv_values(args.env_file), **os.environ}
    required = ['R2_ENDPOINT_URL', 'R2_BUCKET_NAME', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY']
    if any(not credentials.get(name) for name in required):
        raise ValueError('required R2 credentials missing')
    client = boto3.client('s3', endpoint_url=credentials['R2_ENDPOINT_URL'], region_name='auto',
        aws_access_key_id=credentials['R2_ACCESS_KEY_ID'],
        aws_secret_access_key=credentials['R2_SECRET_ACCESS_KEY'],
        config=Config(connect_timeout=15, read_timeout=60,
                      retries={'mode': 'standard', 'total_max_attempts': 3}))
    records = []
    for page in client.get_paginator('list_multipart_uploads').paginate(
            Bucket=credentials['R2_BUCKET_NAME'], Prefix=prefix,
            PaginationConfig={'PageSize': 100}):
        for upload in page.get('Uploads', []):
            if len(records) >= 100:
                raise ValueError('audit upload count exceeds safety bound')
            key = upload['Key']
            if not key.startswith(prefix):
                raise ValueError('listing returned an object outside the requested prefix')
            parts, size = 0, 0
            try:
                for chunk in client.get_paginator('list_parts').paginate(
                        Bucket=credentials['R2_BUCKET_NAME'], Key=key,
                        UploadId=upload['UploadId'], PaginationConfig={'PageSize': 1000}):
                    for part in chunk.get('Parts', []):
                        parts += 1
                        size += part['Size']
                        if parts > 10000:
                            raise ValueError('multipart part count exceeds supported bound')
                state = 'incomplete_at_observation'
            except client.exceptions.ClientError as error:
                if error.response.get('Error', {}).get('Code') != 'NoSuchUpload':
                    raise
                state = 'disappeared_during_audit_completion_or_abort_unknown'
            records.append({'key': key, 'upload_id': upload['UploadId'],
                'initiated_utc': upload['Initiated'].isoformat(),
                'matches_supplied_manifest': key in known, 'observed_parts': parts,
                'observed_bytes': size, 'state': state,
                'abandoned': 'not_determined', 'cleanup_performed': False})
    if identities != {str(p): file_record(p) for p in args.manifest}:
        raise ValueError('manifest changed during audit')
    receipt = {'schema_version': 1, 'status': 'multipart_read_only_audit_completed',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'prefix': prefix,
        'manifests': identities, 'auditor': file_record(Path(__file__)),
        'boto3_version': boto3.__version__, 'uploads': records,
        'limitations': ['Listing and parts are not an atomic snapshot',
                        'No inference of abandonment from age or matching key',
                        'No aborts or lifecycle mutations performed']}
    (args.output / 'receipt.json').write_bytes(canonical_json(receipt))
    print('Multipart audit recorded:', len(records), 'uploads; none aborted')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Multipart audit failed ({type(error).__name__}); no passing receipt.', file=sys.stderr)
        raise SystemExit(1)
