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
import subprocess


def read_identity(archive, sha):
    tag = 'scientific-network-api:sha-' + sha
    configs = {}
    manifest = None
    for member in archive:
        # Config/manifest JSON is tiny; never materialize layer tarballs.
        if not member.isfile() or member.size > 4 * 1024**2:
            continue
        payload = archive.extractfile(member).read()
        if member.name == 'manifest.json':
            manifest = json.loads(payload)
        else:
            try:
                data = json.loads(payload)
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(data, dict) and all(k in data for k in ('architecture', 'os', 'rootfs', 'config')):
                configs[member.name] = (payload, data)
    entries = [m for m in manifest or [] if tag in (m.get('RepoTags') or [])]
    assert len(entries) == 1, 'Expected exact immutable image tag'
    config, data = configs[entries[0]['Config']]
    assert data['architecture'] == 'amd64' and data['os'] == 'linux'
    assert data['config']['Labels']['org.opencontainers.image.revision'] == sha
    return 'sha256:' + hashlib.sha256(config).hexdigest()


def identity(path, sha):
    with tarfile.open(path, 'r|gz') as archive:
        return read_identity(archive, sha)


def docker_identity(image, sha):
    with subprocess.Popen(['docker', 'save', image], stdout=subprocess.PIPE) as proc:
        with tarfile.open(fileobj=proc.stdout, mode='r|') as archive:
            result = read_identity(archive, sha)
        assert proc.wait() == 0
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', nargs='?')
    parser.add_argument('--docker-image')
    parser.add_argument('--sha', required=True)
    args = parser.parse_args()
    assert bool(args.archive) != bool(args.docker_image)
    print(docker_identity(args.docker_image, args.sha) if args.docker_image else identity(args.archive, args.sha))
