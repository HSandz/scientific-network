#!/usr/bin/env python3
"""Portable image configuration digest from docker-save, across Docker stores.

Docker's containerd store can report a manifest digest as inspect.Id; the classic
store reports the config digest. The hashed config and its rootfs DiffIDs define
one immutable runnable image across both. The archive checksum binds delivery.
"""
import argparse
import hashlib
import json
import tarfile


def identity(path, sha):
    tag = 'scientific-network-api:sha-' + sha
    with tarfile.open(path, 'r:gz') as archive:
        manifest = json.load(archive.extractfile('manifest.json'))
        entries = [m for m in manifest if tag in (m.get('RepoTags') or [])]
        assert len(entries) == 1, 'Expected exact immutable image tag'
        config = archive.extractfile(entries[0]['Config']).read()
        data = json.loads(config)
        assert data['architecture'] == 'amd64' and data['os'] == 'linux'
        assert data['config']['Labels']['org.opencontainers.image.revision'] == sha
        return 'sha256:' + hashlib.sha256(config).hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive')
    parser.add_argument('--sha', required=True)
    args = parser.parse_args()
    print(identity(args.archive, args.sha))
