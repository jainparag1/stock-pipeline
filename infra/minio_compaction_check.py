#!/usr/bin/env python3
"""
MinIO compaction verification helper

Usage examples:
  python infra/minio_compaction_check.py summary \
    --endpoint http://localhost:9000 --access-key minioadmin --secret-key minioadmin \
    --bucket stock-data-local --prefix streaming-output

  python infra/minio_compaction_check.py snapshot --out before.json --bucket stock-data-local --prefix streaming-output ...

  python infra/minio_compaction_check.py diff --a before.json --b after.json

This script uses boto3 to list objects and collects counts and total sizes for parquet files.
It also supports saving snapshots (JSON) and diffing two snapshots to show file-count/size changes.
"""

import argparse
import json
import sys
import re
from datetime import datetime
from collections import defaultdict

try:
    import boto3
    from botocore.config import Config
except Exception as e:
    print("Error: boto3 and botocore are required. Install with: pip install boto3 botocore", file=sys.stderr)
    raise

PARQUET_RE = re.compile(r"\.parquet$", re.IGNORECASE)
PART_KV_RE = re.compile(r"([a-zA-Z0-9_]+)=([^/]+)")


def make_s3_client(endpoint, access_key, secret_key, region, use_ssl, url_style):
    config = Config(s3={'addressing_style': url_style}) if url_style else None
    return boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        use_ssl=use_ssl,
        config=config,
    )


def list_parquet_objects(s3, bucket, prefix):
    paginator = s3.get_paginator('list_objects_v2')
    page_iter = paginator.paginate(Bucket=bucket, Prefix=prefix)
    files = []
    for page in page_iter:
        for obj in page.get('Contents', []):
            key = obj['Key']
            if PARQUET_RE.search(key):
                files.append({'Key': key, 'Size': obj['Size'], 'LastModified': obj['LastModified'].isoformat()})
    return files


def summarize_files(files, prefix=None):
    total_files = len(files)
    total_bytes = sum(f['Size'] for f in files)

    # group by partition keys if present (year/month/day/hour)
    groups = defaultdict(lambda: {'count': 0, 'bytes': 0})
    for f in files:
        key = f['Key']
        # remove prefix if provided
        k = key[len(prefix):].lstrip('/') if prefix and key.startswith(prefix) else key
        parts = k.split('/')
        # look for first partition-like segment e.g., year=2025
        part_map = {}
        for seg in parts:
            m = PART_KV_RE.match(seg)
            if m:
                part_map[m.group(1)] = m.group(2)
        # build a group label (year/month/day) if present
        if 'year' in part_map:
            label = f"year={part_map.get('year')}"
        elif 'date' in part_map:
            label = f"date={part_map.get('date')}"
        else:
            label = 'ungrouped'
        groups[label]['count'] += 1
        groups[label]['bytes'] += f['Size']

    return {
        'total_files': total_files,
        'total_bytes': total_bytes,
        'groups': groups,
    }


def snapshot(args):
    s3 = make_s3_client(args.endpoint, args.access_key, args.secret_key, args.region, not args.no_ssl, args.url_style)
    files = list_parquet_objects(s3, args.bucket, args.prefix)
    out = {
        'created_at': datetime.utcnow().isoformat(),
        'bucket': args.bucket,
        'prefix': args.prefix,
        'files': files,
    }
    if args.out:
        with open(args.out, 'w') as f:
            json.dump(out, f, indent=2)
        print(f"Wrote snapshot to {args.out} ({len(files)} parquet files)")
    else:
        print(json.dumps(out, indent=2))
    return out


def do_summary(args):
    s3 = make_s3_client(args.endpoint, args.access_key, args.secret_key, args.region, not args.no_ssl, args.url_style)
    files = list_parquet_objects(s3, args.bucket, args.prefix)
    total_files = len(files)
    total_bytes = sum(f['Size'] for f in files)
    print(f"Found {total_files} parquet files under s3://{args.bucket}/{args.prefix} (total {total_bytes} bytes)")
    # simple group by year if possible
    groups = defaultdict(lambda: {'count': 0, 'bytes': 0})
    for f in files:
        key = f['Key']
        k = key[len(args.prefix):].lstrip('/') if args.prefix and key.startswith(args.prefix) else key
        m = re.search(r"year=(\d{4})", k)
        if m:
            label = f"year={m.group(1)}"
        else:
            label = 'ungrouped'
        groups[label]['count'] += 1
        groups[label]['bytes'] += f['Size']

    for label, vals in sorted(groups.items()):
        print(f"  {label}: {vals['count']} files, {vals['bytes']} bytes")

    if args.show_top:
        top_n = args.show_top
        files_sorted = sorted(files, key=lambda x: x['Size'], reverse=True)
        print(f"\nTop {top_n} largest parquet files:")
        for f in files_sorted[:top_n]:
            print(f"  {f['Key']} ({f['Size']} bytes)")

    return {'total_files': total_files, 'total_bytes': total_bytes, 'groups': groups}


def do_diff(args):
    with open(args.a) as fa, open(args.b) as fb:
        A = json.load(fa)
        B = json.load(fb)
    filesA = {f['Key']: f for f in A.get('files', [])}
    filesB = {f['Key']: f for f in B.get('files', [])}
    added = [k for k in filesB.keys() - filesA.keys()]
    removed = [k for k in filesA.keys() - filesB.keys()]
    size_changed = [k for k in filesA.keys() & filesB.keys() if filesA[k]['Size'] != filesB[k]['Size']]
    print(f"Snapshot A ({args.a}): {len(filesA)} files")
    print(f"Snapshot B ({args.b}): {len(filesB)} files")
    print(f"Added: {len(added)}, Removed: {len(removed)}, Size changed: {len(size_changed)}")
    if args.verbose:
        if added:
            print('\nAdded files:')
            for k in added:
                print('  +', k)
        if removed:
            print('\nRemoved files:')
            for k in removed:
                print('  -', k)
        if size_changed:
            print('\nSize-changed files:')
            for k in size_changed:
                print('  *', k, filesA[k]['Size'], '->', filesB[k]['Size'])
    return {'added': added, 'removed': removed, 'size_changed': size_changed}


def main(argv=None):
    p = argparse.ArgumentParser(description='MinIO compaction verification tools')
    sub = p.add_subparsers(dest='cmd')

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--endpoint', default='http://localhost:9000', help='MinIO endpoint URL (scheme optional)')
    common.add_argument('--access-key', default=None)
    common.add_argument('--secret-key', default=None)
    common.add_argument('--region', default='us-east-1')
    common.add_argument('--no-ssl', action='store_true', help='Use HTTP instead of HTTPS')
    common.add_argument('--url-style', default='path', help='s3 url style: path or virtual')

    s_sum = sub.add_parser('summary', parents=[common])
    s_sum.add_argument('--bucket', required=True)
    s_sum.add_argument('--prefix', default='')
    s_sum.add_argument('--show-top', type=int, default=5)

    s_snap = sub.add_parser('snapshot', parents=[common])
    s_snap.add_argument('--bucket', required=True)
    s_snap.add_argument('--prefix', default='')
    s_snap.add_argument('--out', default=None, help='Write snapshot to a file (JSON)')

    s_diff = sub.add_parser('diff')
    s_diff.add_argument('--a', required=True)
    s_diff.add_argument('--b', required=True)
    s_diff.add_argument('--verbose', action='store_true')

    args = p.parse_args(argv)

    if args.cmd is None:
        p.print_help()
        return 2

    # For commands that use S3, normalize endpoint and credentials; diff doesn't have these attrs
    if hasattr(args, 'endpoint'):
        # allow endpoint without scheme: if startswith http use as-is else prepend http based on no_ssl
        ep = args.endpoint
        if not ep.startswith('http'):
            ep = ('https://' if not getattr(args, 'no_ssl', False) else 'http://') + ep
        args.endpoint = ep

        # if access/secret not provided, leave as None (boto3 may use env or other providers)
        args.access_key = getattr(args, 'access_key', None)
        args.secret_key = getattr(args, 'secret_key', None)

    if args.cmd == 'summary':
        return 0 if do_summary(args) else 0
    if args.cmd == 'snapshot':
        snapshot(args)
        return 0
    if args.cmd == 'diff':
        do_diff(args)
        return 0


if __name__ == '__main__':
    sys.exit(main())
